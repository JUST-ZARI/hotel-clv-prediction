import textwrap

import pandas as pd
import streamlit as st

import alerts
import charts
import components as ui
from auth import require_auth
from data import repository as repo

require_auth()
rm = ui.is_revenue_manager()

ui.page_header("Hotel Guest CLV Dashboard",
               "Overview of predicted customer lifetime value and recommended guest actions")

if not rm:
    alerts.action_board_banner(alerts.inbox())

# ---------------------------------------------------------------------------
# Impact of recent actions (from ACTION_LOGS outcomes)
# ---------------------------------------------------------------------------
impact = repo.outcome_summary(days=30)
items = [
    ("paper-plane", f"<b>{impact['contacted']:,}</b> guests contacted"),
    ("rotate-left", f"<b>{impact['came_back']:,}</b> came back ({impact['return_rate']:.0%})"),
    ("hourglass-half", f"<b>{impact['waiting']:,}</b> still waiting"),
]
if rm:
    items.append(("sack-dollar", f"<b>{ui.ksh(impact['value_retained'])}</b> predicted value retained"))
st.html('<div class="ds-impact"><span class="ds-impact-k"><i class="fa-regular fa-calendar"></i>Last 30 days</span>'
        + "".join(f'<span class="ds-impact-i"><i class="fa-solid fa-{ic}"></i>{txt}</span>' for ic, txt in items)
        + "</div>")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
o = repo.overview()
ui.kpi_row([
    ui.Kpi("Total Guests", f"{o['total_guests']:,}", "All tracked hotel guests", "users"),
    ui.Kpi("High-Value Guests", f"{o['high_value_guests']:,}",
           f"{o['high_value_guests'] / o['total_guests']:.0%} of total guest base", "star", "orange"),
    ui.Kpi("At-Risk High-Value", f"{o['at_risk_high_value']:,}",
           f"Inactive {repo.at_risk_days()}+ days", "triangle-exclamation", "red"),
    ui.Kpi("Avg. Predicted CLV", ui.ksh(o["avg_predicted_clv"]), "Across all guests", "chart-simple", "brand"),
])

queue = repo.action_queue()

# ---------------------------------------------------------------------------
# Top 10 chart — Revenue Manager only
# ---------------------------------------------------------------------------
if rm:
    top = queue.head(10)
    with ui.card("top10"):
        with st.container(horizontal=True, vertical_alignment="top"):
            ui.card_title("Top 10 Guests by Predicted CLV", "Highest predicted lifetime value first")
            st.space("stretch")
            ui.export_menu("chart_top10", top[["guest_id", "clv_tier", "predicted_clv"]],
                           "top10_guests_by_clv", label="Export PNG / CSV")
        charts.show(
            charts.hbar_track(
                labels=top["guest_id"].tolist(),
                values=top["predicted_clv"].tolist(),
                colors=charts.warm_scale(len(top)),
                value_text=[ui.ksh(v) for v in top["predicted_clv"]],
            ),
            key="chart_top10", filename="top10_guests_by_clv",
        )

# ---------------------------------------------------------------------------
# Guest action list
# ---------------------------------------------------------------------------
with ui.card("actions"):
    with st.container(horizontal=True, vertical_alignment="top"):
        ui.card_title("Guest Action List",
                      "Prioritised list of guests requiring immediate attention based on CLV predictions" if rm
                      else "Prioritised list of guests requiring campaign actions")
        st.space("stretch")
        ui.note("Priority guests first, then by predicted CLV")

    tier_opts = ["All Tiers"] + repo.TIERS
    action_opts = ["All Actions"] + sorted(queue["recommended_action"].unique())
    with st.container(key="bar_ab", horizontal=True, vertical_alignment="center"):
        tier = ui.filter_select("CLV Tier", tier_opts, "ab_tier")
        action = ui.filter_select("Recommended Action", action_opts, "ab_action", width=330)
        show = ui.filter_select("Show", ["All guests", "Priority only"], "ab_show", width=210)
        query = ui.search_box("ab_search")
        download_slot = st.container(width="content")

    # Guests the Revenue Manager sent as priority come first, then highest predicted CLV.
    has_priority = "is_priority" in queue.columns
    rows = queue.sort_values(["is_priority", "predicted_clv"], ascending=[False, False]) if has_priority else queue
    if show == "Priority only":
        rows = rows[rows["is_priority"]] if has_priority else rows.iloc[0:0]
    if tier != "All Tiers":
        rows = rows[rows["clv_tier"] == tier]
    if action != "All Actions":
        rows = rows[rows["recommended_action"] == action]
    if query.strip():
        rows = rows[rows["guest_id"].str.contains(query.strip(), case=False, regex=False)]

    export_cols = ["guest_id", "clv_tier", "predicted_clv", "recommended_action", "days_since_last_stay"]
    if not rm:
        export_cols.remove("predicted_clv")
    with download_slot:
        ui.download_csv("Download CSV", rows[export_cols], "guest_action_list.csv", key="ab_csv")

    ui.reset_page_on_change("ab", tier, action, show, query)
    start, end = ui.paginate("ab", len(rows))

    cols = [
        ui.Col("Guest ID", 1.1, kind="guest_link"),
        ui.Col("CLV Tier", 1.3, lambda r: ui.tier_badge(r["tier_badge"])
               + (" " + ui.pill("Priority", "navy") if r.get("is_priority") else "")),
    ]
    if rm:
        cols.append(ui.Col("Predicted CLV (KSh)", 1.6, lambda r: f'<span class="gt-num">{r["predicted_clv"]:,}</span>'))
    else:
        cols.append(ui.Col("Recommended Action", 2.0, lambda r: f'<span class="gt-tag gt-tag-action">{ui.esc(r["recommended_action"])}</span>'))
    cols += [
        ui.Col("Days Since Last Stay", 1.4, lambda r: f'{r["days_since_last_stay"]} days'),
        ui.Col("", 1.0, kind="view_button"),
    ]
    ui.data_table("ab", rows.iloc[start:end], cols)
    ui.pagination_bar("ab", len(rows))

