"""
On-screen alerts telling the Marketing Team about guests the Revenue Manager sent them.

- Pop-up when they sign in, if priority guests are waiting for an action.
- Notice in the corner if new guests arrive while they are working (checked every minute).
- Banner on the Action Board and a count on the sidebar while guests are waiting.

Nothing is stored for the alerts themselves: a guest stops counting as soon as
Marketing logs an action for them.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import components as ui
from data import repository as repo

ACTION_BOARD = "views/action_board.py"
CHECK_EVERY = "60s"


def inbox() -> pd.DataFrame:
    """Waiting priority guests; empty if the data cannot be read (alerts must never break a page)."""
    try:
        return repo.marketing_inbox()
    except Exception:  # noqa: BLE001
        return pd.DataFrame(columns=repo.INBOX_COLUMNS)


def _latest(df: pd.DataFrame):
    return None if df.empty else df["decided_at"].max()


def _when(ts) -> str:
    return f"{ts:%d %b %Y, %H:%M}"


def show_priority() -> None:
    """Action Board filter → priority guests only, then scroll down to the Guest Action List."""
    st.session_state["ab_show"] = "Priority only"
    st.session_state["_ab_page"] = 1
    st.session_state["_ab_scroll"] = True


def scroll_to_list() -> None:
    """Scroll to the Guest Action List once, after "Show priority guests" was clicked."""
    if not st.session_state.pop("_ab_scroll", False):
        return
    n = st.session_state.get("_scroll_nonce", 0) + 1     # new content each time, so the script runs again
    st.session_state["_scroll_nonce"] = n
    st.html(f"""<script>/* {n} */
    // Waits until the page below the list has loaded (so there is room to scroll), up to 5 seconds.
    (function go(tries) {{
        const list = document.querySelector('.st-key-card_actions');
        const main = document.querySelector('[data-testid="stMain"]');
        if (list && main) {{
            const target = main.scrollTop + list.getBoundingClientRect().top - main.getBoundingClientRect().top - 16;
            if (main.scrollHeight - main.clientHeight >= target || tries >= 50) {{
                main.scrollTo({{top: target, behavior: 'smooth'}});
                // Some browsers skip smooth scrolling: jump there if it has not moved.
                setTimeout(() => {{ if (Math.abs(main.scrollTop - target) > 40) main.scrollTop = target; }}, 900);
                return;
            }}
        }}
        if (tries < 50) setTimeout(() => go(tries + 1), 100);
    }})(0);
    </script>""", unsafe_allow_javascript=True)


def _batches(df: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    """Sends grouped by minute and reason (one threshold change = one batch), newest first."""
    b = df.assign(minute=df["decided_at"].dt.floor("min"))
    return (b.groupby(["minute", "reason"]).size().rename("guests").reset_index()
            .sort_values("minute", ascending=False).head(limit))


@st.dialog("New priority guests", icon=":material/notifications_active:")
def _popup(df: pd.DataFrame) -> None:
    n = len(df)
    st.html(f'<p class="mk-pop-lead">The Revenue Manager has sent you <b>{n:,} priority '
            f'guest{"s" if n != 1 else ""}</b> who are waiting for an action.</p>')
    st.html("".join(
        f'<div class="mk-pop-row"><b>{r.guests:,} guest{"s" if r.guests != 1 else ""}</b>'
        f'<span>{_when(r.minute)}</span><p>{ui.esc(r.reason)}</p></div>'
        for r in _batches(df).itertuples()))
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Later", key="mk_pop_later"):
            st.rerun()
        if st.button("Show priority guests", type="primary", icon=":material/arrow_forward:", key="mk_pop_go"):
            show_priority()
            st.switch_page(ACTION_BOARD)


@st.fragment(run_every=CHECK_EVERY)
def _watch() -> None:
    """Corner notice when the Revenue Manager sends new guests while Marketing is signed in."""
    df = inbox()
    latest, seen = _latest(df), st.session_state.get("_mk_seen_at")
    if latest is not None and (seen is None or latest > seen):
        new = int((df["decided_at"] > seen).sum()) if seen is not None else len(df)
        st.session_state["_mk_seen_at"] = latest
        st.toast(f"**{new:,} new priority guest{'s' if new != 1 else ''}** from the Revenue Manager.",
                 icon=":material/notifications_active:", duration="infinite")


def marketing_alerts(df: pd.DataFrame) -> None:
    """Run on every Marketing page (from app.py)."""
    if not st.session_state.get("_mk_popup_done"):
        st.session_state["_mk_popup_done"] = True
        st.session_state["_mk_seen_at"] = _latest(df)
        if not df.empty:
            _popup(df)
    _watch()
    ui.css("""
    .mk-pop-lead { margin: 0 0 10px; font-size: 1rem; color: var(--ink-800); }
    .mk-pop-row { padding: 10px 12px; margin-bottom: 8px; border: 1px solid var(--navy-200);
                  border-radius: 8px; background: var(--navy-50); font-size: 0.9rem; color: var(--navy-700); }
    .mk-pop-row span { float: right; color: var(--ink-500); font-size: 0.82rem; }
    .mk-pop-row p { margin: 4px 0 0; color: var(--ink-500); font-size: 0.85rem; }
    """)


def action_board_banner(df: pd.DataFrame) -> None:
    """Banner at the top of Marketing's Action Board while priority guests are waiting."""
    if df.empty:
        return
    n = len(df)
    with st.container(key="mk_alert", horizontal=True, vertical_alignment="center", wrap=False):
        st.html(f"""
        <div class="mk-alert-body">
            <span class="mk-alert-ico"><i class="fa-solid fa-bell"></i></span>
            <div>
                <div class="mk-alert-title">{n:,} priority guest{"s" if n != 1 else ""} from the Revenue Manager
                    waiting for an action</div>
                <div class="mk-alert-text">Latest sent {_when(_latest(df))}. A guest leaves this list once you
                    log an action for them.</div>
            </div>
        </div>""")
        st.space("stretch")
        st.button("Show priority guests", key="mk_alert_go", type="primary", icon=":material/filter_list:",
                  on_click=show_priority)
    ui.css("""
    .st-key-mk_alert { background: var(--navy-50); border: 1px solid var(--navy-200); border-radius: var(--r-lg);
                       padding: 14px 18px !important; gap: 14px !important; }
    .mk-alert-body { display: flex; align-items: center; gap: 12px; }
    .mk-alert-ico { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; display: inline-flex;
                    align-items: center; justify-content: center; background: var(--surface);
                    color: var(--navy-700); border: 1px solid var(--navy-200); }
    .mk-alert-title { font-size: 1rem; font-weight: 600; color: var(--navy-700); }
    .mk-alert-text { margin-top: 2px; font-size: 0.86rem; color: var(--ink-500); }
    @media (max-width: 640px) { .st-key-mk_alert { flex-wrap: wrap !important; } }
    """)
