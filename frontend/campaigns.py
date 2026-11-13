"""
Marketing Team tools on the Action Board:

- Bulk send: email or SMS the waiting priority guests (5, 10, 25 or 50 at a time), or the
  guests ticked on the Guest Action List, within the daily limit. Each guest gets the template
  that matches their recommended action. With test_recipient (email) or test_phone (SMS) set
  under [messaging] in secrets, every message goes there instead (test mode), Guest ID shown.
- Follow-up reminders: actions whose outcome has been 'Waiting' for too long, so Marketing
  records the result (keeping Campaign Insights accurate) or sends a second message.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError

import components as ui
import messaging
import templates
from data import repository as repo
from style import alert
from utils import HOTEL_NAME

BATCH_SIZES = [5, 10, 25, 50]
DEFAULT_BATCH = 10


# ---------------------------------------------------------------------------
# Bulk email to priority guests
# ---------------------------------------------------------------------------

def _valid_email(raw: str | None) -> bool:
    try:
        messaging.normalize_email(raw or "")
        return True
    except messaging.SendError:
        return False


CHANNELS = ["Email", "SMS"]
NOUN = {"Email": ("email", "emails"), "SMS": ("SMS", "SMS")}


def _log(guest_id: str, action: str, channel: str, status: str, masked: str | None,
         provider_id: str | None = None) -> bool:
    try:
        repo.log_action(guest_id, action, channel, status, masked, provider_id)
        return True
    except APIError:
        return False


def _noun(channel: str, n: int) -> str:
    one, many = NOUN[channel]
    return f"{n} {one if n == 1 else many}"


def _compose(cands: pd.DataFrame, key: str, size: int | None, lead: list[str]) -> None:
    """Shared form: choose Email or SMS, check limits and test mode, preview, send.

    `size` caps the batch (None = every guest in `cands`). In test mode every message goes to
    test_recipient (email) or test_phone (SMS) instead of the guests, with the Guest ID shown.
    """
    channel = st.segmented_control("Send by", CHANNELS, default="Email", key=f"{key}_channel",
                                   required=True) or "Email"
    email = channel == "Email"
    test_to = messaging.test_recipient() if email else messaging.test_phone()
    ready = messaging.email_ready() if email else messaging.sms_ready()
    limit = messaging.daily_limit()
    left = max(0, limit - repo.sends_last_24h())

    recipients: dict[str, str] = {}
    skipped = 0
    if not test_to and not cands.empty:
        if email:
            found = repo.guest_emails(cands["guest_id"].tolist())
            recipients = {g: e for g, e in found.items() if _valid_email(e)}
        ok = cands["guest_id"].isin(list(recipients))      # guests have no phone numbers on record
        skipped = int((~ok).sum())
        cands = cands[ok]
    want = len(cands) if size is None else min(size, len(cands))
    batch = cands.head(min(want, left))

    counts = batch["recommended_action"].value_counts()
    st.html('<ul class="bk-list">' + "".join(f"<li>{x}</li>" for x in lead)
            + "".join(f"<li>{n} × {ui.esc(a)}</li>" for a, n in counts.items())
            + f"<li><b>{left}</b> of {limit} messages left today (daily limit)</li></ul>")
    if test_to:
        where = "the subject" if email else "the message"
        alert("info", f"Test mode: every {NOUN[channel][0]} goes to {messaging.mask(test_to)} instead of the "
                      f"guest, with the Guest ID in {where}.")
    elif skipped and email:
        alert("warning", f"{skipped} guest{'s' if skipped != 1 else ''} with demo addresses (@example.com) cannot "
                         "receive email and will be skipped. Add test_recipient under [messaging] in secrets to "
                         "test with your own inbox.")
    elif skipped:
        alert("warning", "The guests in the data have no phone numbers. Add test_phone under [messaging] in "
                         "secrets to test with your own phone.")
    if not ready:
        alert("warning", "Email is not set up: add gmail_address and gmail_app_password under [messaging] in "
                         "secrets." if email else
                         "SMS is not set up: add africastalking_username and africastalking_api_key under "
                         "[messaging] in secrets.")
    elif left == 0:
        alert("warning", "Daily limit reached. Try again later, or raise daily_limit under [messaging] in secrets.")
    elif len(batch) < want:
        ui.note(f"Only {left} sends are left today, so only the first {len(batch)} guests will be contacted.")
    if not email and ready and messaging.is_sandbox():
        ui.note("Africa's Talking sandbox: the SMS appear in the Africa's Talking simulator, not on a real phone.")

    if not batch.empty:
        first = batch.iloc[0]
        subject, texts = templates.messages(templates.template_for(first["recommended_action"]))
        with st.expander(f"Preview: {NOUN[channel][0]} to {first['guest_id']}",
                         icon=":material/mail:" if email else ":material/sms:"):
            st.html((f"<p class='bk-subj'><b>Subject:</b> {ui.esc(subject)}</p>" if email else "")
                    + f"<pre class='bk-body'>{ui.esc(texts[channel])}</pre>")

    n = len(batch)
    if st.button(f"Send {_noun(channel, n)}", type="primary", width="stretch", icon=":material/send:",
                 key=f"{key}_send", disabled=n == 0 or not ready):
        st.session_state["_bulk_done"] = _send(batch, recipients, test_to, channel)


def _dialog_body(cands: pd.DataFrame, key: str, size: int | None, lead: list[str], on_done=None) -> None:
    done = st.session_state.get("_bulk_done")
    if done:
        _results(done, on_done)
        return
    form = st.empty()     # replaced by the results once the messages are sent
    with form.container():
        _compose(cands, key, size, lead)
    if st.session_state.get("_bulk_done"):
        form.empty()
        _results(st.session_state["_bulk_done"], on_done)
    ui.css("""
    .bk-list { margin: 0 0 6px; padding-left: 18px; font-size: 0.92rem; color: var(--ink-800); line-height: 1.7; }
    .bk-subj { margin: 0 0 6px; font-size: 0.9rem; }
    .bk-body { white-space: pre-wrap; font-family: inherit; font-size: 0.85rem; margin: 0; color: var(--ink-700); }
    """)


def open_bulk_email() -> None:
    """Button handler: start a fresh send to the waiting priority guests."""
    st.session_state.pop("_bulk_done", None)
    bulk_email()


@st.dialog("Contact priority guests", width="medium")
def bulk_email() -> None:
    cands = repo.bulk_candidates()
    size = DEFAULT_BATCH
    if not st.session_state.get("_bulk_done"):
        size = st.segmented_control("How many guests", BATCH_SIZES, default=DEFAULT_BATCH, key="bulk_size",
                                    required=True, format_func=lambda n: f"{n} guests") or DEFAULT_BATCH
    w = len(cands)
    _dialog_body(cands, "bulk", size, [
        f"<b>{w:,}</b> priority guest{'s' if w != 1 else ''} waiting for an action, highest predicted CLV first",
        "Each guest gets the message that matches their recommended action:"])


def open_selected_email(rows: pd.DataFrame) -> None:
    """Button handler: contact the guests Marketing ticked on the Guest Action List."""
    st.session_state.pop("_bulk_done", None)
    st.session_state["_sel_batch"] = rows[["guest_id", "recommended_action"]].astype(str).to_dict("records")
    selected_email()


def _clear_ticks() -> None:
    """Done: untick the Guest Action List after a send."""
    for k in [k for k in st.session_state if str(k).startswith("ab_sel_")]:
        del st.session_state[k]
    st.session_state["ab_all"] = False


@st.dialog("Send recommended action", width="medium")
def selected_email() -> None:
    """Send each ticked guest the message that matches their recommended action, by email or SMS."""
    picked = pd.DataFrame(st.session_state.get("_sel_batch", []), columns=["guest_id", "recommended_action"])
    n = len(picked)
    _dialog_body(picked, "sel", None, [f"<b>{n}</b> guest{'s' if n != 1 else ''} selected:"], on_done=_clear_ticks)


def _send(batch: pd.DataFrame, recipients: dict[str, str], test_to: str | None, channel: str = "Email") -> dict:
    """Send one message per guest (emails over a single Gmail connection); every attempt is logged."""
    tally = {"sent": 0, "unlogged": 0}
    failed: list[tuple[str, str]] = []
    progress = st.progress(0.0, text="Connecting to Gmail…" if channel == "Email" else "Sending SMS…")

    def one(send, r) -> None:
        subject, texts = templates.messages(templates.template_for(r.recommended_action))
        to = test_to or recipients[r.guest_id]
        try:
            if channel == "Email":
                res = send(to, f"[Test · {r.guest_id}] {subject}" if test_to else subject, texts["Email"])
            else:
                res = messaging.send_sms(to, f"[Test {r.guest_id}] {texts['SMS']}" if test_to else texts["SMS"])
        except messaging.SendError as e:
            failed.append((r.guest_id, str(e)))
            tally["unlogged"] += not _log(r.guest_id, r.recommended_action, channel, "Failed", messaging.mask(to))
        else:
            tally["sent"] += 1
            tally["unlogged"] += not _log(r.guest_id, r.recommended_action, channel, "Completed",
                                          res.recipient_masked, res.provider_id)

    error = None
    try:
        if channel == "Email":
            with messaging.email_batch(HOTEL_NAME) as send:
                for i, r in enumerate(batch.itertuples(), 1):
                    one(send, r)
                    progress.progress(i / len(batch), text=f"Sent {i} of {len(batch)}…")
        else:
            for i, r in enumerate(batch.itertuples(), 1):
                one(None, r)
                progress.progress(i / len(batch), text=f"Sent {i} of {len(batch)}…")
    except messaging.SendError as e:     # Gmail login or connection failed: nothing more was sent
        error = str(e)
    return {"channel": channel, "test": bool(test_to), "sent": tally["sent"], "failed": failed,
            "error": error, "unlogged": tally["unlogged"]}


def _results(done: dict, on_done=None) -> None:
    channel = done.get("channel", "Email")
    if done["error"]:
        alert("error", done["error"])
    if done["sent"]:
        where = (" to your test inbox" if channel == "Email" else " to your test phone") if done["test"] else ""
        alert("success", f"{_noun(channel, done['sent'])} sent{where} and recorded in the Action Logs. "
                         "Priority guests among them have left the priority list.")
    if done["failed"]:
        alert("warning", f"{_noun(channel, len(done['failed']))} failed and were recorded as Failed: "
                         + "; ".join(f"{g} ({why})" for g, why in done["failed"][:5]))
    if done["unlogged"]:
        alert("warning", f"{done['unlogged']} send{'s' if done['unlogged'] != 1 else ''} could not be recorded "
                         "in the Action Logs.")
    if st.button("Done", type="primary", width="stretch", key="bulk_done", on_click=on_done):
        st.session_state.pop("_bulk_done", None)
        st.rerun()


# ---------------------------------------------------------------------------
# Follow-up reminders
# ---------------------------------------------------------------------------

def show_follow_ups() -> None:
    st.session_state["_ab_scroll"] = "card_followup"


def follow_up_banner(df: pd.DataFrame) -> None:
    """Banner at the top of Marketing's Action Board while outcomes are overdue."""
    if df.empty:
        return
    n, days = len(df), repo.follow_up_days()
    with st.container(key="fu_alert", horizontal=True, vertical_alignment="center", wrap=False):
        st.html(f"""
        <div class="mk-alert-body">
            <span class="fu-alert-ico"><i class="fa-solid fa-clock-rotate-left"></i></span>
            <div>
                <div class="fu-alert-title">{n:,} outcome{"s" if n != 1 else ""} waiting more than {days} days</div>
                <div class="mk-alert-text">Record whether these guests came back, or send a follow-up message.</div>
            </div>
        </div>""")
        st.space("stretch")
        st.button("Show outcomes", key="fu_alert_go", icon=":material/arrow_downward:", on_click=show_follow_ups)
    ui.css("""
    .st-key-fu_alert { background: var(--amber-50); border: 1px solid var(--amber-200); border-radius: var(--r-lg);
                       padding: 14px 18px !important; gap: 14px !important; }
    .fu-alert-ico { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; display: inline-flex;
                    align-items: center; justify-content: center; background: var(--surface);
                    color: var(--amber-700); border: 1px solid var(--amber-200); }
    .fu-alert-title { font-size: 1rem; font-weight: 600; color: var(--amber-700); }
    @media (max-width: 640px) { .st-key-fu_alert { flex-wrap: wrap !important; } }
    """)


