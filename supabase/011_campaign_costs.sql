-- =========================================================
-- HOTEL CLV DECISION SUPPORT SYSTEM
-- 011: campaign costs for the Campaign ROI page
--
-- Run after 010_control_group.sql in Supabase Dashboard → SQL Editor. Safe to re-run.
--
-- One shared setting in APP_SETTINGS holds what a campaign costs the hotel:
--   * the cost of sending one Email or one SMS (KSh)
--   * the cost of each offer when a guest takes it up by coming back (KSh)
-- The values below are starting assumptions; the Revenue Manager changes them on the
-- Campaign ROI page (the existing policy lets only the Revenue Manager update settings,
-- and the existing trigger records every change in SETTINGS_HISTORY).
-- =========================================================

insert into public.app_settings (key, value)
values ('campaign_costs', '{
    "Email": 5,
    "SMS": 1,
    "Win-back offer": 3000,
    "Suite upgrade": 5000,
    "Loyalty thank-you": 1500,
    "Seasonal news": 0
}'::jsonb)
on conflict (key) do nothing;

-- The costs must be a JSON object (the app checks each value is a number from 0 to 1,000,000).
alter table public.app_settings drop constraint if exists campaign_costs_is_object;
alter table public.app_settings
    add constraint campaign_costs_is_object
        check (key <> 'campaign_costs' or jsonb_typeof(value) = 'object');
