-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- Remaining application tables: GUESTS, CLV_PREDICTIONS, ACTION_LOGS
--
-- Run after schema.sql (USERS) in Supabase Dashboard → SQL Editor.
-- Safe to re-run: tables/indexes use IF NOT EXISTS, policies are dropped first.
--
-- Automatic table exposure is OFF for this project, so each table needs both:
--   * GRANTs   — let a Postgres role reach the table through the Data API
--   * RLS      — decide which rows / operations that role may use
-- =========================================================


-- =========================================================
-- 1. GUESTS  — one row per guest, produced by the booking-data pipeline
-- =========================================================

create table if not exists public.guests (
    guest_id             text primary key,
    guest_email          text,
    avg_daily_rate       numeric,
    total_previous_stays integer check (total_previous_stays >= 0),   -- [changed] non-negative
    cancellation_rate    numeric,
    booking_channel      text,
    last_stay_date       date,

    -- [added] fields the dashboard already shows (Guest Lookup, Segments).
    -- All nullable so the ETL can fill them as the feature set is finalised.
    avg_length_of_stay   numeric,
    booking_lead_time    integer,
    is_repeat_guest      boolean,
    guest_type           text,
    first_stay_date      date,
    created_at           timestamptz not null default now()
);


-- =========================================================
-- 2. CLV_PREDICTIONS  — one row per guest per model run (GUESTS 1 → many)
-- =========================================================

create table if not exists public.clv_predictions (
    prediction_id  uuid primary key default gen_random_uuid(),

    guest_id       text not null
        references public.guests(guest_id)
        on delete cascade,

    predicted_clv  numeric not null check (predicted_clv >= 0),        -- [changed] non-negative

    clv_tier       text not null
        check (clv_tier in ('High', 'Medium', 'Low')),

    recommended_action        text,
    recommended_action_reason text,                                     -- [added] shown in Guest Lookup

    model_used     text,

    predicted_at   timestamptz not null default now()
);


-- =========================================================
-- 3. ACTION_LOGS  — actions taken by staff (GUESTS 1 → many, USERS 1 → many)
-- =========================================================

create table if not exists public.action_logs (
    log_id           uuid primary key default gen_random_uuid(),

    user_id          uuid not null
        references public.users(id)
        on delete cascade,

    guest_id         text not null
        references public.guests(guest_id)
        on delete cascade,

    prediction_id    uuid
        references public.clv_predictions(prediction_id)
        on delete set null,

    action_taken     text not null,

    action_status    text not null default 'Pending'                    -- [changed] constrained + default
        check (action_status in ('Pending', 'Completed', 'Failed')),

    delivery_channel text,

    logged_at        timestamptz not null default now()
);


-- =========================================================
-- 4. INDEXES
-- =========================================================

create index if not exists clv_predictions_guest_id_idx
    on public.clv_predictions(guest_id);

create index if not exists clv_predictions_tier_idx
    on public.clv_predictions(clv_tier);

create index if not exists clv_predictions_guest_date_idx
    on public.clv_predictions(guest_id, predicted_at desc);

create index if not exists action_logs_user_id_idx
    on public.action_logs(user_id);

create index if not exists action_logs_guest_id_idx
    on public.action_logs(guest_id);

create index if not exists action_logs_prediction_id_idx
    on public.action_logs(prediction_id);


-- =========================================================
-- 5. ROW LEVEL SECURITY
-- =========================================================

alter table public.guests          enable row level security;
alter table public.clv_predictions enable row level security;
alter table public.action_logs     enable row level security;


-- =========================================================
-- 6. GUESTS POLICIES — any signed-in staff member can read
-- =========================================================

drop policy if exists "authenticated_users_can_read_guests" on public.guests;
create policy "authenticated_users_can_read_guests"
    on public.guests
    for select
    to authenticated
    using (true);


-- =========================================================
-- 7. CLV_PREDICTIONS POLICIES — any signed-in staff member can read
-- =========================================================

drop policy if exists "authenticated_users_can_read_predictions" on public.clv_predictions;
create policy "authenticated_users_can_read_predictions"
    on public.clv_predictions
    for select
    to authenticated
    using (true);


-- =========================================================
-- 8. ACTION_LOGS POLICIES
-- =========================================================

-- Insert only as yourself.
drop policy if exists "authenticated_users_can_insert_actions" on public.action_logs;
create policy "authenticated_users_can_insert_actions"
    on public.action_logs
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);

-- [changed] Read the whole team's history, not just your own rows: Guest Lookup
-- shows every action taken on a guest (e.g. the Revenue Manager sees what the
-- Marketing Team did). Logs are never updated or deleted from the app.
drop policy if exists "users_can_read_own_action_logs" on public.action_logs;
drop policy if exists "authenticated_users_can_read_action_logs" on public.action_logs;
create policy "authenticated_users_can_read_action_logs"
    on public.action_logs
    for select
    to authenticated
    using (true);


-- =========================================================
-- 9. DATA API GRANTS
-- =========================================================

-- Signed-in users (RLS above still applies row by row)
grant select         on public.users           to authenticated;
grant select         on public.guests          to authenticated;
grant select         on public.clv_predictions to authenticated;
grant select, insert on public.action_logs     to authenticated;

-- [added] Nothing is readable without signing in.
revoke all on public.users, public.guests, public.clv_predictions, public.action_logs from anon;

-- Trusted server-side role (Streamlit server + prediction pipeline; bypasses RLS)
grant all on public.users           to service_role;
grant all on public.guests          to service_role;
grant all on public.clv_predictions to service_role;
grant all on public.action_logs     to service_role;
