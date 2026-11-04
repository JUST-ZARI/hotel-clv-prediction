-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 010: control group — measure whether actions bring guests back
--
-- Run after 009_clear_priority_on_return.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
--
-- Each time at-risk guests are sent to the Marketing Team, 10% of them are picked at
-- random and NOT contacted. They are recorded in ACTION_LOGS with the status 'Held out'
-- and the outcome 'Waiting'. The Marketing Team later records whether they came back,
-- exactly as for contacted guests, and the Action Board compares the two return rates.
--
-- Only the allowed statuses change: no new table, column or permission is needed.
-- =========================================================

-- Drop the old status check, whatever Postgres named it.
do $$
declare
    c text;
begin
    for c in
        select con.conname
          from pg_constraint con
         where con.conrelid = 'public.action_logs'::regclass
           and con.contype = 'c'
           and pg_get_constraintdef(con.oid) like '%action_status%'
    loop
        execute format('alter table public.action_logs drop constraint %I', c);
    end loop;
end;
$$;

alter table public.action_logs
    add constraint action_logs_action_status_check
        check (action_status in ('Pending', 'Completed', 'Failed', 'Held out'));

-- Held-out guests start with the outcome 'Waiting', like completed actions.
update public.action_logs
   set outcome = 'Waiting'
 where action_status = 'Held out' and outcome is null;

create index if not exists action_logs_status_idx on public.action_logs(action_status);
