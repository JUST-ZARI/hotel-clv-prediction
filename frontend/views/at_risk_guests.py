import streamlit as st

import charts
import components as ui
from auth import require_auth
from data import repository as repo
from style import icon

require_auth()

ui.page_header("At-Risk High-Value Guests",
               "High-value guests who have not returned within the selected inactivity period")

rm = ui.is_revenue_manager()
threshold = repo.at_risk_days()

EXPORT_COLS = ["guest_id", "predicted_clv", "clv_tier", "days_since_last_stay", "total_previous_stays",
               "risk_level", "recommended_action", "booking_channel"]
all_at_risk = repo.at_risk()


def _save_threshold(key: str) -> None:
    """Revenue Manager changed the shared at-risk threshold."""
    repo.set_at_risk_days(st.session_state[key])
    st.toast(f"At-risk threshold set to {st.session_state[key]} days for all users.", icon=":material/check_circle:")

# ---------------------------------------------------------------------------
# Alert banner
# ---------------------------------------------------------------------------
with st.container(key="ar_banner", horizontal=True, vertical_alignment="center", wrap=False):
    st.html(f"""
    <div class="ar-banner-body">
        <span class="ar-banner-ico">{icon("triangle-exclamation")}</span>
        <div>
            <div class="ar-banner-title">{len(all_at_risk):,} At-Risk High-Value Guests</div>
            <div class="ar-banner-text">These guests represent high predicted CLV and have not returned in
            {threshold}+ days. Immediate action is recommended.</div>
        </div>
    </div>""")
    st.space("stretch")
    with st.container(key="ar_banner_tools", horizontal=True, vertical_alignment="center", width="content"):
        if rm:
            # Keyed by the current value so a change made by another user shows up on rerun.
            th_key = f"ar_threshold_{threshold}"
            ui.filter_select("At-risk after", repo.AT_RISK_OPTIONS, th_key, format_func=lambda d: f"{d} days",
                             index=repo.AT_RISK_OPTIONS.index(threshold), width=230,
                             on_change=_save_threshold, args=(th_key,),
                             help="Applies to every user: the At-Risk list, the sidebar badge and the Action Board.")
        else:
            st.html(f'<span class="ar-rule">{icon("sliders")} At-risk rule: {threshold}+ days without a stay '
                    f'<em>(set by the Revenue Manager)</em></span>')
        with st.container(key="ar_export_all", width="content"):
            ui.download_csv("Export All", all_at_risk[EXPORT_COLS], "at_risk_guests_all.csv", key="ar_all_csv")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
MIN_CLV = [150_000, 200_000, 300_000, 400_000]
MIN_DAYS = [threshold] + [d for d in (60, 90, 120, 180) if d > threshold]
TIER_SCOPE = {"High / Platinum": None, "Platinum only": "Platinum", "High only": "High"}

with st.container(key="bar_ar", horizontal=True, vertical_alignment="center"):
    min_clv = ui.filter_select("Min CLV", MIN_CLV, "ar_min_clv", format_func=ui.ksh, width=225)
    min_days = ui.filter_select("Days Inactive", MIN_DAYS, "ar_days", format_func=lambda d: f"{d}+ days", width=235)
    scope = ui.filter_select("CLV Tier", list(TIER_SCOPE), "ar_scope", width=250)
    channel = ui.filter_select("Booking Channel", ["All Channels"] + repo.BOOKING_CHANNELS, "ar_channel", width=290)
    query = ui.search_box("ar_search")
    download_slot = st.container(width="content")

rows = repo.at_risk(min_clv, min_days)
if TIER_SCOPE[scope]:
    rows = rows[rows["tier_badge"] == TIER_SCOPE[scope]]
if channel != "All Channels":
    rows = rows[rows["booking_channel"] == channel]
if query.strip():
    rows = rows[rows["guest_id"].str.contains(query.strip(), case=False, regex=False)]

with download_slot:
    ui.download_csv("Download CSV", rows[EXPORT_COLS], "at_risk_guests_filtered.csv", key="ar_csv")

sort_by = st.session_state.get("ar_sort") or "Predicted CLV"
rows = rows.sort_values("predicted_clv" if sort_by == "Predicted CLV" else "days_since_last_stay",
                        ascending=False)