alerts.scroll_to_list()


# ---------------------------------------------------------------------------
# Campaign insights — trends in ACTION_LOGS outcomes, so the next campaign
# is planned on what has worked before
# ---------------------------------------------------------------------------
PERIODS = {"Last 30 days": 30, "Last 60 days": 60, "Last 90 days": 90, "Last 12 months": 365}


def _rate_chart(rates, by: str, colors: list[str], key: str, filename: str) -> None:
    labels = ["<br>".join(textwrap.wrap(str(v), 18)) for v in rates[by]]
    values = [0 if pd.isna(r) else round(r * 100, 1) for r in rates["return_rate"]]
    text = [f"{r:.0%} ({c}/{d})" if d else f"{w} waiting"
            for r, c, d, w in zip(rates["return_rate"], rates["came_back"], rates["decided"], rates["waiting"])]
    charts.show(charts.hbar_track(labels=labels, values=values, colors=colors, value_text=text, max_value=100,
                                  height=44 * len(labels) + 10),
                key=key, filename=filename)


with ui.card("insights"):
    with st.container(horizontal=True, vertical_alignment="top"):
        ui.card_title("Campaign Insights",
                      "How guests responded to past actions, to guide the next campaign", fa="chart-line")
        st.space("stretch")
        period = ui.filter_select("Period", list(PERIODS), "ci_period", index=2, width=230)
    trends = repo.campaign_trends(PERIODS[period])

    if trends.empty:
        ui.note("No completed actions in this period yet. Charts appear once actions are sent and recorded.")
    else:
        decided = int((trends["outcome"] != "Waiting").sum())
        came = int((trends["outcome"] == "Came back").sum())
        waiting = len(trends) - decided
        ui.kpi_row([
            ui.Kpi("Actions Sent", f"{len(trends):,}", period, "paper-plane", "brand"),
            ui.Kpi("Return Rate", f"{came / decided:.0%}" if decided else "–",
                   f"{came} of {decided} with a known result", "rotate-left", "orange"),
            ui.Kpi("Still Waiting", f"{waiting:,}", "Outcome not recorded yet", "hourglass-half"),
        ])

        weekly = (trends.pivot_table(index="week", columns="outcome", values="guest_id", aggfunc="size",
                                     fill_value=0).sort_index())
        with st.container(horizontal=True, vertical_alignment="top"):
            ui.card_title("Outcomes per week", "Guests contacted each week and what happened next")
            st.space("stretch")
            ui.export_menu("chart_ci_weeks", weekly.reset_index(), "campaign_outcomes_per_week")
        charts.show(charts.outcome_weeks(weekly), key="chart_ci_weeks", filename="campaign_outcomes_per_week")

        by_action = repo.return_rates(trends, "action_taken")
        ui.card_title("Return rate by action", "Which actions bring guests back most often")
        _rate_chart(by_action, "action_taken", charts.warm_scale(len(by_action)),
                    "chart_ci_action", "return_rate_by_action")

        left, right = st.columns(2, gap="large")
        with left:
            by_tier = repo.return_rates(trends, "clv_tier")
            ui.card_title("By CLV tier", "Response of each guest tier")
            _rate_chart(by_tier, "clv_tier", [charts.TIER_COLORS.get(t, charts.INK_400) for t in by_tier["clv_tier"]],
                        "chart_ci_tier", "return_rate_by_tier")
        with right:
            by_channel = repo.return_rates(trends, "delivery_channel")
            ui.card_title("By channel", "Email compared with SMS")
            _rate_chart(by_channel, "delivery_channel",
                        [{"Email": charts.BRAND, "SMS": charts.SKY}.get(c, charts.INK_400)
                         for c in by_channel["delivery_channel"]],
                        "chart_ci_channel", "return_rate_by_channel")

        ui.note("Return rate counts only actions with a recorded result. A guest coming back shows what happened "
                "after the action, not proof that the action caused it.")
