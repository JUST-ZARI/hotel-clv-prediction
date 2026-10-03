import streamlit as st

import charts
import components as ui
from auth import require_auth
from data import repository as repo

require_auth()
rm = ui.is_revenue_manager()

ui.page_header("Hotel Guest CLV Dashboard",
               "Overview of predicted customer lifetime value and recommended guest actions")

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
st.html('<div class="ds-impact"><span class="ds-impact-k">Last 30 days</span>'
        + "".join(f'<span class="ds-impact-i"><i class="fa-solid fa-{ic}"></i>{txt}</span>' for ic, txt in items)
        + "</div>")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
o = repo.overview()
ui.kpi_row([
    ui.Kpi("Total Guests", f"{o['total_guests']:,}", "All tracked hotel guests", "users"),
    ui.Kpi("High-Value Guests", f"{o['high_value_guests']:,}",
           f"{o['high_value_guests'] / o['total_guests']:.0%} of total guest base", "arrow-trend-up", "teal"),
    ui.Kpi("At-Risk High-Value", f"{o['at_risk_high_value']:,}",
           f"Inactive {repo.at_risk_days()}+ days", "triangle-exclamation", "red"),
    ui.Kpi("Avg. Predicted CLV", ui.ksh(o["avg_predicted_clv"]), "Across all guests", "chart-simple", "amber"),
])

queue = repo.action_queue()

# ---------------------------------------------------------------------------
# Top 10 chart — Revenue Manager only
# ---------------------------------------------------------------------------
if rm:
    top = queue.head(10)
    with ui.card("top10"):
        with st.container(horizontal=True, vertical_alignment="top"):
            ui.card_title("Top 10 Guests by Predicted CLV", "Sorted by predicted CLV — coloured by tier")
            st.space("stretch")
            ui.export_menu("chart_top10", top[["guest_id", "clv_tier", "predicted_clv"]],
                           "top10_guests_by_clv", label="Export PNG / CSV")
        charts.show(
            charts.hbar_track(
                labels=top["guest_id"].tolist(),
                values=top["predicted_clv"].tolist(),
                colors=[charts.TIER_COLORS[t] for t in top["clv_tier"]],
                value_text=[ui.ksh(v) for v in top["predicted_clv"]],
            ),
            key="chart_top10", filename="top10_guests_by_clv",
        )
        st.html('<div class="ds-legend">'
                + "".join(f'<span><i class="fa-solid fa-circle" style="color:{charts.TIER_COLORS[t]}"></i>{t}</span>'
                          for t in repo.TIERS) + "</div>")

# ---------------------------------------------------------------------------
# Guest action list
# ---------------------------------------------------------------------------
with ui.card("actions"):
    with st.container(horizontal=True, vertical_alignment="top"):
        ui.card_title("Guest Action List",
                      "Prioritised list of guests requiring immediate attention based on CLV predictions" if rm
                      else "Prioritised list of guests requiring campaign actions")
        st.space("stretch")
        ui.note("Sorted by predicted CLV descending")

    tier_opts = ["All Tiers"] + repo.TIERS
    action_opts = ["All Actions"] + sorted(queue["recommended_action"].unique())
    with st.container(key="bar_ab", horizontal=True, vertical_alignment="center"):
        tier = ui.filter_select("CLV Tier", tier_opts, "ab_tier")
        action = ui.filter_select("Recommended Action", action_opts, "ab_action", width=330)
        query = ui.search_box("ab_search")
        download_slot = st.container(width="content")

    rows = queue
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

    ui.reset_page_on_change("ab", tier, action, query)
    start, end = ui.paginate("ab", len(rows))

    cols = [
        ui.Col("Guest ID", 1.1, kind="guest_link"),
        ui.Col("CLV Tier", 1.0, lambda r: ui.tier_badge(r["tier_badge"])),
    ]
    if rm:
        cols.append(ui.Col("Predicted CLV (KSh)", 1.6, lambda r: f'<span class="ds-strong">{r["predicted_clv"]:,}</span>'))
    else:
        cols.append(ui.Col("Recommended Action", 2.0, lambda r: ui.action_text(r["recommended_action"])))
    cols += [
        ui.Col("Days Since Last Stay", 1.4, lambda r: f'{r["days_since_last_stay"]} days'),
        ui.Col("", 1.0, kind="view_button"),
    ]
    ui.data_table("ab", rows.iloc[start:end], cols)
    ui.pagination_bar("ab", len(rows))

ui.note(f"Predictions generated by {repo.model_meta().model_used} model trained on historical booking data. "
        "CLV tiers: High (>KSh 150,000), Medium (KSh 50,000–150,000), Low (<KSh 50,000).")
