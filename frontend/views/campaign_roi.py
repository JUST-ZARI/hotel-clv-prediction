"""Campaign ROI (Revenue Manager): what campaigns cost against the predicted value of the guests
who came back, which CLV tier gives the most value per shilling, and a budget planner."""

import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError

import charts
import components as ui
from auth import require_auth
from data import repository as repo
from style import alert

require_auth({"revenue_manager"})

ui.page_header("Campaign ROI", "")

PERIODS = {"Last 30 days": 30, "Last 60 days": 60, "Last 90 days": 90, "Last 12 months": 365}
COST_LABELS = {"Email": "Per email sent", "SMS": "Per SMS sent", "Win-back offer": "Win-back offer (per return)",
               "Suite upgrade": "Suite upgrade (per return)", "Loyalty thank-you": "Loyalty thank-you (per return)",
               "Seasonal news": "Seasonal news (per return)"}

costs, saved = repo.campaign_costs()

# ---------------------------------------------------------------------------
# Period + cost settings
# ---------------------------------------------------------------------------
with st.container(key="roi_bar", horizontal=True, vertical_alignment="center"):
    period = ui.filter_select("Period", list(PERIODS), "roi_period", index=2, width=230)
    st.space("stretch")
    with st.popover("Campaign costs", icon=":material/payments:", key="roi_costs"):
        st.html('<p class="roi-pop">What a campaign costs the hotel, in KSh. Messages are paid for every send; '
                'an offer costs the hotel only when the guest comes back to use it. Every change is recorded.</p>')
        with st.form("roi_cost_form", border=False):
            new = {k: st.number_input(COST_LABELS[k], min_value=0.0, max_value=float(repo.MAX_COST),
                                      value=float(costs[k]), step=1.0 if k in repo.MESSAGE_CHANNELS else 500.0,
                                      key=f"roi_cost_{k}") for k in repo.COST_DEFAULTS}
            if st.form_submit_button("Save costs", type="primary", width="stretch"):
                try:
                    repo.set_campaign_costs(new)
                except (ValueError, PermissionError) as e:
                    alert("warning", str(e))
                except APIError:
                    alert("error", "The costs could not be saved. Please try again.")
                else:
                    st.toast("Campaign costs saved for everyone.", icon=":material/check_circle:")
                    st.rerun()

if not saved:
    alert("info", "Using the starting cost assumptions. Run supabase/011_campaign_costs.sql in Supabase so the "
                  "Revenue Manager can save the hotel's own costs.")

days = PERIODS[period]
trends = repo.campaign_trends(days)

if trends.empty:
    with ui.card("roi_empty"):
        ui.note("No completed actions in this period yet. ROI appears once the Marketing Team sends actions and "
                "records whether guests came back.")
    st.stop()

# ---------------------------------------------------------------------------
# Return on investment
# ---------------------------------------------------------------------------
cmp = repo.control_comparison(days)
roi = repo.campaign_roi(trends, costs, cmp["uplift"], cmp["contacted"]["known"])


def _per_ksh(v) -> str:
    return f"KSh {v:,.0f}" if v is not None else "–"


with ui.card("roi"):
    ui.card_title("Return on Investment", f"Completed actions · {period.lower()}", fa="sack-dollar")
    ui.kpi_row([
        ui.Kpi("Campaign Cost", ui.ksh(roi["total_cost"]),
               f"Messages {ui.ksh(roi['message_cost'])} · offers {ui.ksh(roi['offer_cost'])}", "receipt", "brand"),
        ui.Kpi("Value of Guests Who Came Back", ui.ksh(roi["value"]),
               f"{roi['came_back']:,} of {roi['contacted']:,} contacted guests · predicted CLV", "rotate-left",
               "orange"),
        ui.Kpi("Value per KSh 1 Spent", _per_ksh(roi["value_per_ksh"]), "Predicted CLV returned per shilling",
               "scale-balanced", "green"),
        ui.Kpi("Extra Value Caused", ui.ksh(roi["extra_value"]) if roi["extra_value"] is not None else "–",
               f"≈ {roi['extra_returns']:.0f} extra returns compared with the control group"
               if roi["extra_returns"] is not None
               else f"Shown once the control group has {repo.CONTROL_MIN_RESULTS} results in each group",
               "flask", "navy"),
    ])

# ---------------------------------------------------------------------------
# Budget guidance by CLV tier
# ---------------------------------------------------------------------------
guidance = repo.budget_guidance(trends, costs)
ready = guidance[guidance["enough"]]

