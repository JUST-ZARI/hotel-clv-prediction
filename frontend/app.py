import streamlit as st
from utils import init_session_state

st.set_page_config(page_title="Hotel CLV Dashboard", page_icon="🏨", layout="wide")
init_session_state()

# --- Define every page once ---
setup_page = st.Page("views/setup.py", title="Setup", icon=":material/settings:")
login_page = st.Page("views/login.py", title="Login", icon=":material/login:")

action_board_page = st.Page("views/action_board.py", title="Action Board",
                             icon=":material/dashboard:", default=True)
guest_lookup_page = st.Page("views/guest_lookup.py", title="Guest Lookup",
                             icon=":material/search:")
segments_page = st.Page("views/segments.py", title="Segments",
                         icon=":material/pie_chart:")
at_risk_page = st.Page("views/at_risk_guests.py", title="At-Risk Guests",
                        icon=":material/warning:")
model_performance_page = st.Page("views/model_performance.py", title="Model Performance",
                                  icon=":material/bar_chart:")

# --- Decide which pages are reachable, based on session state ---
# One-time setup screen shows until both role accounts exist (matches the wireframe's
# "1 of 2 accounts created" flow). Skip this gate in dummy-data mode by flipping
# setup_complete to True in utils.init_session_state() once real Supabase auth lands.
if not st.session_state.setup_complete:
    pages = [setup_page]
elif not st.session_state.authenticated:
    pages = [login_page]
else:
    # Both roles see the same 5 pages (matches wireframes) — role differences are
    # in-page: column sets, presence of $ figures, CSV export, and the action panel.
    pages = [action_board_page, guest_lookup_page, segments_page,
             at_risk_page, model_performance_page]

pg = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.markdown("### 🏨 CLV Dashboard")
    st.caption("Revenue Management")

pg.run()
