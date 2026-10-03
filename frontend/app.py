import streamlit as st

import auth
from data import repository as repo
from style import inject_global_css
from utils import init_session_state, render_sidebar

st.set_page_config(page_title="Hotel CLV", page_icon=":material/apartment:", layout="wide",
                   initial_sidebar_state=240)
init_session_state()
inject_global_css()

RM, MK = "revenue_manager", "marketing"

# --- Public pages ---
home_page = st.Page("views/home.py", title="Home", url_path="home", default=True)
login_page = st.Page(auth.LOGIN_PAGE, title="Sign in", url_path="login")
signup_page = st.Page(auth.SIGNUP_PAGE, title="Create account", url_path="signup")
PUBLIC_PAGES = [home_page, login_page, signup_page]

# --- Protected pages → roles allowed to open them ---
# Both roles share the four dashboard pages (per the wireframes); what each
# role sees inside a page is decided in the page. Restrict a whole page by
# removing a role from its set here.
PROTECTED_PAGES = {
    st.Page("views/action_board.py", title="Action Board", icon=":material/space_dashboard:",
            url_path="action-board"): {RM, MK},
    st.Page("views/guest_lookup.py", title="Guest Lookup", icon=":material/person_search:",
            url_path="guest-lookup"): {RM, MK},
    st.Page("views/segments.py", title="Segments", icon=":material/donut_small:",
            url_path="segments"): {RM, MK},
    st.Page("views/at_risk_guests.py", title="At-Risk Guests", icon=":material/warning:",
            url_path="at-risk"): {RM, MK},
}

# Every page is registered so direct URLs resolve and can be guarded;
# the visible menu is rendered by render_sidebar() from the allowed set.
pg = st.navigation(PUBLIC_PAGES + list(PROTECTED_PAGES), position="hidden")

role = auth.current_role()
allowed = [p for p, roles in PROTECTED_PAGES.items() if role in roles]

if pg.url_path in {p.url_path for p in PUBLIC_PAGES}:
    # Signed-in users skip the landing/auth screens.
    if auth.is_logged_in():
        st.switch_page(allowed[0])
else:
    if not auth.is_logged_in():
        auth.set_flash("info", "Please sign in to continue.")
        st.switch_page(login_page)
    if not auth.session_valid():
        auth.logout(revoke=False)
        auth.set_flash("info", "Your session has expired. Please sign in again.")
        st.switch_page(login_page)
    if pg.url_path not in {p.url_path for p in allowed}:
        st.switch_page(allowed[0])
    render_sidebar(allowed, current=pg.url_path, counts={"at-risk": repo.overview()["at_risk_high_value"]})

pg.run()
