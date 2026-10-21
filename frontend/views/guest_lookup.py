import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError

import charts
import components as ui
import messaging
from auth import require_auth
from data import repository as repo
from style import alert, icon
from utils import HOTEL_NAME, role_label

require_auth()
rm = ui.is_revenue_manager()

ui.page_header("Guest Lookup", "Search for an individual guest and review their predicted lifetime value")

CHANNELS = {"Email": "Send Email", "SMS": "Send SMS"}

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
if "lookup_guest_id" not in st.session_state:
    st.session_state["lookup_guest_id"] = repo.default_guest_id()
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
        st.text_input("Guest ID", key="gl_query", type="search", placeholder="Enter Guest ID — e.g. G-000123",
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
CHANNEL_NOTE = {"Direct": "High margin", "TA/TO": "Commission-based", "Corporate": "Negotiated rate",
                "GDS": "Commission-based"}


def band(value, cuts, labels):
    return next((lab for cut, lab in zip(cuts, labels) if value < cut), labels[-1])


def _decision_panel(guest_id: str, g: pd.Series, decision: dict) -> None:
    """Revenue Manager: override the recommended action or flag the guest as a priority, with a reason.
    Decisions are kept as feedback for future retraining."""
    choices = ["Override action", "Flag priority"]
    if decision["override"]:
        choices.append("Clear override")
    if decision["priority"]:
        choices.remove("Flag priority")
        choices.append("Remove priority")
    labels = {"Override action": "Use a different action", "Flag priority": "Flag as priority guest",
              "Clear override": "Go back to the model's action", "Remove priority": "Remove priority flag"}
    with st.expander("Revenue Manager decision", icon=":material/gavel:"):
        with st.form(f"gl_decision_{guest_id}", border=False, clear_on_submit=True):
            kind = st.selectbox("Decision", choices, format_func=labels.get)
            new_action = st.selectbox("Action to use instead (for “Use a different action”)",
                                      [a for a in repo.ACTIONS if a != g["recommended_action"]])
            reason = st.text_area("Reason", placeholder="e.g. Long-standing corporate client; call personally.",
                                  height=80)
            if st.form_submit_button("Save decision", type="primary", width="stretch"):
                try:
                    repo.record_decision(guest_id, kind, reason, new_action if kind == "Override action" else None)
                except ValueError as e:
                    alert("warning", str(e))
                except APIError:
                    alert("error", "The decision could not be saved. Only the Revenue Manager can record decisions.")
                else:
                    st.toast("Decision saved. Marketing now sees it on this guest.", icon=":material/check_circle:")
                    st.rerun()
        ui.note("Every decision and its reason is kept with the guest's outcomes as feedback for retraining "
                "the model.")


def _decision_history(guest_id: str) -> None:
    hist = repo.decision_history(guest_id)
    if hist.empty:
        return
    rows = "".join(
        f'<div class="gl-dec"><b>{ui.esc(r.decision_type)}</b>'
        + (f' → {ui.esc(r.new_action)}' if isinstance(r.new_action, str) else "")
        + f'<span>{ui.esc(r.reason)}</span>'
        f'<em>{ui.esc(r.user_name or "Revenue Manager")} · {r.decided_at:%d %b %Y, %H:%M}</em></div>'
        for r in hist.itertuples())
    with st.expander(f"Decision history ({len(hist)})", icon=":material/history:"):
        st.html(f'<div class="gl-decs">{rows}</div>')


def _log(guest_id: str, action: str, channel: str, status: str, recipient_masked: str | None = None,
         provider_id: str | None = None) -> None:
    try:
        repo.log_action(guest_id, action, channel, status, recipient_masked, provider_id)
    except APIError:
        st.toast("The action could not be saved. Please try again.", icon=":material/error:")
        return
    if status == "Failed":
        st.toast("The failed attempt was recorded in the action log.", icon=":material/error:")
    elif recipient_masked:
        st.toast(f"{channel} sent to {recipient_masked} and recorded.", icon=":material/check_circle:")
    else:
        st.toast(f"“{action}” recorded as {status}" + (f" via {channel}." if status == "Completed" else "."),
                 icon=":material/check_circle:")


insights = [
    ("repeat", "Repeat Visits", f"{stays} previous stays",
     band(stays, [1, 3, 10], ["First-time guest", "Occasional guest", "Returning guest", "Strong loyalty"]), ""),
    ("arrow-trend-up", "Spending Behaviour",
     "Above avg ADR" if adr > avg_adr * 1.1 else "Below avg ADR" if adr < avg_adr * 0.9 else "Around avg ADR",
     "Premium spender" if adr > avg_adr * 1.1 else "Value-conscious" if adr < avg_adr * 0.9 else "Typical spend",
     "green" if adr > avg_adr * 1.1 else ""),
    ("circle-xmark", "Cancellation", f"{int(g['cancellation_rate'])}% rate",
     band(int(g["cancellation_rate"]), [8, 15, 30], ["Very low", "Low", "Moderate", "High"]), ""),
    ("hotel", "Hotel & Segment", str(g["hotel_type"]), f"{g['market_segment']} · {g['guest_type']}", ""),
    ("clock", "Recency", f"{days:,} days ago",
     band(days, [30, repo.at_risk_days()], ["Recently active", "Cooling off", "Inactive — at risk"]),
     "red" if days >= repo.at_risk_days() else ""),
    ("globe", "Booking Channel", str(g["booking_channel"]), CHANNEL_NOTE.get(str(g["booking_channel"]), "Other"), ""),
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
            <div class="gl-badges">{ui.tier_badge(g["tier_badge"])}
            {ui.pill("Priority (Revenue Manager)", "navy") if g["is_priority"] else ""}</div>
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
    tone = {"High": "brand", "Medium": "sage", "Low": "sky"}[g["clv_tier"]]
    top_pct = max(1, round((1 - g["clv_percentile"]) * 100))
    st.html(f"""
    <div class="gl-clv gl-clv-{tone}">
        <div class="gl-k">Predicted Customer Lifetime Value</div>
        <div class="gl-clv-v">{ui.ksh(g["predicted_clv"])}</div>
        <div class="gl-clv-tier">{ui.esc(g["clv_tier"])} value tier</div>
        <div class="gl-clv-c">Top {top_pct}% of all hotel guests · {ui.esc(g["model_used"])}</div>
    </div>""")

    decision = g["decision"]
    with ui.card("gl_action"):
        overridden = decision["override"] is not None
        st.html(f"""
        <div class="gl-rec-k">{icon("bolt")} Recommended Action
            {ui.pill("Set by Revenue Manager", "amber") if overridden else ""}</div>
        <div class="gl-rec-v">{ui.esc(g["recommended_action"])}</div>
        <div class="gl-rec-r">Reason: {ui.esc(g["recommended_action_reason"])}</div>
        {f'<div class="gl-rec-r">Model suggested: {ui.esc(g["model_action"])}</div>' if overridden else ""}""")
        if not rm:
            if st.button("Log Action", type="primary", width="stretch", key="gl_log"):
                _log(gid, g["recommended_action"], "Dashboard", "Pending")
        elif repo.decisions_enabled():
            _decision_panel(gid, g, decision)
        else:
            ui.note("Revenue Manager decisions are not set up yet: run supabase/006_rm_decisions.sql in Supabase.")
        _decision_history(gid)

    drivers = repo.prediction_drivers(gid)
    with ui.card("gl_drivers"):
        ui.card_title("Prediction Drivers", "Share of the model's reasoning for this guest — ▲ raised, ▼ lowered the CLV")
        if not drivers:
            st.html('<div class="ds-empty">No driver details stored for this prediction.</div>')
        else:
            charts.show(
                charts.hbar_track([d for d, _, _ in drivers], [v for _, v, _ in drivers],
                                  [charts.SERIES[i % len(charts.SERIES)] for i in range(len(drivers))],
                                  [f"{'▲' if way == 'up' else '▼'} {v:.0f}%" for _, v, way in drivers],
                                  max_value=100, height=30 * len(drivers) + 6),
                key="chart_drivers", filename=f"{gid}_prediction_drivers",
            )
            with st.container(horizontal=True, vertical_alignment="center"):
                st.html('<span class="ds-pager-info">Download drivers</span>')
                st.space("stretch")
                ui.export_menu("chart_drivers", pd.DataFrame(drivers, columns=["feature", "impact_pct", "direction"]),
                               f"{gid}_prediction_drivers", label="PNG / CSV")

# ---------------------------------------------------------------------------
# Stay timeline
# ---------------------------------------------------------------------------
history = repo.stay_history(g)
with ui.card("gl_timeline"):
    ui.card_title("Stay History", "Latest booking on record · earlier stays are known by count only")
    items = "".join(f"""
    <div class="gl-stay">
        <span class="gl-stay-ico">{icon("hotel")}</span>
        <b>{s["date"]}</b><span>{s["nights"]} night{"s" if s["nights"] != 1 else ""} · {s["status"]}</span>
        <span class="gl-stay-amt">{ui.ksh(s["amount"])} / night</span><span>{ui.esc(s["room_type"])}</span>
    </div>""" for s in history)
    more = (f'<div class="gl-more">+{stays} earlier stay{"s" if stays != 1 else ""}</div>' if stays
            else '<div class="gl-more">No earlier stays</div>')
    st.html(f'<div class="gl-stays">{items}{more}</div>')

def _messages(action: str) -> tuple[str, dict[str, str]]:
    """Email subject plus Email and SMS text for a recommended action, written as the hotel."""
    a = action.lower()
    if "upsell" in a:
        subject = f"An upgrade for your next stay at {HOTEL_NAME}"
        lead = ("As one of our valued guests, we would like to make your next stay even more special. "
                "On your next booking we are pleased to offer you an upgrade to one of our suites, "
                "with late check-out and breakfast for two included, subject to availability.")
        sms = (f"{HOTEL_NAME}: As a valued guest, enjoy a suite upgrade with breakfast for two and late "
               f"check-out on your next stay. Reply to this message to reserve. T&Cs apply.")
    elif any(k in a for k in ("loyalty", "concierge")):
        subject = f"Thank you for staying with {HOTEL_NAME}"
        lead = ("Thank you for choosing us time and again. As a token of our appreciation, you are invited "
                "to enjoy exclusive member privileges on your next visit, including a complimentary welcome "
                "drink, priority check-in and a dedicated guest relations contact who will arrange every "
                "detail of your stay.")
        sms = (f"{HOTEL_NAME}: Thank you for staying with us. Enjoy priority check-in and a complimentary "
               f"welcome drink on your next visit. Reply to this message to book.")
    elif "cost-efficient" in a:
        subject = f"What's new at {HOTEL_NAME}"
        lead = ("We have some exciting news to share: our restaurant has a new seasonal menu, and our "
                "weekend packages are now available at special rates. We would love to welcome you back.")
        sms = (f"{HOTEL_NAME}: Our new seasonal menu and weekend packages are here. "
               f"Reply to this message to book your stay.")
    else:   # win-back, retention and re-engagement actions
        subject = f"We miss you at {HOTEL_NAME}"
        lead = ("It has been a while since your last visit, and we would love to welcome you back. "
                "As a valued guest, you are invited to enjoy a special returning-guest rate on your next "
                "stay, together with a complimentary room upgrade, subject to availability.")
        sms = (f"{HOTEL_NAME}: We miss you! Enjoy a special returning-guest rate and a complimentary room "
               f"upgrade on your next stay. Reply to this message to book. T&Cs apply.")
    email = (f"Dear Valued Guest,\n\n"
             f"Warm greetings from {HOTEL_NAME}.\n\n"
             f"{lead}\n\n"
             f"To reserve, simply reply to this email and our reservations team will be glad to assist you.\n\n"
             f"We look forward to welcoming you back.\n\n"
             f"Warm regards,\n"
             f"Guest Relations Team\n"
             f"{HOTEL_NAME}, Nairobi")
    return subject, {"Email": email, "SMS": sms}


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
        # Guest-ready message for the recommended action, filled in for the guest on screen (editable).
        subject, defaults = _messages(g["recommended_action"])
        if st.session_state.get("_gl_msg_for") != gid:   # new guest: fresh text for every channel
            for ch in CHANNELS:
                st.session_state[f"gl_message_{ch}"] = defaults[ch]
            st.session_state["gl_subject"] = subject
            st.session_state["_gl_msg_for"] = gid

        ready = messaging.email_ready() if channel == "Email" else messaging.sms_ready()
        recipient = st.text_input(
            "Send to", key=f"gl_to_{channel}",
            placeholder="name@strathmore.edu" if channel == "Email" else "0712 345 678 or +254712345678")
        if channel == "Email":
            st.text_input("Subject", key="gl_subject")
        st.text_area("Message", key=f"gl_message_{channel}", height=220)

        if not ready:
            alert("warning", f"{channel} sending is not set up yet: add the keys under [messaging] in "
                             ".streamlit/secrets.toml (see secrets.example.toml).")

        # Always clickable (a disabled button can swallow the first click after typing); checked on click.
        if st.button(CHANNELS[channel], type="primary", width="stretch", key="gl_execute_btn",
                     icon=":material/send:", disabled=not ready):
            body = st.session_state[f"gl_message_{channel}"]
            try:
                if not recipient.strip():
                    raise messaging.SendError("Enter who to send to: an email address or phone number.")
                to = (messaging.normalize_email(recipient) if channel == "Email"
                      else messaging.normalize_phone(recipient))
                if repo.sends_last_24h() >= messaging.daily_limit():
                    raise messaging.SendError(f"Daily limit reached ({messaging.daily_limit()} messages in "
                                              "24 hours). Try again later.")
            except messaging.SendError as e:
                alert("warning", str(e))           # nothing was attempted, so nothing is logged
                to = None
            if to:
                try:
                    with st.spinner(f"Sending {channel.lower()}…"):
                        sent = (messaging.send_email(to, st.session_state["gl_subject"], body, HOTEL_NAME)
                                if channel == "Email" else messaging.send_sms(to, body))
                except messaging.SendError as e:
                    alert("error", str(e))
                    _log(gid, g["recommended_action"], channel, "Failed", messaging.mask(to))
                else:
                    _log(gid, g["recommended_action"], channel, "Completed", sent.recipient_masked,
                         sent.provider_id)

# ---------------------------------------------------------------------------
# Action logs
# ---------------------------------------------------------------------------
logs = repo.action_logs(gid)
status_tone = {"Completed": "green", "Pending": "amber", "Failed": "red"}
LOG_COLS = [("Action Taken", 2.2), ("Channel", 1.2), ("Status", 1.0), ("Time Stamp", 1.5), ("User", 1.3),
            ("Outcome", 1.6)]


def _save_outcome(log_id: str, key: str) -> None:
    try:
        repo.set_outcome(log_id, st.session_state[key])
    except (PermissionError, APIError):
        st.toast("The outcome could not be saved.", icon=":material/error:")
        return
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
                to = getattr(r, "recipient_masked", None)
                c[1].html(f'<span class="ds-td">{ui.esc(r.delivery_channel)}'
                          + (f'<br><small style="color:var(--ink-500)">to {ui.esc(to)}</small>'
                             if isinstance(to, str) else "") + "</span>")
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

.gl-k { font-size: 0.8rem; font-weight: 500; color: var(--ink-500); }
.gl-profile-head { display: flex; justify-content: space-between; align-items: flex-start; }
.gl-id { margin-top: 2px; font-size: 1.6rem; font-weight: 600; letter-spacing: -0.02em; color: var(--ink-900); }
.gl-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 32px; margin-top: 16px; }
.gl-v { margin-top: 2px; font-size: 1.2rem; font-weight: 600; color: var(--ink-900); font-variant-numeric: tabular-nums; }

.gl-tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.gl-tile {
    border: 1px solid var(--line); border-radius: var(--r-md); padding: 12px 14px; background: var(--subtle);
    transition: border-color .25s var(--ease), background-color .25s var(--ease), transform .25s var(--ease), box-shadow .25s var(--ease);
}
.gl-tile:hover { border-color: var(--brand-200); background: var(--surface); transform: translateY(-2px); box-shadow: var(--shadow-card); }
.gl-tile-k { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 500; color: var(--ink-500); }
.gl-tile-k i { color: var(--brand-500); }
.gl-tile-v { margin-top: 6px; font-size: 1.05rem; font-weight: 600; color: var(--ink-900); }
.gl-tile-c { margin-top: 2px; font-size: 0.8rem; color: var(--ink-500); }

/* Predicted CLV: the page's key figure */
.gl-clv { border-radius: var(--r-lg); padding: 20px 22px; border: 1px solid; animation: ds-rise .5s var(--ease) both; }
.gl-clv-brand { background: radial-gradient(500px 220px at 100% 0%, rgba(168,224,190,.22), rgba(168,224,190,0) 60%),
                linear-gradient(140deg, var(--brand-600), var(--brand-700)); border-color: var(--brand-700);
                box-shadow: 0 18px 36px -22px rgba(0,63,43,.8); }
.gl-clv-brand .gl-k { color: rgba(255,255,255,.7); }
.gl-clv-brand .gl-clv-v { color: #FFFFFF; }
.gl-clv-brand .gl-clv-tier { color: var(--mint-300); }
.gl-clv-brand .gl-clv-c { color: rgba(255,255,255,.7); }
.gl-clv-sage { background: var(--sage-50); border-color: var(--sage-200); }
.gl-clv-sage .gl-clv-v, .gl-clv-sage .gl-clv-tier { color: var(--sage-700); }
.gl-clv-sky  { background: var(--sky-50);  border-color: var(--sky-200); }
.gl-clv-sky  .gl-clv-v, .gl-clv-sky  .gl-clv-tier { color: var(--sky-700); }
.gl-clv-v { margin-top: 8px; font-size: 2.1rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; font-variant-numeric: tabular-nums; }
.gl-clv-tier { margin-top: 4px; font-size: 0.9rem; font-weight: 500; }
.gl-clv-c { margin-top: 2px; font-size: 0.8rem; color: var(--ink-600); }

.gl-badges { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.gl-decs { display: flex; flex-direction: column; gap: 10px; }
.gl-dec { display: flex; flex-direction: column; gap: 2px; font-size: 0.9rem; color: var(--ink-800);
          padding-bottom: 8px; border-bottom: 1px solid var(--line); }
.gl-dec span { color: var(--ink-700); }
.gl-dec em { font-style: normal; font-size: 0.8rem; color: var(--ink-500); }
.gl-rec-k { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; font-weight: 500; color: var(--ink-500); }
.gl-rec-k i { color: var(--brand-600); }
.gl-rec-v { margin-top: 10px; font-size: 1.05rem; font-weight: 600; color: var(--ink-900); }
.gl-rec-r { margin-top: 4px; font-size: 0.85rem; line-height: 1.5; color: var(--ink-600); }

.gl-stays { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 28px; }
.gl-stay { display: flex; flex-direction: column; align-items: center; gap: 1px; min-width: 100px; text-align: center; font-size: 0.82rem; color: var(--ink-500); }
.gl-stay b { margin-top: 6px; font-size: 0.9rem; font-weight: 600; color: var(--ink-900); }
.gl-stay-amt { color: var(--ink-900) !important; font-weight: 600; }
.gl-stay-ico {
    width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); border: 1px solid var(--brand-100);
    transition: background-color .15s var(--ease), color .15s var(--ease);
}
.gl-stay:hover .gl-stay-ico { background: var(--brand-600); color: #FFFFFF; }
.gl-more { font-size: 0.85rem; font-weight: 500; color: var(--ink-700); padding: 6px 10px; border: 1px dashed var(--line-strong); border-radius: var(--r-md); }

@media (max-width: 900px) { .gl-tiles { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .gl-tiles, .gl-metrics { grid-template-columns: 1fr; } }
""")
