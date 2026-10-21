-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 005: record real email / SMS sends on action logs
--
-- Run after 004_predictions_dashboard.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
-- =========================================================

-- Who the message went to, masked (e.g. "l***@strathmore.edu", "+254*****678"),
-- and the provider's id for the message (Gmail Message-ID / Twilio SID).
-- The full address is never stored.
alter table public.action_logs
    add column if not exists recipient_masked    text,
    add column if not exists provider_message_id text;

-- The app counts each user's sends in the last 24 hours (daily send limit).
create index if not exists action_logs_user_logged_idx
    on public.action_logs(user_id, logged_at desc);

-- Inserts are already allowed for signed-in users as themselves (002); the new
-- columns are covered by that table-level grant. Logs stay write-once.
