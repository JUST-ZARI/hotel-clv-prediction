from datetime import date

import pandas as pd
import streamlit as st

import charts
import components as ui
from auth import require_auth
from data import repository as repo
from style import alert, icon
from utils import HOTEL_NAME, role_label

require_auth()
rm = ui.is_revenue_manager()

ui.page_header("Guest Lookup", "Search for an individual guest and review their predicted lifetime value")

DEFAULT_GUEST = "G-10234"
CHANNELS = {"Email": "Send Email", "SMS": "Send SMS", "Phone call": "Log Call",
            "Front desk (in-stay)": "Log Front-Desk Offer"}

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
if "lookup_guest_id" not in st.session_state:
    st.session_state["lookup_guest_id"] = DEFAULT_GUEST
if st.session_state.get("_lookup_synced") != st.session_state["lookup_guest_id"]:
    # Arrived from "View Guest" elsewhere: show that ID in the search box.
    st.session_state["gl_query"] = st.session_state["lookup_guest_id"]
    st.session_state["_lookup_synced"] = st.session_state["lookup_guest_id"]


def _search() -> None:
    gid = repo.normalize_guest_id(st.session_state.get("gl_query", ""))
    st.session_state["_lookup_error"] = None
    if not gid:
        st.session_state["_lookup_error"] = "Enter a Guest ID to search."
    elif repo.get_guest(gid) is None:
        st.session_state["_lookup_error"] = f"No guest found with ID “{gid}”. Check the ID and try again."
    else:
        st.session_state["lookup_guest_id"] = st.session_state["_lookup_synced"] = gid
        st.session_state["gl_query"] = gid


with st.form("gl_search", border=False, enter_to_submit=True):
    with st.container(key="gl_searchbar", horizontal=True, vertical_alignment="center"):
        st.text_input("Guest ID", key="gl_query", type="search", placeholder="Enter Guest ID — e.g. G-10234",
                      label_visibility="collapsed")
        st.form_submit_button("Search", type="primary", on_click=_search)

if st.session_state.get("_lookup_error"):
    alert("warning", st.session_state["_lookup_error"])

g = repo.get_guest(st.session_state["lookup_guest_id"])
gid = g["guest_id"]

# ---------------------------------------------------------------------------
# Derived insights
# ---------------------------------------------------------------------------
all_guests = repo.guests()
avg_adr = all_guests["avg_daily_rate"].mean()
stays, adr, days = int(g["total_previous_stays"]), int(g["avg_daily_rate"]), int(g["days_since_last_stay"])
tenure_days = (repo.model_meta().predicted_at.date() - date(int(g["first_booking_year"]), 1, 1)).days
every = max(1, round(tenure_days / max(stays, 1)))


def band(value, cuts, labels):
    return next((lab for cut, lab in zip(cuts, labels) if value < cut), labels[-1])


insights = [
    ("repeat", "Repeat Visits", f"{stays} stays", band(stays, [3, 10], ["Occasional guest", "Returning guest", "Strong loyalty"]), ""),
    ("arrow-trend-up", "Spending Behaviour",
     "Above avg ADR" if adr > avg_adr * 1.1 else "Below avg ADR" if adr < avg_adr * 0.9 else "Around avg ADR",
     "Premium spender" if adr > avg_adr * 1.1 else "Value-conscious" if adr < avg_adr * 0.9 else "Typical spend",
     "green" if adr > avg_adr * 1.1 else ""),
    ("circle-xmark", "Cancellation", f"{int(g['cancellation_rate'])}% rate",
     band(int(g["cancellation_rate"]), [8, 15, 30], ["Very low", "Low", "Moderate", "High"]), ""),
    ("calendar", "Booking Frequency", f"Every {every} days",
     band(every, [60, 180], ["High frequency", "Regular", "Infrequent"]), ""),
    ("clock", "Recency", f"{days} days ago",
     band(days, [30, repo.at_risk_days()], ["Recently active", "Cooling off", "Inactive — at risk"]),
     "red" if days >= repo.at_risk_days() else ""),
    ("globe", "Booking Channel", g["booking_channel"].replace("Direct / Website", "Direct / Web"),
     {"Direct / Website": "High margin", "Online TA": "Commission-based", "Offline TA/TO": "Commission-based",
      "Corporate": "Negotiated rate", "Groups": "Group booking"}[g["booking_channel"]], ""),
]

