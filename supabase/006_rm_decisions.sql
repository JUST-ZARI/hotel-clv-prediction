-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 006: capture Revenue Manager decisions as feedback for future retraining
--
-- Run after 005_messaging.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
--
--   RM_DECISIONS      overrides of a recommended action and priority flags,
--                     with the reason (append-only: the newest row per guest wins)
--   SETTINGS_HISTORY  every change to a shared setting (e.g. the at-risk threshold),
--                     written automatically by a trigger
-- =========================================================


-- =========================================================
-- 1. RM_DECISIONS
-- =========================================================

create table if not exists public.rm_decisions (
    decision_id     uuid primary key default gen_random_uuid(),

    guest_id        text not null
        references public.guests(guest_id)
        on delete cascade,

    prediction_id   uuid
        references public.clv_predictions(prediction_id)
        on delete set null,

    user_id         uuid not null
        references public.users(id)
        on delete cascade,

    decision_type   text not null
        check (decision_type in ('Override action', 'Clear override', 'Flag priority', 'Remove priority')),

    original_action text,          -- the model's recommended action at the time
    new_action      text,          -- the action chosen by the Revenue Manager (Override action only)

    reason          text not null check (char_length(trim(reason)) between 5 and 500),

    decided_at      timestamptz not null default now(),

    constraint override_needs_action check (
        decision_type <> 'Override action' or new_action is not null
    )
);

create index if not exists rm_decisions_guest_idx on public.rm_decisions(guest_id, decided_at desc);
create index if not exists rm_decisions_decided_idx on public.rm_decisions(decided_at desc);

alter table public.rm_decisions enable row level security;

-- Every signed-in user can read decisions (Marketing must see the action to carry out).
drop policy if exists "authenticated_users_can_read_rm_decisions" on public.rm_decisions;
create policy "authenticated_users_can_read_rm_decisions"
    on public.rm_decisions
    for select
    to authenticated
    using (true);

-- Only the Revenue Manager can record a decision, and only as themselves.
drop policy if exists "revenue_manager_can_record_decisions" on public.rm_decisions;
create policy "revenue_manager_can_record_decisions"
    on public.rm_decisions
    for insert
    to authenticated
    with check (
        user_id = (select auth.uid())
        and exists (select 1 from public.users u
                     where u.id = (select auth.uid()) and u.role = 'revenue_manager')
    );

-- Decisions are never edited or deleted from the app (a new row replaces an old one).
grant select, insert on public.rm_decisions to authenticated;
revoke all          on public.rm_decisions from anon;
grant all           on public.rm_decisions to service_role;


-- =========================================================
-- 2. SETTINGS_HISTORY (filled by a trigger on APP_SETTINGS)
-- =========================================================

create table if not exists public.settings_history (
    history_id  uuid primary key default gen_random_uuid(),
    key         text not null,
    old_value   jsonb,
    new_value   jsonb not null,
    changed_by  uuid references public.users(id) on delete set null,
    changed_at  timestamptz not null default now()
);

create index if not exists settings_history_key_idx on public.settings_history(key, changed_at desc);

-- Runs with the owner's rights so users never need write access to the history.
create or replace function public.log_setting_change()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if new.value is distinct from old.value then
        insert into public.settings_history (key, old_value, new_value, changed_by, changed_at)
        values (new.key, old.value, new.value, new.updated_by, coalesce(new.updated_at, now()));
    end if;
    return new;
end;
$$;

drop trigger if exists app_settings_history on public.app_settings;
create trigger app_settings_history
    after update on public.app_settings
    for each row execute function public.log_setting_change();

alter table public.settings_history enable row level security;

drop policy if exists "authenticated_users_can_read_settings_history" on public.settings_history;
create policy "authenticated_users_can_read_settings_history"
    on public.settings_history
    for select
    to authenticated
    using (true);

grant select on public.settings_history to authenticated;
revoke all   on public.settings_history from anon;
grant all    on public.settings_history to service_role;
revoke execute on function public.log_setting_change() from public, anon, authenticated;