FU_COLS = [("", 0.35), ("Guest ID", 1.1), ("Action", 2.0), ("Sent On", 1.1), ("Waiting", 0.9), ("Outcome", 1.6)]


def _sel_key(log_id: str) -> str:
    return f"fu_sel_{log_id}"


def _select_page(log_ids: list[str]) -> None:
    on = st.session_state["fu_all"]
    for i in log_ids:
        st.session_state[_sel_key(i)] = on


def _saved_toast(n: int, outcome: str) -> None:
    st.toast(f"{n} outcome{'s' if n != 1 else ''} recorded: {outcome}.", icon=":material/check_circle:")
    if outcome == "Came back":
        st.toast("Guests who came back were removed from the Priority list automatically.", icon=":material/flag:")


def _mark_selected(log_ids: list[str], outcome: str) -> None:
    """Record one outcome for every ticked row on this page."""
    chosen = [i for i in log_ids if st.session_state.get(_sel_key(i))]
    if not chosen:
        st.toast("Tick at least one guest first.", icon=":material/info:")
        return
    try:
        n = repo.set_outcomes(chosen, outcome)
    except (PermissionError, APIError):
        st.toast("The outcomes could not be saved. Please try again.", icon=":material/error:")
        return
    for i in chosen:
        st.session_state.pop(_sel_key(i), None)
    st.session_state["fu_all"] = False
    _saved_toast(n, outcome)


