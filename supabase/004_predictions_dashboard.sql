-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 004: real model output for the dashboard
-- =========================================================


-- =========================================================
-- 1. GUESTS: details the dashboard shows that 002 did not have
-- =========================================================

alter table public.guests
    add column if not exists market_segment     text,
    add column if not exists hotel_type         text,
    add column if not exists room_type          text,      -- room type of the guest's booking (A–L)
    add column if not exists meal_plan          text,
    add column if not exists booking_canceled   boolean,   -- was that booking cancelled?
    add column if not exists first_booking_year integer,
    -- Contact permission. False for every guest in the historical data: the app
    -- must never message a guest who has not agreed to it.
    add column if not exists marketing_consent  boolean not null default false;


-- =========================================================
-- 2. MODEL_RUNS: one row per prediction run (notebook 08)
-- =========================================================
-- predicted_at is the run key: every CLV_PREDICTIONS row of a run carries the
-- same predicted_at. Thresholds are stored so the app explains tiers with the
-- numbers the model actually used.

create table if not exists public.model_runs (
    predicted_at      timestamptz primary key,
    model_used        text not null,
    as_of_date        date not null,      -- "today" of the historical data (latest check-out)
    high_min_clv      numeric not null,   -- predicted CLV ≥ this → High
    low_max_clv       numeric not null,   -- predicted CLV ≤ this → Low
    platinum_min_clv  numeric not null,   -- High and ≥ this → Platinum badge
    test_mae          numeric,
    test_rmse         numeric,
    test_r2           numeric,
    guests_predicted  integer,
    loaded_at         timestamptz not null default now()
);


-- =========================================================
-- 3. CLV_PREDICTIONS: badge, rank, drivers, Action Board flag
-- =========================================================

alter table public.clv_predictions
    add column if not exists tier_badge      text
        check (tier_badge in ('Platinum', 'High', 'Medium', 'Low')),
    add column if not exists clv_percentile  numeric check (clv_percentile between 0 and 1),
    add column if not exists top_drivers     jsonb,     -- [{"feature", "impact_pct", "direction"}] × 5
    add column if not exists in_action_queue boolean not null default false;

-- The app reads one run at a time, page by page in guest order.
create index if not exists clv_predictions_run_guest_idx
    on public.clv_predictions(predicted_at, guest_id);


-- =========================================================
-- 4. STAFF_DIRECTORY: names on action logs and settings
-- =========================================================
-- USERS rows stay private (own row only, see 001). This view exposes just the
-- name and role of each staff member so the app can show who logged an action.
-- It runs with the owner's rights on purpose; emails are not included.

create or replace view public.staff_directory
    with (security_invoker = false) as
    select id, full_name, role from public.users;


-- =========================================================
-- 5. ROW LEVEL SECURITY + DATA API GRANTS
-- =========================================================

alter table public.model_runs enable row level security;

drop policy if exists "authenticated_users_can_read_model_runs" on public.model_runs;
create policy "authenticated_users_can_read_model_runs"
    on public.model_runs
    for select
    to authenticated
    using (true);

grant select on public.model_runs      to authenticated;
grant select on public.staff_directory to authenticated;
revoke all   on public.model_runs, public.staff_directory from anon;
grant all    on public.model_runs      to service_role;
grant select on public.staff_directory to service_role;
