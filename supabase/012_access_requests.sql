-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 012: access requests — "Request an invite" on the Create Account page
--
-- Run after 011_campaign_costs.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
--
-- Someone without an invite code asks for one (name, email, role). The app server writes
-- the request with the server key after checking it; visitors cannot read or write this
-- table. Only the System Administrator can read requests and approve or decline them.
-- A request never creates an account: approving it sends a normal single-use invite.
-- =========================================================

create table if not exists public.access_requests (
    request_id   uuid primary key default gen_random_uuid(),
    full_name    text not null check (char_length(trim(full_name)) between 2 and 100),
    email        text not null check (char_length(email) <= 254 and email = lower(trim(email))
                                      and email like '%_@_%._%'),
    role         text not null check (role in ('revenue_manager', 'marketing')),
    status       text not null default 'Pending' check (status in ('Pending', 'Approved', 'Declined')),
    requested_at timestamptz not null default now(),
    decided_by   uuid references public.users(id) on delete set null,
    decided_at   timestamptz,

    -- A decided request records when it was decided; a pending one does not.
    constraint access_request_decided check ((status = 'Pending') = (decided_at is null))
);

-- At most one pending request per email.
create unique index if not exists access_requests_one_pending
    on public.access_requests(email) where status = 'Pending';
create index if not exists access_requests_requested_idx on public.access_requests(requested_at desc);

alter table public.access_requests enable row level security;

-- Only the administrator can read requests…
drop policy if exists "admin_can_read_access_requests" on public.access_requests;
create policy "admin_can_read_access_requests"
    on public.access_requests for select to authenticated
    using ((select public.is_admin()));

-- …and decide them, as themselves (or put one back to Pending if creating the invite failed).
drop policy if exists "admin_can_decide_access_requests" on public.access_requests;
create policy "admin_can_decide_access_requests"
    on public.access_requests for update to authenticated
    using ((select public.is_admin()))
    with check ((select public.is_admin()) and (status = 'Pending' or decided_by = (select auth.uid())));

-- No insert policy: new requests are written only by the app server (service role).
grant select                                  on public.access_requests to authenticated;
grant update (status, decided_by, decided_at) on public.access_requests to authenticated;
revoke all                                    on public.access_requests from anon;
grant all                                     on public.access_requests to service_role;