# ---------------------------------------------------------------------------
# Profile + CLV
# ---------------------------------------------------------------------------
left, right = st.columns([2.2, 1], gap="small")

with left:
    with ui.card("gl_profile"):
        metrics = [
            ("Total Previous Stays", f"{stays}"),
            ("Average Daily Rate", ui.ksh(adr)),
            ("Avg. Length of Stay", f"{g['avg_length_of_stay']:.1f} nights"),
            ("Cancellation Rate", f"{int(g['cancellation_rate'])}%"),
            ("Booking Lead Time", f"{int(g['booking_lead_time'])} days"),
            ("Booking Channel", g["booking_channel"]),
            ("Repeat Guest", "Yes" if g["is_repeat_guest"] else "No"),
            ("Days Since Last Stay", f"{days} days"),
        ]
        cells = "".join(f'<div><div class="gl-k">{ui.esc(k)}</div><div class="gl-v">{ui.esc(v)}</div></div>'
                        for k, v in metrics)
        st.html(f"""
        <div class="gl-profile-head">
            <div><div class="gl-k">Guest Profile</div><div class="gl-id">{ui.esc(gid)}</div></div>
            {ui.tier_badge(g["tier_badge"])}
        </div>
        <div class="gl-metrics">{cells}</div>""")

    with ui.card("gl_insights"):
        ui.card_title("Behavioural Insights")
        tiles = "".join(f"""
        <div class="gl-tile">
            <div class="gl-tile-k">{icon(ic)} {ui.esc(k)}</div>
            <div class="gl-tile-v {('ds-text-' + tone) if tone else ''}">{ui.esc(v)}</div>
            <div class="gl-tile-c">{ui.esc(c)}</div>
        </div>""" for ic, k, v, c, tone in insights)
        st.html(f'<div class="gl-tiles">{tiles}</div>')

with right:
    tone = {"High": "teal", "Medium": "sage", "Low": "sky"}[g["clv_tier"]]
    top_pct = max(1, round((1 - g["clv_percentile"]) * 100))
    st.html(f"""
    <div class="gl-clv gl-clv-{tone}">
        <div class="gl-k">Predicted Customer Lifetime Value</div>
        <div class="gl-clv-v">{ui.ksh(g["predicted_clv"])}</div>
        <div class="gl-clv-tier">{ui.esc(g["clv_tier"])} value tier</div>
        <div class="gl-clv-c">Top {top_pct}% of all hotel guests · {ui.esc(g["model_used"])}</div>
    </div>""")

    with ui.card("gl_action"):
        st.html(f"""
        <div class="gl-rec-k">{icon("bolt")} Recommended Action</div>
        <div class="gl-rec-v">{ui.esc(g["recommended_action"])}</div>
        <div class="gl-rec-r">Reason: {ui.esc(g["recommended_action_reason"])}</div>""")
        if not rm:
            if st.button("Log Action", type="primary", width="stretch", key="gl_log"):
                repo.log_action(gid, g["recommended_action"], "Dashboard", "Pending")
                st.toast("Action logged as Pending.", icon=":material/check_circle:")

    drivers = repo.prediction_drivers(gid)
    with ui.card("gl_drivers"):
        ui.card_title("Prediction Drivers", "Top features influencing this guest's CLV prediction")
        charts.show(
            charts.hbar_track([d for d, _ in drivers], [v for _, v in drivers], [charts.SERIES[i % len(charts.SERIES)] for i in range(len(drivers))],
                              [f"{v}%" for _, v in drivers], max_value=100, height=30 * len(drivers) + 6),
            key="chart_drivers", filename=f"{gid}_prediction_drivers",
        )
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<span class="ds-pager-info">Download drivers</span>')
            st.space("stretch")
            ui.export_menu("chart_drivers", pd.DataFrame(drivers, columns=["feature", "importance_pct"]),
                           f"{gid}_prediction_drivers", label="PNG / CSV")

# ---------------------------------------------------------------------------
# Stay timeline
# ---------------------------------------------------------------------------
history = repo.stay_history(g)
earlier = max(0, stays - len(history))
with ui.card("gl_timeline"):
    ui.card_title("Historical Stay Timeline")
    items = "".join(f"""
    <div class="gl-stay">
        <span class="gl-stay-ico">{icon("hotel")}</span>
        <b>{s["date"]}</b><span>{s["nights"]} nights</span>
        <span class="gl-stay-amt">{ui.ksh(s["amount"])}</span><span>{s["room_type"]}</span>
    </div>""" for s in history)
    more = f'<div class="gl-more">+{earlier} earlier</div>' if earlier else ""
    st.html(f'<div class="gl-stays">{items}{more}</div>')

