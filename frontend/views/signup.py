import streamlit as st

import auth
from style import alert, auth_page_chrome, brand_lockup, field_error, icon

auth_page_chrome()

form = auth.FormState("_signup_form")

def _clear(field: str) -> None:
    form.clear_field(field)


def _submit() -> None:
    s = st.session_state
    full_name = " ".join((s.get("su_name") or "").split())
    email = auth.normalize_email(s.get("su_email"))
    code = (s.get("su_token") or "").strip()
    password = s.get("su_password") or ""
    confirm = s.get("su_confirm") or ""

    # 1. Form-level validation — nothing is sent anywhere until this passes.
    errors = {}
    if len(full_name) < 2:
        errors["name"] = "Enter your full name."
    if not email:
        errors["email"] = "Enter your email address."
    elif not auth.is_valid_email(email):
        errors["email"] = "Enter a valid email address."
    if not code:
        errors["token"] = "Enter the invite code from your invitation email."
    if not all(ok for _, ok in auth.password_checks(password)):
        errors["password"] = "Password doesn't meet all the requirements."
    if not confirm:
        errors["confirm"] = "Re-enter your password."
    elif confirm != password:
        errors["confirm"] = "Passwords do not match."
    if errors:
        form.set(fields=errors)
        return

    problem = auth.config_error()
    if problem:
        form.set(form=problem)
        return

    # 2. The invite code must be the open invite for this email (single use, not expired).
    wait = auth.lockout_remaining("invite_token")
    if wait:
        mins = max(1, round(wait / 60))
        form.set(form=f"Too many invalid invite codes. Try again in about {mins} minute{'s' if mins > 1 else ''}.")
        return
    try:
        invite = auth.verify_invite(email, code)
    except Exception:
        form.set(form="We couldn't check your invite right now. Please try again.")
        return
    if invite is None:
        auth.record_failure("invite_token")
        form.set(fields={"token": "This code is not valid for this email, has been used, or has expired. "
                                  "Ask your system administrator for a new invitation."})
        return
    auth.clear_failures("invite_token")

    # 3. Supabase Auth → USERS table.
    try:
        needs_confirmation = auth.sign_up(full_name, email, password, invite)
    except auth.AuthFailure as err:
        if err.field:
            form.set(fields={err.field: err.message})
        else:
            form.set(form=err.message)
        return

    for key in ("su_password", "su_confirm", "su_token"):
        s[key] = ""
    form.reset()
    s["login_email"] = email
    if needs_confirmation:
        auth.set_flash("success", f"Account created. Confirm your email using the link sent to {email}, then sign in.")
    else:
        auth.set_flash("success", "Account created. Sign in to continue.")
    s["_signup_done"] = True


def _wrap(field: str) -> str:
    return ("err_" if form.field(field) else "ok_") + "su_" + field


if st.session_state.pop("_signup_done", False):
    st.switch_page(auth.LOGIN_PAGE)

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------

with st.container(key="auth_topbar", horizontal=True, vertical_alignment="center"):
    st.markdown(brand_lockup(), unsafe_allow_html=True)
    st.space("stretch")
    if st.button("Back to home", type="tertiary", icon=":material/arrow_back:", key="signup_home"):
        st.switch_page("views/home.py")

# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

with st.container(key="auth_card_wide"):
    st.markdown(
        f"""
        <div class="auth-head">
            <div class="auth-mark">{icon("user-plus")}</div>
            <div class="auth-title">Create your account</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if form.form():
        alert("error", form.form())

    with st.container(key=_wrap("name")):
        st.text_input("Full name", key="su_name", placeholder="e.g. Amina Wanjiru",
                      icon=":material/person:", autocomplete="name",
                      on_change=_clear, args=("name",))
        field_error(form.field("name"))

    with st.container(key=_wrap("email")):
        st.text_input("Email", key="su_email", type="email", validate="",
                      placeholder="name@hotel.com", on_change=_clear, args=("email",))
        field_error(form.field("email"))

    with st.container(key=_wrap("token")):
        st.text_input("Invite code", key="su_token", icon=":material/key:", placeholder="e.g. K7QX-M2PD-9TAZ",
                      autocomplete="off", on_change=_clear, args=("token",),
                      help="Your role comes from the invitation. Codes work once and expire after 7 days.")
        field_error(form.field("token"))

    @st.fragment
    def _password_fields() -> None:
        with st.container(key=_wrap("password")):
            password = st.text_input("Password", key="su_password", type="password",
                                     icon=":material/lock:", placeholder="Create a password",
                                     autocomplete="new-password", live=True,
                                     on_change=_clear, args=("password",))

            attempted = bool(form.field("password"))
            items = []
            for label, ok in auth.password_checks(password):
                state = "ok" if ok else ("bad" if attempted else "")
                glyph = "circle-check" if ok else ("circle-xmark" if attempted else "circle")
                items.append(f'<span class="{state}">{icon(glyph)}{label}</span>')
            st.markdown(f'<div class="pw-rules">{"".join(items)}</div>', unsafe_allow_html=True)

        with st.container(key=_wrap("confirm")):
            confirm = st.text_input("Confirm password", key="su_confirm", type="password",
                                    icon=":material/lock:", placeholder="Re-enter your password",
                                    autocomplete="new-password", live=True,
                                    on_change=_clear, args=("confirm",))
            if form.field("confirm"):
                field_error(form.field("confirm"))
            elif confirm and password and confirm != password:
                field_error("Passwords do not match.")

    _password_fields()

    st.button("Create account", type="primary", width="stretch", on_click=_submit, key="su_submit")

    st.markdown('<div class="auth-switch">Already have an account?</div>', unsafe_allow_html=True)
    if st.button("Sign in", width="stretch", key="signup_to_login"):
        form.reset()
        st.switch_page(auth.LOGIN_PAGE)

