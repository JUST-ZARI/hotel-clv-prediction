-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 009: remove a guest's Priority flag automatically when they come back
--
-- Run after 008_drop_marketing_consent.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
--
-- When the Marketing Team records the outcome "Came back" on an action, the guest
-- no longer needs a priority follow-up. A trigger adds a 'Remove priority' row to
-- RM_DECISIONS (append-only, so the history shows when and why it was removed).
--
-- Marketing cannot write RM_DECISIONS directly (only the Revenue Manager can), so the
-- trigger runs with the owner's rights and does only this one insert.
-- =========================================================

create or replace function public.clear_priority_on_return()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    last_flag text;
begin
    if new.outcome = 'Came back' and old.outcome is distinct from 'Came back' then
        -- Is the guest currently flagged? (the newest flag / remove row wins)
        select d.decision_type into last_flag
          from public.rm_decisions d
         where d.guest_id = new.guest_id
           and d.decision_type in ('Flag priority', 'Remove priority')
         order by d.decided_at desc
         limit 1;

        if last_flag = 'Flag priority' then
            insert into public.rm_decisions (guest_id, prediction_id, user_id, decision_type, reason)
            values (new.guest_id, new.prediction_id, coalesce((select auth.uid()), new.user_id),
                    'Remove priority',
                    left('Priority removed automatically: the guest came back after "'
                         || coalesce(new.action_taken, 'the action') || '".', 500));
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists action_logs_clear_priority on public.action_logs;
create trigger action_logs_clear_priority
    after update of outcome on public.action_logs
    for each row execute function public.clear_priority_on_return();

-- Only the trigger calls this function.
revoke execute on function public.clear_priority_on_return() from public, anon, authenticated;