# ---------------------------------------------------------------------------
# Execute recommended action — Marketing Team
# ---------------------------------------------------------------------------
if not rm:
    with ui.card("gl_execute"):
        with st.container(horizontal=True, vertical_alignment="center"):
            ui.card_title("Execute Recommended Action", fa="paper-plane")
            st.space("stretch")
            st.html(f'<span class="ds-chip ds-chip-role-mt">{role_label(st.session_state.role)}</span>')
        channel = st.selectbox("Delivery channel", list(CHANNELS), key="gl_channel")
        default_msg = (
            f"Dear Valued Guest ({gid}),\n\n"
            f"As one of our {g['tier_badge']} guests, we would love to offer you a personalised experience "
            f"on your next visit: {g['recommended_action'].lower()}. Please find your exclusive offer enclosed.\n\n"
            f"— {HOTEL_NAME}, Revenue & Guest Relations"
        )
        if st.session_state.get("_gl_msg_for") != gid:
            st.session_state["gl_message"] = default_msg
            st.session_state["_gl_msg_for"] = gid
        st.text_area("Message preview", key="gl_message", height=130)
        verb = CHANNELS[channel]
        if st.button(verb, type="primary", width="stretch", key="gl_execute_btn", icon=":material/send:"):
            repo.log_action(gid, g["recommended_action"], channel, "Completed")
            st.toast(f"“{g['recommended_action']}” recorded as Completed via {channel}.",
                     icon=":material/check_circle:")

# ---------------------------------------------------------------------------
# Action logs
# ---------------------------------------------------------------------------
logs = repo.action_logs(gid)
status_tone = {"Completed": "green", "Pending": "amber", "Failed": "red"}
LOG_COLS = [("Action Taken", 2.2), ("Channel", 1.2), ("Status", 1.0), ("Time Stamp", 1.5), ("User", 1.3),
            ("Outcome", 1.6)]


def _save_outcome(log_id: int, key: str) -> None:
    repo.set_outcome(log_id, st.session_state[key])
    st.toast(f"Outcome updated: {st.session_state[key]}.", icon=":material/check_circle:")


with ui.card("gl_logs"):
    ui.card_title("Action Logs", "Actions recorded by the Marketing Team for this guest" if rm
                  else "Record whether the guest came back after each completed action")
    widths = [w for _, w in LOG_COLS]
    with st.container(key="tbl_gl_logs", gap=None):
        with st.container(key="tblhead_gl_logs"):
            for (h, _), col in zip(LOG_COLS, st.columns(widths, gap="small", vertical_alignment="center")):
                col.html(f'<span class="ds-th">{h}</span>')
        if logs.empty:
            st.html('<div class="ds-empty">No actions logged for this guest yet.</div>')
        for i, r in enumerate(logs.itertuples()):
            with st.container(key=f"tblrow_gl_logs_{i}"):
                c = st.columns(widths, gap="small", vertical_alignment="center")
                c[0].html(f'<span class="ds-td">{ui.esc(r.action_taken)}</span>')
                c[1].html(f'<span class="ds-td">{ui.esc(r.delivery_channel)}</span>')
                c[2].html(f'<span class="ds-td">{ui.pill(r.action_status, status_tone.get(r.action_status, "neutral"))}</span>')
                c[3].html(f'<span class="ds-td" style="color:var(--ink-500)">{r.logged_at:%d %b %Y, %H:%M}</span>')
                c[4].html(f'<span class="ds-td">{ui.esc(r.user_name or role_label(r.user_role))}</span>')
                if r.action_status != "Completed" or not isinstance(r.outcome, str):
                    c[5].html('<span class="ds-td" style="color:var(--ink-400)">—</span>')
                elif rm:
                    c[5].html(f'<span class="ds-td">{ui.pill(r.outcome, ui.OUTCOME_TONE[r.outcome])}</span>')
                else:
                    key = f"outcome_{r.log_id}"
                    with c[5], st.container(key=f"oc_{r.log_id}"):
                        st.selectbox("Outcome", repo.OUTCOMES, index=repo.OUTCOMES.index(r.outcome), key=key,
                                     label_visibility="collapsed", on_change=_save_outcome, args=(r.log_id, key))

