"""System Administration: staff accounts, invitations and system health.

The administrator manages the system, not the business: they cannot open the
guest dashboards and the database does not let them read guest data (007).
"""

from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError

import auth
import components as ui
import messaging
from data import repository as repo
from style import alert

auth.require_auth({"admin"})
client = auth.user_client()

ui.page_header("System Administration", "Staff accounts, invitations and system health")


def _ts(value) -> str:
    if not value:
        return "—"
    return pd.Timestamp(value).tz_convert("Africa/Nairobi").strftime("%d %b %Y, %H:%M")


def _load():
    users = client.table("users").select("id, email, full_name, role, is_active, created_at") \
        .order("created_at").execute().data or []
    invites = client.table("invites").select("*").order("created_at", desc=True).limit(50).execute().data or []
    return users, invites


try:
    users, invites = _load()
except APIError:
    alert("error", "Administration tables are missing. Run supabase/007_admin_invites.sql in Supabase.")
    st.stop()

now = datetime.now(timezone.utc)


def invite_status(i: dict) -> str:
    if i.get("used_at"):
        return "Accepted"
    if i.get("revoked_at"):
        return "Cancelled"
    return "Expired" if pd.Timestamp(i["expires_at"]) < now else "Pending"


names = {u["id"]: u["full_name"] for u in users}
pending = [i for i in invites if invite_status(i) == "Pending"]
run = repo._runs(client)
latest = run[0] if run else None

ui.kpi_row([
    ui.Kpi("Active staff", f"{sum(u['is_active'] for u in users):,}", f"{len(users)} accounts in total", "users"),
    ui.Kpi("Pending invites", f"{len(pending)}", "Waiting to be accepted", "envelope", "amber"),
    ui.Kpi("Latest prediction run", _ts(latest["loaded_at"]).split(",")[0] if latest else "None",
           f"{latest['model_used']} · {latest['guests_predicted']:,} guests" if latest else "Load predictions first",
           "chart-simple", "brand"),
    ui.Kpi("Messaging", "Ready" if messaging.email_ready() else "Not set up",
           "Email" + (" + SMS" if messaging.sms_ready() else " only") if messaging.email_ready() else "Add keys to secrets",
           "paper-plane", "brand" if messaging.email_ready() else "red"),
])


# ---------------------------------------------------------------------------
# Invite a staff member
# ---------------------------------------------------------------------------
def _issue(email: str, role: str) -> None:
    try:
        code = auth.create_invite(email, role)
    except auth.AuthFailure as e:
        st.session_state["_adm_msg"] = ("warning", e.message, None)
        return
    try:
        auth.send_invite_email(auth.normalize_email(email), role, code)
        msg = ("success", f"Invitation emailed to {email}.", code)
    except messaging.SendError as e:
        msg = ("warning", f"The invite was created but the email failed ({e}). Give them the code below.", code)
    st.session_state["_adm_msg"] = msg


with ui.card("adm_invite"):
    ui.card_title("Invite a staff member", "A single-use code is generated and emailed. It expires after 7 days.")
    with st.form("adm_invite_form", border=False, clear_on_submit=True):
        c1, c2 = st.columns([2, 1], gap="small")
        email = c1.text_input("Email address", placeholder="name@hotel.com")
        role = c2.selectbox("Role", list(auth.ROLES), format_func=auth.ROLES.get)
        if st.form_submit_button("Send invitation", type="primary", icon=":material/send:"):
            _issue(email, role)
            st.rerun()
    msg = st.session_state.pop("_adm_msg", None)
    if msg:
        alert(msg[0], msg[1])
        if msg[2]:
            st.code(msg[2], language=None)
            ui.note("Shown once. The code is stored only in scrambled (hashed) form, so it cannot be looked up later.")


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------
TONE = {"Pending": "amber", "Accepted": "green", "Cancelled": "neutral", "Expired": "red"}

