"""
Marketing Team tools on the Action Board:

- Bulk email: email the waiting priority guests in one go (5, 10, 25 or 50 at a time, within
  the daily limit). Each guest gets the template that matches their recommended action.
  With test_recipient set under [messaging] in secrets, every email goes to that address
  instead (test mode), with the Guest ID in the subject.
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


def _log(guest_id: str, action: str, status: str, masked: str | None, provider_id: str | None = None) -> bool:
    try:
        repo.log_action(guest_id, action, "Email", status, masked, provider_id)
        return True
    except APIError:
        return False


def open_bulk_email() -> None:
    """Button handler: start a fresh bulk send."""
    st.session_state.pop("_bulk_done", None)
    bulk_email()


@st.dialog("Email priority guests", width="medium")
def bulk_email() -> None:
    done = st.session_state.get("_bulk_done")
    if done:
        _results(done)
        return

    form = st.empty()     # replaced by the results once the emails are sent
    with form.container():
        cands = repo.bulk_candidates()
        test_to = messaging.test_recipient()
        limit = messaging.daily_limit()
        left = max(0, limit - repo.sends_last_24h())
        size = st.segmented_control("How many guests", BATCH_SIZES, default=DEFAULT_BATCH, key="bulk_size",
                                    required=True, format_func=lambda n: f"{n} guests")
        emails: dict[str, str] = {}
        skipped = 0
        if not test_to:
            emails = repo.guest_emails(cands["guest_id"].tolist())
            ok = cands["guest_id"].map(lambda g: _valid_email(emails.get(g)))
            skipped = int((~ok).sum())
            cands = cands[ok]
        batch = cands.head(min(size or DEFAULT_BATCH, left))

        st.html(f"""<ul class="bk-list">
            <li><b>{len(cands):,}</b> priority guest{"s" if len(cands) != 1 else ""} waiting for an action</li>
            <li><b>{left}</b> of {limit} emails left today (daily limit)</li>
            <li>This batch: <b>{len(batch)}</b> guest{"s" if len(batch) != 1 else ""}, highest predicted CLV first,
                each with the template that matches their recommended action</li></ul>""")
        if test_to:
            alert("info", f"Test mode: every email goes to {messaging.mask(test_to)} instead of the guest, "
                          "with the Guest ID in the subject.")
        elif skipped:
            alert("warning", f"{skipped} guest{'s' if skipped != 1 else ''} with demo addresses (@example.com) "
                             "cannot receive email and will be skipped. Add test_recipient under [messaging] in "
                             "secrets to test with your own inbox.")
        if not messaging.email_ready():
            alert("warning", "Email is not set up: add gmail_address and gmail_app_password under [messaging] in secrets.")
        elif left == 0:
            alert("warning", "Daily limit reached. Try again later, or raise daily_limit under [messaging] in secrets.")
        elif len(batch) < min(size or DEFAULT_BATCH, len(cands)):
            ui.note(f"Only {left} sends are left today. Raise daily_limit under [messaging] in secrets to send more.")

        if not batch.empty:
            first = batch.iloc[0]
            subject, texts = templates.messages(templates.template_for(first["recommended_action"]))
            with st.expander(f"Preview: email to {first['guest_id']}", icon=":material/mail:"):
                st.html(f"<p class='bk-subj'><b>Subject:</b> {ui.esc(subject)}</p>"
                        f"<pre class='bk-body'>{ui.esc(texts['Email'])}</pre>")

        n = len(batch)
        if st.button(f"Send {n} email{'s' if n != 1 else ''}", type="primary", width="stretch",
                     icon=":material/send:", key="bulk_send", disabled=n == 0 or not messaging.email_ready()):
            st.session_state["_bulk_done"] = _send(batch, emails, test_to)

    if st.session_state.get("_bulk_done"):
        form.empty()
        _results(st.session_state["_bulk_done"])

    ui.css("""
    .bk-list { margin: 0 0 6px; padding-left: 18px; font-size: 0.92rem; color: var(--ink-800); line-height: 1.7; }
    .bk-subj { margin: 0 0 6px; font-size: 0.9rem; }
    .bk-body { white-space: pre-wrap; font-family: inherit; font-size: 0.85rem; margin: 0; color: var(--ink-700); }
    """)


def _send(batch: pd.DataFrame, emails: dict[str, str], test_to: str | None) -> dict:
    """Send one email per guest over a single Gmail connection; every attempt is logged."""
    sent, failed, unlogged = 0, [], 0
    progress = st.progress(0.0, text="Connecting to Gmail…")
    try:
        with messaging.email_batch(HOTEL_NAME) as send:
            for i, r in enumerate(batch.itertuples(), 1):
                subject, texts = templates.messages(templates.template_for(r.recommended_action))
                to = test_to or emails[r.guest_id]
                if test_to:
                    subject = f"[Test · {r.guest_id}] {subject}"
                try:
                    res = send(to, subject, texts["Email"])
                except messaging.SendError as e:
                    failed.append((r.guest_id, str(e)))
                    unlogged += not _log(r.guest_id, r.recommended_action, "Failed", messaging.mask(to))
                else:
                    sent += 1
                    unlogged += not _log(r.guest_id, r.recommended_action, "Completed", res.recipient_masked,
                                         res.provider_id)
                progress.progress(i / len(batch), text=f"Sent {i} of {len(batch)}…")
    except messaging.SendError as e:     # Gmail login or connection failed: nothing was sent
        return {"sent": sent, "failed": failed, "error": str(e), "unlogged": unlogged, "test": bool(test_to)}
    return {"sent": sent, "failed": failed, "error": None, "unlogged": unlogged, "test": bool(test_to)}


def _results(done: dict) -> None:
    if done["error"]:
        alert("error", done["error"])
    if done["sent"]:
        where = " to your test inbox" if done["test"] else ""
        alert("success", f"{done['sent']} email{'s' if done['sent'] != 1 else ''} sent{where} and recorded in "
                         "the Action Logs. These guests have left the priority list.")
    if done["failed"]:
        alert("warning", f"{len(done['failed'])} email{'s' if len(done['failed']) != 1 else ''} failed and "
                         "were recorded as Failed: " + "; ".join(f"{g} ({why})" for g, why in done["failed"][:5]))
    if done["unlogged"]:
        alert("warning", f"{done['unlogged']} send{'s' if done['unlogged'] != 1 else ''} could not be recorded "
                         "in the Action Logs.")
    if st.button("Done", type="primary", width="stretch", key="bulk_done"):
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


def follow_up_card(df: pd.DataFrame) -> None:
    """List of overdue outcomes for the Marketing Team (shown only when there are some)."""
    if df.empty:
        return
    days = repo.follow_up_days()
    with ui.card("followup"):
        ui.card_title("Outcomes to Record",
                      f"Actions waiting more than {days} days for a result, oldest first. Open a guest to record "
                      "whether they came back, or send a follow-up message.", fa="clock-rotate-left")
        start, end = ui.paginate("fu", len(df))
        ui.data_table("fu", df.iloc[start:end], [
            ui.Col("Guest ID", 1.1, kind="guest_link"),
            ui.Col("Action", 2.0, lambda r: f'<span class="gt-tag gt-tag-action">{ui.esc(r["action_taken"])}</span>'),
            ui.Col("Sent On", 1.3, lambda r: f'{r["logged_at"]:%d %b %Y}'),
            ui.Col("Waiting", 1.0, lambda r: ui.pill(f'{r["days_waiting"]} days',
                                                     "red" if r["days_waiting"] > 2 * days else "amber")),
            ui.Col("", 1.0, kind="view_button"),
        ], empty="No outcomes are overdue.")
        ui.pagination_bar("fu", len(df))
