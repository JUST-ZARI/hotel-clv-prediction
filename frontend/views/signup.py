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
    role = s.get("su_role")
    token = (s.get("su_token") or "").strip()
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
    if role not in auth.ROLES:
        errors["role"] = "Select your team."
    if not token:
        errors["token"] = "Enter the invite token you were given."
    if not all(ok for _, ok in auth.password_checks(password)):
        errors["password"] = "Password doesn't meet all the requirements."
    if not confirm:
        errors["confirm"] = "Re-enter your password."
    elif confirm != password:
        errors["confirm"] = "Passwords do not match."
    if errors:
        form.set(fields=errors)
        return

    problem = auth.config_error(for_signup=True)
    if problem:
        form.set(form=problem)
        return

    # 2. Invite token must belong to the selected role.
    wait = auth.lockout_remaining("invite_token")
    if wait:
        mins = max(1, round(wait / 60))
        form.set(form=f"Too many invalid invite tokens. Try again in about {mins} minute{'s' if mins > 1 else ''}.")
        return
    if not auth.verify_invite_token(role, token):
        auth.record_failure("invite_token")
        form.set(fields={"token": f"This invite token is not valid for {auth.ROLES[role]}."})
        return
    auth.clear_failures("invite_token")

    # 3. Supabase Auth → USERS table.
    try:
        needs_confirmation = auth.sign_up(full_name, email, password, role)
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
            <div class="auth-sub"> Use the token issued to your team for registration.</div>
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

    col_role, col_token = st.columns(2, gap="small")
    with col_role, st.container(key=_wrap("role")):
        st.selectbox("Team", options=list(auth.ROLES), format_func=auth.ROLES.get,
                     index=None, placeholder="Select your team", key="su_role",
                     on_change=_clear, args=("role",))
        field_error(form.field("role"))
    with col_token, st.container(key=_wrap("token")):
        st.text_input("Invite token", key="su_token", type="password",
                      icon=":material/key:", placeholder="Paste token",
                      autocomplete="off", on_change=_clear, args=("token",))
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

st.markdown(
    f'<div class="auth-foot">{icon("shield-halved")}'
    "Invite tokens are issued per team.</div>",
    unsafe_allow_html=True,
)