ui.css("""
.st-key-gl_searchbar { gap: 10px !important; }
[class*="st-key-oc_"] [role="group"] { min-height: 32px !important; font-size: 0.9rem !important; }
.st-key-gl_searchbar .stTextInput { flex: 1; }
.st-key-gl_searchbar [data-testid="stTextInputRootElement"] { min-height: 46px; }
.st-key-gl_searchbar button { min-height: 46px !important; padding: 0 28px !important; }
[data-testid="stForm"]:has(.st-key-gl_searchbar) { border: none; padding: 0; }

.gl-k { font-size: 0.74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-600); }
.gl-profile-head { display: flex; justify-content: space-between; align-items: flex-start; }
.gl-id { margin-top: 2px; font-size: 1.85rem; font-weight: 700; color: var(--ink-900); }
.gl-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 32px; margin-top: 16px; }
.gl-v { margin-top: 2px; font-size: 1.5rem; font-weight: 700; color: var(--ink-900); font-variant-numeric: lining-nums; }

.gl-tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.gl-tile {
    border: 1px solid var(--line); border-radius: var(--r-md); padding: 12px 14px; background: var(--subtle);
    transition: border-color .15s var(--ease), background-color .15s var(--ease);
}
.gl-tile:hover { border-color: var(--brand-200); background: var(--surface); }
.gl-tile-k { display: flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; color: var(--ink-600); }
.gl-tile-k i { color: var(--brand-500); }
.gl-tile-v { margin-top: 6px; font-size: 1.3rem; font-weight: 700; color: var(--ink-900); }
.gl-tile-c { margin-top: 2px; font-size: 0.85rem; color: var(--ink-500); }

/* Predicted CLV: the page's key figure */
.gl-clv { border-radius: var(--r-lg); padding: 20px 22px; border: 1px solid; }
.gl-clv-teal { background: var(--brand-600); border-color: var(--brand-600); }
.gl-clv-teal .gl-k { color: rgba(255,255,255,.7); }
.gl-clv-teal .gl-clv-v { color: #FFFFFF; }
.gl-clv-teal .gl-clv-tier { color: var(--lime-400); }
.gl-clv-teal .gl-clv-c { color: rgba(255,255,255,.7); }
.gl-clv-sage { background: var(--sage-50); border-color: var(--sage-200); }
.gl-clv-sage .gl-clv-v, .gl-clv-sage .gl-clv-tier { color: var(--sage-700); }
.gl-clv-sky  { background: var(--sky-50);  border-color: var(--sky-200); }
.gl-clv-sky  .gl-clv-v, .gl-clv-sky  .gl-clv-tier { color: var(--sky-700); }
.gl-clv-v { margin-top: 8px; font-size: 2.4rem; font-weight: 700; line-height: 1.05; font-variant-numeric: lining-nums; }
.gl-clv-tier { margin-top: 4px; font-size: 1rem; font-weight: 700; }
.gl-clv-c { margin-top: 2px; font-size: 0.85rem; color: var(--ink-600); }

.gl-rec-k { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-900); }
.gl-rec-k i { color: var(--brand-600); }
.gl-rec-v { margin-top: 10px; font-size: 1.12rem; font-weight: 700; color: var(--brand-600); }
.gl-rec-r { margin-top: 4px; font-size: 0.92rem; line-height: 1.5; color: var(--ink-600); }

.gl-stays { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 28px; }
.gl-stay { display: flex; flex-direction: column; align-items: center; gap: 1px; min-width: 100px; text-align: center; font-size: 0.82rem; color: var(--ink-500); }
.gl-stay b { margin-top: 6px; font-size: 0.97rem; font-weight: 700; color: var(--ink-900); }
.gl-stay-amt { color: var(--ink-900) !important; font-weight: 700; }
.gl-stay-ico {
    width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); border: 1px solid var(--brand-100);
    transition: background-color .15s var(--ease), color .15s var(--ease);
}
.gl-stay:hover .gl-stay-ico { background: var(--brand-600); color: var(--lime-400); }
.gl-more { font-size: 0.92rem; font-weight: 700; color: var(--ink-700); padding: 6px 10px; border: 1px dashed var(--line-strong); border-radius: var(--r-md); }

@media (max-width: 900px) { .gl-tiles { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .gl-tiles, .gl-metrics { grid-template-columns: 1fr; } }
""")