with ui.card("adm_invites"):
    ui.card_title("Invitations", "Most recent 50")
    if not invites:
        st.html('<div class="ds-empty">No invitations yet.</div>')
    for i in invites:
        status = invite_status(i)
        c = st.columns([2.4, 1.4, 1.0, 1.6, 1.4, 1.6], gap="small", vertical_alignment="center")
        c[0].html(f'<span class="ds-td">{ui.esc(i["email"])}</span>')
        c[1].html(f'<span class="ds-td">{ui.esc(auth.ROLES.get(i["role"], i["role"]))}</span>')
        c[2].html(f'<span class="ds-td">{ui.pill(status, TONE[status])}</span>')
        c[3].html(f'<span class="ds-td" style="color:var(--ink-500)">Expires {_ts(i["expires_at"])}</span>')
        c[4].html(f'<span class="ds-td" style="color:var(--ink-500)">{ui.esc(names.get(i["invited_by"], "—"))}</span>')
        if status in ("Pending", "Expired"):
            with c[5], st.container(horizontal=True, gap="small"):
                if st.button("Resend", key=f"adm_resend_{i['invite_id']}", type="secondary"):
                    _issue(i["email"], i["role"])
                    st.rerun()
                if status == "Pending" and st.button("Cancel", key=f"adm_cancel_{i['invite_id']}", type="tertiary"):
                    auth.revoke_invite(i["invite_id"])
                    st.toast("Invitation cancelled.", icon=":material/check_circle:")
                    st.rerun()


# ---------------------------------------------------------------------------
# Staff accounts
# ---------------------------------------------------------------------------
try:
    signed_in = auth.last_sign_ins()
except Exception:
    signed_in = {}


def _change_role(uid: str, key: str) -> None:
    try:
        auth.set_role(uid, st.session_state[key])
        st.toast("Role updated.", icon=":material/check_circle:")
    except auth.AuthFailure as e:
        st.toast(e.message, icon=":material/error:")


with ui.card("adm_users"):
    ui.card_title("Staff accounts", "Change roles, or deactivate someone who has left. Deactivated accounts cannot "
                                    "sign in, and any open session ends within five minutes.")
    for u in users:
        me = u["id"] == st.session_state.get("user_id")
        c = st.columns([1.8, 2.2, 1.8, 1.1, 1.6, 1.3], gap="small", vertical_alignment="center")
        c[0].html(f'<span class="ds-td ds-strong">{ui.esc(u["full_name"])}{" (you)" if me else ""}</span>')
        c[1].html(f'<span class="ds-td">{ui.esc(u["email"])}</span>')
        key = f"adm_role_{u['id']}"
        c[2].selectbox("Role", list(auth.ROLES), index=list(auth.ROLES).index(u["role"]), key=key,
                       format_func=auth.ROLES.get, label_visibility="collapsed", disabled=me,
                       on_change=_change_role, args=(u["id"], key))
        c[3].html(f'<span class="ds-td">{ui.pill("Active", "green") if u["is_active"] else ui.pill("Deactivated", "red")}</span>')
        c[4].html(f'<span class="ds-td" style="color:var(--ink-500)">Last sign-in {_ts(signed_in.get(u["id"]))}</span>')
        if not me:
            label = "Deactivate" if u["is_active"] else "Reactivate"
            if c[5].button(label, key=f"adm_act_{u['id']}", type="secondary" if u["is_active"] else "primary"):
                try:
                    auth.set_active(u["id"], not u["is_active"])
                    st.toast(f"{u['full_name']} {'deactivated' if u['is_active'] else 'reactivated'}.",
                             icon=":material/check_circle:")
                except auth.AuthFailure as e:
                    st.toast(e.message, icon=":material/error:")
                st.rerun()


# ---------------------------------------------------------------------------
# System health
# ---------------------------------------------------------------------------
with ui.card("adm_health"):
    ui.card_title("System health")
    if latest:
        rows = [("Model in use", latest["model_used"]),
                ("Predictions loaded", _ts(latest["loaded_at"])),
                ("Guests predicted", f"{latest['guests_predicted']:,}"),
                ("Test performance", f"R² {float(latest['test_r2']):.3f} · MAE KSh {float(latest['test_mae']):,.0f}"),
                ("Prediction runs kept", f"{len(run)} (the newest is shown in the dashboards)"),
                ("Email", "Configured" if messaging.email_ready() else "Not configured"),
                ("SMS", ("Configured" + (" (sandbox)" if messaging.is_sandbox() else "")) if messaging.sms_ready()
                 else "Not configured")]
        st.html('<table class="ds-table"><tbody>' + "".join(
            f'<tr><td class="muted">{ui.esc(k)}</td><td class="ds-strong">{ui.esc(v)}</td></tr>' for k, v in rows)
            + "</tbody></table>")
    else:
        alert("warning", "No prediction run has been loaded. Run supabase/load_predictions.py.")
