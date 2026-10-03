-- =====================================================================
-- Hotel CLV Decision Support System — application users
-- Run once in Supabase Dashboard → SQL Editor.
-- =====================================================================

-- One row per Supabase Auth user. `id` is the same UUID as auth.users.id,
-- so deleting the auth user removes the application profile too.
create table if not exists public.users (
    id          uuid primary key references auth.users (id) on delete cascade,
    email       text not null unique,
    full_name   text not null check (char_length(full_name) between 2 and 120),
    role        text not null check (role in ('revenue_manager', 'marketing')),
    created_at  timestamptz not null default now()
);

create index if not exists users_role_idx on public.users (role);

-- ---------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------
-- A signed-in user may read only their own row.
-- There are deliberately NO insert/update/delete policies: rows are written
-- by the Streamlit server with the service-role key (which bypasses RLS)
-- only after the invite token has been verified. This stops anyone holding
-- the public anon key from creating a profile or changing their own role.
alter table public.users enable row level security;

drop policy if exists "users_select_own" on public.users;
create policy "users_select_own"
    on public.users
    for select
    to authenticated
    using ((select auth.uid()) = id);

revoke insert, update, delete on public.users from anon, authenticated;
