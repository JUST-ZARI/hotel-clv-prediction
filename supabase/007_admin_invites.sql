-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 007: System Administrator, per-person invitations, deactivation, password reset
--
-- Run after 006_rm_decisions.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
-- Then create the first administrator invite:
--     frontend/.venv/Scripts/python.exe supabase/create_admin_invite.py you@example.com
--
--   * USERS gains the 'admin' role and an is_active flag (deactivated staff lose access).
--   * INVITES replaces the shared invite tokens: one code per person, single use,
--     expires after 7 days, stored only as a hash.
--   * PASSWORD_RESETS holds short-lived reset codes (server only).
--   * Least privilege: the administrator manages accounts but cannot read guest data.
--   * Policy checks are wrapped as (select fn()) so they run once per query, not once per row.
-- =========================================================


-- =========================================================
-- 1. USERS: admin role + active flag
-- =========================================================

alter table public.users drop constraint if exists users_role_check;
alter table public.users
    add constraint users_role_check check (role in ('revenue_manager', 'marketing', 'admin'));

alter table public.users
    add column if not exists is_active      boolean not null default true,
    add column if not exists deactivated_at timestamptz;


-- Role of the signed-in user if their account is active (null otherwise).
-- SECURITY DEFINER so policies can call it without recursive RLS on USERS.
create or replace function public.active_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
    select role from public.users where id = (select auth.uid()) and is_active
$$;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public
as $$ select coalesce(public.active_role() = 'admin', false) $$;

create or replace function public.is_staff() returns boolean
language sql stable security definer set search_path = public
as $$ select coalesce(public.active_role() in ('revenue_manager', 'marketing'), false) $$;

revoke execute on function public.active_role(), public.is_admin(), public.is_staff() from public, anon;
grant  execute on function public.active_role(), public.is_admin(), public.is_staff() to authenticated;

-- The administrator can list every account and change role / active status.
drop policy if exists "admin_can_read_users" on public.users;
create policy "admin_can_read_users"
    on public.users for select to authenticated
    using ((select public.is_admin()));

drop policy if exists "admin_can_update_users" on public.users;
create policy "admin_can_update_users"
    on public.users for update to authenticated
    using ((select public.is_admin()))
    with check ((select public.is_admin()));

grant update (role, is_active, deactivated_at) on public.users to authenticated;


-- =========================================================
-- 2. Least privilege: guest data is for active hotel staff only (not the admin)
-- =========================================================

drop policy if exists "authenticated_users_can_read_guests" on public.guests;
drop policy if exists "staff_can_read_guests" on public.guests;
create policy "staff_can_read_guests"
    on public.guests for select to authenticated using ((select public.is_staff()));

drop policy if exists "authenticated_users_can_read_predictions" on public.clv_predictions;
drop policy if exists "staff_can_read_predictions" on public.clv_predictions;
create policy "staff_can_read_predictions"
    on public.clv_predictions for select to authenticated using ((select public.is_staff()));

drop policy if exists "authenticated_users_can_read_action_logs" on public.action_logs;
drop policy if exists "staff_can_read_action_logs" on public.action_logs;
create policy "staff_can_read_action_logs"
    on public.action_logs for select to authenticated using ((select public.is_staff()));

drop policy if exists "authenticated_users_can_insert_actions" on public.action_logs;
create policy "authenticated_users_can_insert_actions"
    on public.action_logs for insert to authenticated
    with check ((select auth.uid()) = user_id and (select public.is_staff()));

drop policy if exists "authenticated_users_can_read_rm_decisions" on public.rm_decisions;
drop policy if exists "staff_can_read_rm_decisions" on public.rm_decisions;
create policy "staff_can_read_rm_decisions"
    on public.rm_decisions for select to authenticated using ((select public.is_staff()));


-- =========================================================
-- 3. INVITES: one code per person, single use, 7-day expiry
-- =========================================================

create table if not exists public.invites (
    invite_id   uuid primary key default gen_random_uuid(),
    email       text not null check (email = lower(email)),
    role        text not null check (role in ('revenue_manager', 'marketing', 'admin')),
    code_hash   text not null,                         -- SHA-256 of the code; the code itself is never stored
    invited_by  uuid references public.users(id) on delete set null,
    created_at  timestamptz not null default now(),
    expires_at  timestamptz not null default now() + interval '7 days',
    used_at     timestamptz,
    used_by     uuid references public.users(id) on delete set null,
    revoked_at  timestamptz
);

-- At most one open invite per email address.
create unique index if not exists invites_one_open_per_email
    on public.invites(email) where used_at is null and revoked_at is null;
create index if not exists invites_created_idx on public.invites(created_at desc);

alter table public.invites enable row level security;

drop policy if exists "admin_can_read_invites" on public.invites;
create policy "admin_can_read_invites"
    on public.invites for select to authenticated using ((select public.is_admin()));

drop policy if exists "admin_can_create_invites" on public.invites;
create policy "admin_can_create_invites"
    on public.invites for insert to authenticated
    with check ((select public.is_admin()) and invited_by = (select auth.uid()));

drop policy if exists "admin_can_revoke_invites" on public.invites;
create policy "admin_can_revoke_invites"
    on public.invites for update to authenticated
    using ((select public.is_admin())) with check ((select public.is_admin()));

grant select, insert          on public.invites to authenticated;
grant update (revoked_at)     on public.invites to authenticated;
revoke all                    on public.invites from anon;
grant all                     on public.invites to service_role;
-- Accepting an invite (used_at / used_by) is done by the server after it checks the code.


-- =========================================================
-- 4. PASSWORD_RESETS: 6-digit codes, 15-minute expiry (server only)
-- =========================================================

create table if not exists public.password_resets (
    reset_id    uuid primary key default gen_random_uuid(),
    user_id     uuid not null references public.users(id) on delete cascade,
    code_hash   text not null,
    created_at  timestamptz not null default now(),
    expires_at  timestamptz not null default now() + interval '15 minutes',
    used_at     timestamptz,
    attempts    integer not null default 0
);

create index if not exists password_resets_user_idx on public.password_resets(user_id, created_at desc);

alter table public.password_resets enable row level security;   -- no policies: only the server key can use it
revoke all on public.password_resets from anon, authenticated;
grant all  on public.password_resets to service_role;