def _mark_one(log_id: str, key: str) -> None:
    """Outcome dropdown on a single row: saved straight away."""
    outcome = st.session_state[key]
    if outcome == "Waiting":
        return
    try:
        repo.set_outcome(log_id, outcome)
    except (PermissionError, APIError):
        st.toast("The outcome could not be saved. Please try again.", icon=":material/error:")
        return
    st.session_state.pop(_sel_key(log_id), None)
    _saved_toast(1, outcome)


def follow_up_card(df: pd.DataFrame) -> None:
    """Overdue outcomes for the Marketing Team, recorded one by one or many at once."""
    if df.empty:
        return
    days = repo.follow_up_days()
    with ui.card("followup"):
        ui.card_title("Outcomes to Record",
                      f"Actions waiting more than {days} days for a result, oldest first.", fa="clock-rotate-left")
        start, end = ui.paginate("fu", len(df))
        page = df.iloc[start:end]
        ids = page["log_id"].astype(str).tolist()

        with st.container(key="fu_bulk", horizontal=True, vertical_alignment="center"):
            st.checkbox("Select all on this page", key="fu_all", on_change=_select_page, args=(ids,))
            st.space("stretch")
            picked = sum(bool(st.session_state.get(_sel_key(i))) for i in ids)
            st.html(f'<span class="fu-count">{picked} selected</span>')
            st.button("Mark selected: Came back", key="fu_came", type="primary", icon=":material/check:",
                      on_click=_mark_selected, args=(ids, "Came back"))
            st.button("Mark selected: Didn't come back", key="fu_not", icon=":material/close:",
                      on_click=_mark_selected, args=(ids, "Didn't come back"))

        with st.container(key="tbl_fu", gap=None):
            with st.container(key="tblhead_fu"):
                head = st.columns([w for _, w in FU_COLS], gap="small", vertical_alignment="center")
                for cell, (label, _) in zip(head, FU_COLS):
                    cell.html(f'<span class="ds-th">{label}</span>')
            for n, r in enumerate(page.itertuples()):
                lid, gid, waited = str(r.log_id), str(r.guest_id), int(r.days_waiting)  # type: ignore[arg-type]
                with st.container(key=f"tblrow_fu_{n}"):
                    c = st.columns([w for _, w in FU_COLS], gap="small", vertical_alignment="center")
                    c[0].checkbox("Select", key=_sel_key(lid), label_visibility="collapsed")
                    with c[1], st.container(key=f"lnk_fu_{n}"):
                        if st.button(gid, key=f"fu_id_{lid}", type="tertiary"):
                            ui.view_guest(gid)
                    tag = (ui.pill("Control group", "amber") if r.action_status == repo.HELD_OUT
                           else f'<span class="gt-tag gt-tag-action">{ui.esc(r.action_taken)}</span>')
                    c[2].html(f'<span class="ds-td">{tag}</span>')
                    c[3].html(f'<span class="ds-td" style="color:var(--ink-500)">{r.logged_at:%d %b %Y}</span>')
                    c[4].html(f'<span class="ds-td">{ui.pill(f"{waited} days", "red" if waited > 2 * days else "amber")}</span>')
                    key = f"fu_out_{lid}"
                    with c[5]:
                        st.selectbox("Outcome", repo.OUTCOMES, key=key, label_visibility="collapsed",
                                     on_change=_mark_one, args=(lid, key))
        ui.pagination_bar("fu", len(df))
    ui.css("""
    .st-key-fu_bulk { gap: 10px !important; margin-bottom: 8px; flex-wrap: wrap !important; }
    .fu-count { font-size: 0.88rem; color: var(--ink-500); }
    """)
