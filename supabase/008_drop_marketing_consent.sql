-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 008: remove the unused marketing_consent column from GUESTS
--
-- Consent handling is not part of this prototype (the historical data has no
-- consent information and the app never read this column). Safe to re-run.
-- =========================================================

alter table public.guests drop column if exists marketing_consent;