with ui.card("roi_tiers"):
    with st.container(horizontal=True, vertical_alignment="top"):
        ui.card_title("Where the Budget Works Best", "Predicted value returned per KSh 1, by CLV tier", fa="chart-bar")
        st.space("stretch")
        ui.export_menu("chart_roi_tiers", guidance.drop(columns="enough"), "value_per_ksh_by_tier")
    if not ready.empty:
        best = ready.iloc[0]
        st.html(f'<p class="roi-lead">Spend first on <b>{ui.esc(best["clv_tier"])}-tier</b> guests: each KSh 1 '
                f'returns about <b>{_per_ksh(best["value_per_ksh"])}</b> in predicted lifetime value '
                f'({best["return_rate"]:.0%} came back, average CLV {ui.ksh(best["avg_clv"])}).</p>')
        charts.show(charts.hbar_track(
            labels=ready["clv_tier"].tolist(), values=[round(v or 0) for v in ready["value_per_ksh"]],
            colors=[charts.TIER_COLORS.get(t, charts.INK_400) for t in ready["clv_tier"]],
            value_text=[_per_ksh(v) for v in ready["value_per_ksh"]], height=44 * len(ready) + 10),
            key="chart_roi_tiers", filename="value_per_ksh_by_tier")
    ui.data_table("roi_tiers", guidance.assign(guest_id=guidance["clv_tier"]), [
        ui.Col("CLV Tier", 1.0, lambda r: ui.tier_badge(r["clv_tier"])),
        ui.Col("Actions", 0.8, lambda r: f'{r["actions"]:,}'),
        ui.Col("Return Rate", 1.1, lambda r: f'{r["return_rate"]:.0%} ({r["known"]} results)'
               if pd.notna(r["return_rate"]) else "Waiting"),
        ui.Col("Avg. CLV", 1.1, lambda r: ui.ksh(r["avg_clv"])),
        ui.Col("Cost per Guest", 1.1, lambda r: ui.ksh(r["cost_per_contact"])),
        ui.Col("Value per KSh 1", 1.1, lambda r: _per_ksh(r["value_per_ksh"]) if r["enough"]
               else '<span style="color:var(--ink-400)">Too few results</span>'),
    ], empty="No tiers to compare.")

# ---------------------------------------------------------------------------
# Budget planner
# ---------------------------------------------------------------------------
with ui.card("roi_plan"):
    ui.card_title("Budget Planner", "How a campaign budget would best be spent, using the results above",
                  fa="calculator")
    budget = st.number_input("Campaign budget (KSh)", min_value=0, max_value=100_000_000, value=50_000, step=5_000,
                             key="roi_budget", width=260)
    plan = repo.budget_plan(guidance, budget, repo.available_by_tier())
    if ready.empty:
        pass     # the tier table above shows that no tier has enough results yet
    elif plan.empty:
        ui.note("This budget is too small to contact any guest. Increase it, or lower the costs.")
    else:
        spent, returns, value = plan["cost"].sum(), plan["expected_returns"].sum(), plan["expected_value"].sum()
        st.html(f'<p class="roi-lead">Contact <b>{plan["guests"].sum():,} guests</b> for <b>{ui.ksh(spent)}</b>: '
                f'about <b>{returns:.0f} expected to come back</b>, worth about <b>{ui.ksh(value)}</b> in predicted '
                f'lifetime value.</p>')
        if budget - spent >= ready["cost_per_contact"].min():
            ui.note(f"{ui.ksh(budget - spent)} is left over: every guest available in these tiers is already "
                    "included.")
        ui.data_table("roi_plan", plan.assign(guest_id=plan["clv_tier"]), [
            ui.Col("CLV Tier", 1.0, lambda r: ui.tier_badge(r["clv_tier"])),
            ui.Col("Guests to Contact", 1.2, lambda r: f'{r["guests"]:,}'),
            ui.Col("Cost", 1.1, lambda r: ui.ksh(r["cost"])),
            ui.Col("Expected Returns", 1.2, lambda r: f'{r["expected_returns"]:.0f}'),
            ui.Col("Expected Value", 1.3, lambda r: ui.ksh(r["expected_value"])),
        ])
        with st.container(horizontal=True, horizontal_alignment="right"):
            ui.download_csv("Download plan", plan, "campaign_budget_plan.csv", key="roi_plan_csv", primary=False)

ui.css("""
.roi-pop { margin: 0 0 8px; font-size: 0.85rem; color: var(--ink-500); }
.roi-lead { margin: 0 0 10px; font-size: 0.95rem; color: var(--ink-800); }
.st-key-roi_bar { gap: 10px !important; }
""")
