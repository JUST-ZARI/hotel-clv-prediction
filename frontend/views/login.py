import streamlit as st

import auth
from style import alert, auth_page_chrome, brand_lockup, field_error, icon

auth_page_chrome()

form = auth.FormState("_login_form")


def _submit() -> None:
    email = auth.normalize_email(st.session_state.get("login_email", ""))
    password = st.session_state.get("login_password", "")

    errors = {}
    if not email:
        errors["email"] = "Enter your email address."
    elif not auth.is_valid_email(email):
        errors["email"] = "Enter a valid email address."
    if not password:
        errors["password"] = "Enter your password."
    if errors:
        form.set(fields=errors)
        return

    wait = auth.lockout_remaining("login")
    if wait:
        form.set(form=f"Too many failed attempts. Try again in {wait} seconds.")
        return

    problem = auth.config_error()
    if problem:
        form.set(form=problem)
        return

    try:
        profile, client = auth.sign_in(email, password)
    except auth.AuthFailure as err:
        auth.record_failure("login")
        form.set(form=err.message)
        st.session_state["login_password"] = ""
        return

    auth.clear_failures("login")
    form.reset()
    auth.start_session(profile, client)


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------

with st.container(key="auth_topbar", horizontal=True, vertical_alignment="center"):
    st.markdown(brand_lockup(), unsafe_allow_html=True)
    st.space("stretch")
    if st.button("Back to home", type="tertiary", icon=":material/arrow_back:", key="login_home"):
        st.switch_page("views/home.py")

# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

with st.container(key="auth_card"):
    st.markdown(
        f"""
        <div class="auth-head">
            <div class="auth-mark">{icon("right-to-bracket")}</div>
            <div class="auth-title">Login</div>
            <div class="auth-sub">Access guest value predictions, segments and recommended actions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    flash = auth.pop_flash()
    if flash:
        alert(*flash)

    if form.form():
        alert("error", form.form())

    with st.form("login_form", border=False, enter_to_submit=True):
        with st.container(key=("err_" if form.field("email") else "ok_") + "login_email"):
            st.text_input("Email address", key="login_email", type="email",
                          placeholder="name@hotel.com")
            field_error(form.field("email"))

        with st.container(key=("err_" if form.field("password") else "ok_") + "login_password"):
            st.text_input("Password", key="login_password", type="password",
                          icon=":material/lock:", placeholder="Enter your password",
                          autocomplete="current-password")
            field_error(form.field("password"))

        st.form_submit_button("Login", type="primary", width="stretch", on_click=_submit)

    st.markdown('<div class="auth-switch">New to Hotel CLV?</div>', unsafe_allow_html=True)
    if st.button("Create an account", width="stretch", key="login_to_signup"):
        form.reset()
        st.switch_page(auth.SIGNUP_PAGE)

st.markdown(
    f'<div class="auth-foot">{icon("lock")}'
    "Authorised hotel staff only</div>",
    unsafe_allow_html=True,
)

# Signed in by the form callback → app.py routes to the role's dashboard.
if auth.is_logged_in():
    st.rerun()
