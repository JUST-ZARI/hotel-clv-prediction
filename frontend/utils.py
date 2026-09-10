"""Shared session-state defaults and sidebar branding used across pages."""

import streamlit as st

HOTEL_NAME = "Grand Regency Hotel"


def init_session_state():
    defaults = {
        "authenticated": False,
        "role": None,          # "revenue_manager" or "marketing"
        "setup_complete": False,
        "accounts_created": {"revenue_manager": False, "marketing": False},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def role_label(role: str) -> str:
    return "Revenue Manager" if role == "revenue_manager" else "Marketing Team"


def render_sidebar_footer():
    """User identity block pinned at the bottom of the sidebar, matching the wireframes."""
    st.sidebar.markdown("---")
    with st.sidebar:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("🧑")
        with col2:
            st.markdown(f"**{role_label(st.session_state.role)}**")
            st.caption(HOTEL_NAME)


def render_top_role_badge():
    """Small role pill shown top-right on every authenticated page."""
    st.markdown(
        f"""
        <div style="text-align:right;">
            <span style="background:#eef2ff;color:#3b4ee0;padding:4px 12px;
            border-radius:6px;font-size:0.85em;font-weight:600;">
                Role: {role_label(st.session_state.role)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_status_badges():
    from data.dummy_guests import DASHBOARD_STATS
    col1, col2 = st.columns([1, 1])
    with col1:
        st.caption(f"🕒 Model updated: {DASHBOARD_STATS['model_updated']}")
    with col2:
        st.success(f"⚡ {DASHBOARD_STATS['active_model']} Active", icon="⚡")


def logout_button():
    if st.sidebar.button("Log out"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.rerun()
