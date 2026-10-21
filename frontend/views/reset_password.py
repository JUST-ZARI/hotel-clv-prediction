import streamlit as st

import auth
from style import alert, auth_page_chrome, brand_lockup, field_error, icon

auth_page_chrome()

form = auth.FormState("_reset_form")
s = st.session_state


def _clear(field: str) -> None:
    form.clear_field(field)


def _send_code() -> None:
    email = auth.normalize_email(s.get("rp_email"))
    if not auth.is_valid_email(email):
        form.set(fields={"email": "Enter a valid email address."})
        return
    try:
        auth.request_password_reset(email)
    except auth.AuthFailure as err:
        form.set(form=err.message)
        return
    form.reset()
    s["_rp_sent_to"] = email


def _reset() -> None:
    email = s.get("_rp_sent_to") or ""
    code = (s.get("rp_code") or "").strip()
    password = s.get("rp_password") or ""
    errors = {}
    if not (code.isdigit() and len(code) == 6):
        errors["code"] = "Enter the 6-digit code from the email."
    if not all(ok for _, ok in auth.password_checks(password)):
        errors["password"] = "Password doesn't meet all the requirements."
    if (s.get("rp_confirm") or "") != password:
        errors["confirm"] = "Passwords do not match."
    if errors:
        form.set(fields=errors)
        return
    wait = auth.lockout_remaining("reset")
    if wait:
        form.set(form=f"Too many wrong codes. Try again in about {max(1, round(wait / 60))} minute(s).")
        return
    try:
        auth.complete_password_reset(email, code, password)
    except auth.AuthFailure as err:
        auth.record_failure("reset")
        form.set(fields={err.field: err.message} if err.field else None, form=None if err.field else err.message)
        return
    auth.clear_failures("reset")
    form.reset()
    for key in ("rp_code", "rp_password", "rp_confirm", "_rp_sent_to"):
        s.pop(key, None)
    s["login_email"] = email
    auth.set_flash("success", "Password changed. Sign in with your new password.")
    s["_rp_done"] = True


def _wrap(field: str) -> str:
    return ("err_" if form.field(field) else "ok_") + "rp_" + field


if s.pop("_rp_done", False):
    st.switch_page(auth.LOGIN_PAGE)

with st.container(key="auth_topbar", horizontal=True, vertical_alignment="center"):
    st.markdown(brand_lockup(), unsafe_allow_html=True)
    st.space("stretch")
    if st.button("Back to login", type="tertiary", icon=":material/arrow_back:", key="rp_back"):
        form.reset()
        s.pop("_rp_sent_to", None)
        st.switch_page(auth.LOGIN_PAGE)

with st.container(key="auth_card"):
    sent_to = s.get("_rp_sent_to")
    st.markdown(f"""
        <div class="auth-head">
            <div class="auth-mark">{icon("key")}</div>
            <div class="auth-title">Reset password</div>
            <div class="auth-sub">{"Enter the code we emailed you and choose a new password." if sent_to
                                   else "We will email you a 6-digit code to reset your password."}</div>
        </div>""", unsafe_allow_html=True)

    if form.form():
        alert("error", form.form())

    if not sent_to:
        with st.container(key=_wrap("email")):
            st.text_input("Email address", key="rp_email", type="email", placeholder="name@hotel.com",
                          on_change=_clear, args=("email",))
            field_error(form.field("email"))
        st.button("Send reset code", type="primary", width="stretch", on_click=_send_code, key="rp_send")
    else:
        alert("info", auth.GENERIC_RESET_MESSAGE)
        with st.container(key=_wrap("code")):
            st.text_input("6-digit code", key="rp_code", max_chars=6, icon=":material/pin:",
                          on_change=_clear, args=("code",))
            field_error(form.field("code"))
        with st.container(key=_wrap("password")):
            st.text_input("New password", key="rp_password", type="password", icon=":material/lock:",
                          autocomplete="new-password", on_change=_clear, args=("password",))
            field_error(form.field("password"))
            st.caption("At least 8 characters, with an uppercase letter, a number and a special character.")
        with st.container(key=_wrap("confirm")):
            st.text_input("Confirm new password", key="rp_confirm", type="password", icon=":material/lock:",
                          autocomplete="new-password", on_change=_clear, args=("confirm",))
            field_error(form.field("confirm"))
        st.button("Change password", type="primary", width="stretch", on_click=_reset, key="rp_submit")
        if st.button("Use a different email", type="tertiary", key="rp_restart"):
            s.pop("_rp_sent_to", None)
            form.reset()
            st.rerun()

st.markdown(f'<div class="auth-foot">{icon("lock")}Codes expire after 15 minutes and work once.</div>',
            unsafe_allow_html=True)
