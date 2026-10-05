"""Session-state defaults and the authenticated sidebar."""

import html
import json

import streamlit as st

import auth
from style import brand_lockup

HOTEL_NAME = "Grand Regency Hotel"


def init_session_state():
    auth.init_auth_state()


def role_label(role: str) -> str:
    return auth.ROLES.get(role, "")


def _initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def render_sidebar(nav_pages, current: str, counts: dict[str, int] | None = None):
    """Brand, role-filtered navigation, signed-in user and logout.

    current is the url_path of the page being shown; counts maps a url_path
    to a number shown as a badge on that nav item.
    """
    s = st.session_state
    counts = counts or {}
    with st.sidebar:
        st.html(brand_lockup("Revenue Management"))
        st.html('<div class="ds-nav-label">Navigation</div>')
        for page in nav_pages:
            key = ("navon_" if page.url_path == current else "nav_") + page.url_path
            with st.container(key=key):
                st.page_link(page, width="stretch")
            if page.url_path in counts:
                st.html(f"<style>.st-key-{key} a::after {{ content: "
                        f"{json.dumps(f'{counts[page.url_path]:,}')}; }}</style>")

        with st.container(key="sb_user"):
            st.html(f"""
            <div class="ds-user-card">
                <span class="ds-avatar">{_initials(s.full_name)}</span>
                <span class="ds-user-meta">
                    <div class="ds-user-name">{html.escape(s.full_name or "")}</div>
                    <div class="ds-user-role">{role_label(s.role)}</div>
                    <div class="ds-user-role">{HOTEL_NAME}</div>
                </span>
            </div>""")
            if st.button("Log out", icon=":material/logout:", width="stretch", key="sidebar_logout"):
                auth.logout()
                auth.set_flash("success", "You have been signed out.")
                st.switch_page(auth.LOGIN_PAGE)