ui.reset_page_on_change("ar", min_clv, min_days, scope, channel, query, sort_by)
start, end = ui.paginate("ar", len(rows))
page = rows.iloc[start:end]

# ---------------------------------------------------------------------------
# Days inactive chart (guests on the current page)
# ---------------------------------------------------------------------------
with ui.card("ar_chart"):
    with st.container(horizontal=True, vertical_alignment="top"):
        ui.card_title("Days Inactive per At-Risk Guest",
                      f"Sorted by {sort_by} descending — colour coded by risk level")
        st.space("stretch")
        ui.export_menu("chart_inactive", page[["guest_id", "days_since_last_stay", "risk_level"]],
                       "days_inactive_at_risk")
    if page.empty:
        st.html('<div class="ds-empty">No guests match these filters.</div>')
    else:
        charts.show(
            charts.hbar_track(
                labels=page["guest_id"].tolist(),
                values=page["days_since_last_stay"].tolist(),
                colors=[charts.RISK_COLORS[r] for r in page["risk_level"]],
                value_text=[f"{d} days" for d in page["days_since_last_stay"]],
                max_value=max(180, int(rows["days_since_last_stay"].max())),
            ),
            key="chart_inactive", filename="days_inactive_at_risk",
        )
    st.html('<div class="ds-legend">'
            + "".join(f'<span><i class="fa-solid fa-circle" style="color:{c}"></i>{r}</span>'
                      for r, c in charts.RISK_COLORS.items()) + "</div>")

# ---------------------------------------------------------------------------
# Guest list
# ---------------------------------------------------------------------------
with ui.card("ar_list"):
    with st.container(horizontal=True, vertical_alignment="center"):
        ui.card_title("At-Risk Guest List")
        st.space("stretch")
        with st.container(key="ar_sortbox", horizontal=True, vertical_alignment="center", width="content"):
            st.html('<span class="ds-pager-info">Sort by:</span>')
            st.segmented_control("Sort by", ["Predicted CLV", "Days Inactive"], key="ar_sort",
                                 default="Predicted CLV", required=True, label_visibility="collapsed")

    ui.data_table("ar", page, [
        ui.Col("Guest ID", 1.0, kind="guest_link"),
        ui.Col("Predicted CLV (KSh)", 1.4, lambda r: f'<span class="ds-strong">{r["predicted_clv"]:,}</span>'),
        ui.Col("Days Since Last Stay", 1.4, lambda r: f'<span class="ds-text-red">{r["days_since_last_stay"]} days</span>'),
        ui.Col("Prev. Stays", 0.9, lambda r: str(r["total_previous_stays"])),
        ui.Col("Risk Level", 1.1, lambda r: ui.pill(r["risk_level"], ui.RISK_TONE[r["risk_level"]])),
        ui.Col("Recommended Action", 2.0, lambda r: ui.pill(r["recommended_action"], ui.action_tone(r["recommended_action"]))),
    ])
    ui.pagination_bar("ar", len(rows))

ui.css("""
.st-key-ar_banner {
    background: var(--red-50); border: 1px solid var(--red-200); border-radius: var(--r-lg);
    padding: 16px 20px !important; gap: 16px !important;
}
.ar-banner-body { display: flex; align-items: center; gap: 14px; }
.ar-banner-ico {
    width: 40px; height: 40px; flex-shrink: 0; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    background: var(--red-600); color: #FFFFFF; font-size: 1.064rem;
}
.ar-rule { font-size: 0.92rem; color: var(--red-700); white-space: nowrap; }
.ar-rule em { color: var(--ink-500); }
.st-key-ar_banner [class*="st-key-flt_"] [role="group"] { background: var(--surface) !important; }
.ar-banner-title { font-size: 1.12rem; font-weight: 700; color: var(--red-700); }
.ar-banner-text { margin-top: 2px; font-size: 0.952rem; color: var(--red-700); }
.st-key-ar_banner_tools { gap: 10px !important; flex-shrink: 0; }
.stApp .st-key-ar_export_all button[data-testid^="stBaseButton"] { background: var(--red-600) !important; border-color: var(--red-600) !important; }
.stApp .st-key-ar_export_all button[data-testid^="stBaseButton"]:hover { background: var(--red-700) !important; border-color: var(--red-700) !important; }
.st-key-ar_sortbox { gap: 8px !important; }
""")
