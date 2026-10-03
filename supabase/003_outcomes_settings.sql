-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 003: action outcomes + shared app settings
--
-- Run after 002_app_tables.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
-- =========================================================


-- =========================================================
-- 1. ACTION_LOGS: did the guest come back?
-- =========================================================

alter table public.action_logs
    add column if not exists outcome text
        check (outcome in ('Waiting', 'Came back', 'Didn''t come back')),
    add column if not exists outcome_at timestamptz;

-- Completed actions start as 'Waiting' (the app sets this on insert; backfill old rows).
update public.action_logs
   set outcome = 'Waiting'
 where action_status = 'Completed' and outcome is null;

create index if not exists action_logs_outcome_idx  on public.action_logs(outcome);
create index if not exists action_logs_logged_at_idx on public.action_logs(logged_at desc);

-- Only the outcome columns can be updated, and only by the Marketing Team.
-- (Everything else on a log stays write-once.)
grant update (outcome, outcome_at) on public.action_logs to authenticated;

drop policy if exists "marketing_can_record_outcomes" on public.action_logs;
create policy "marketing_can_record_outcomes"
    on public.action_logs
    for update
    to authenticated
    using (
        exists (select 1 from public.users u
                 where u.id = (select auth.uid()) and u.role = 'marketing')
    )
    with check (
        exists (select 1 from public.users u
                 where u.id = (select auth.uid()) and u.role = 'marketing')
    );


-- =========================================================
-- 2. APP_SETTINGS: values shared by every user
-- =========================================================

create table if not exists public.app_settings (
    key        text primary key,
    value      jsonb not null,
    updated_by uuid references public.users(id) on delete set null,
    updated_at timestamptz not null default now(),

    -- The at-risk threshold may only take the values offered in the app.
    constraint at_risk_days_allowed check (
        key <> 'at_risk_days' or (value #>> '{}')::int in (30, 60, 90, 120)
    )
);

insert into public.app_settings (key, value)
values ('at_risk_days', '60'::jsonb)
on conflict (key) do nothing;

alter table public.app_settings enable row level security;

-- Every signed-in user can read settings.
drop policy if exists "authenticated_users_can_read_settings" on public.app_settings;
create policy "authenticated_users_can_read_settings"
    on public.app_settings
    for select
    to authenticated
    using (true);

-- Only the Revenue Manager can change them (no inserts/deletes from the app).
drop policy if exists "revenue_manager_can_update_settings" on public.app_settings;
create policy "revenue_manager_can_update_settings"
    on public.app_settings
    for update
    to authenticated
    using (
        exists (select 1 from public.users u
                 where u.id = (select auth.uid()) and u.role = 'revenue_manager')
    )
    with check (
        exists (select 1 from public.users u
                 where u.id = (select auth.uid()) and u.role = 'revenue_manager')
        and updated_by = (select auth.uid())
    );


-- =========================================================
-- 3. DATA API GRANTS (automatic table exposure is off)
-- =========================================================

grant select                                  on public.app_settings to authenticated;
grant update (value, updated_by, updated_at)  on public.app_settings to authenticated;
revoke all                                    on public.app_settings from anon;
grant all                                     on public.app_settings to service_role;
