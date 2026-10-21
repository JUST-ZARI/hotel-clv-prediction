"""
auth.py — Supabase authentication, per-person invites, password reset and role-based session state.

Signup:  invite code (single use, 7 days, tied to one email) → password rules → Supabase Auth → USERS row
Login:   Supabase Auth → USERS row (role, is_active) → st.session_state
Reset:   6-digit code emailed to the user (15 minutes, single use) → new password
Admin:   creates invites, changes roles, deactivates leavers (see views/admin.py)

Required secrets (see .streamlit/secrets.example.toml):
    [supabase]  url, publishable_key|anon_key, secret_key|service_role_key
    [messaging] gmail_address, gmail_app_password   (invite and reset emails)
"""

from __future__ import annotations

import base64
import functools
import hashlib
import hmac
import secrets
from contextlib import suppress
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import streamlit as st

ROLES = {
    "revenue_manager": "Revenue Manager",
    "marketing": "Marketing Team",
    "admin": "System Administrator",
}
STAFF_ROLES = {"revenue_manager", "marketing"}   # hotel staff who use the guest dashboards
INVITE_DAYS = 7
RESET_MINUTES = 15

LOGIN_PAGE = "views/login.py"
SIGNUP_PAGE = "views/signup.py"
RESET_PAGE = "views/reset_password.py"

_SESSION_DEFAULTS = {
    "logged_in": False,
    "user_id": None,
    "email": None,
    "full_name": None,
    "role": None,
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Supabase session handling: one client per signed-in user lives in
# st.session_state (never shared between users). get_session() refreshes the
# access token when it is about to expire; get_user() re-verifies the user with
# the Auth server every VERIFY_EVERY seconds.
_CLIENT_KEY = "_sb_client"
_VERIFIED_AT_KEY = "_sb_verified_at"
VERIFY_EVERY = 300

# Failed-attempt limits per browser session (Supabase applies its own IP limits too).
_LIMITS = {
    "login": (5, 60),         # 5 failures → wait 60 s
    "invite_token": (5, 300), # 5 wrong invite codes → wait 5 min
    "reset": (5, 300),        # 5 wrong reset codes → wait 5 min
}


log = logging.getLogger(__name__)


class AuthFailure(Exception):
    """User-facing authentication error. `field` points the message at an input."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


# =====================================================================
# Configuration & clients
# =====================================================================

# Accept Supabase's current key names and the legacy JWT ones.
_PUBLIC_KEY_NAMES = ("publishable_key", "anon_key")      # sb_publishable_… or legacy anon JWT
_SERVER_KEY_NAMES = ("secret_key", "service_role_key")   # sb_secret_… or legacy service_role JWT


def _is_placeholder(value: str) -> bool:
    """Template values copied from secrets.example.toml."""
    return "YOUR-" in value or "CHANGE-ME" in value


def _secret(names: tuple[str, ...]) -> str:
    """First configured, non-placeholder value among `names`."""
    sb = st.secrets.get("supabase", {})
    values = (str(sb.get(n) or "").strip() for n in names)
    return next((v for v in values if v and not _is_placeholder(v)), "")


def _jwt_role(key: str) -> str | None:
    """Role claim of a legacy Supabase JWT key (None for non-JWT keys)."""
    if key.count(".") != 2:
        return None
    try:
        payload = key.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role")
    except (ValueError, UnicodeDecodeError):
        return None


def _is_public_key(key: str) -> bool:
    return key.startswith("sb_publishable_") or _jwt_role(key) == "anon"


def _is_server_key(key: str) -> bool:
    return key.startswith("sb_secret_") or _jwt_role(key) == "service_role"


def config_error(for_signup: bool = False) -> str | None:
    """Return a setup message if the Supabase secrets are missing or misplaced."""
    try:
        url = str(st.secrets["supabase"].get("url", "")).strip()
    except (KeyError, FileNotFoundError):
        return "Supabase is not configured. Add .streamlit/secrets.toml (see secrets.example.toml)."
    public, server = _secret(_PUBLIC_KEY_NAMES), _secret(_SERVER_KEY_NAMES)
    missing = [] if url else ["supabase.url"]
    missing += [] if public else ["supabase.publishable_key (or anon_key)"]
    missing += [] if server else ["supabase.secret_key (or service_role_key)"]
    if missing:
        return "Missing secrets: " + ", ".join(missing) + "."
    if not url.startswith("https://"):
        return "supabase.url must be your project URL, e.g. https://<project-ref>.supabase.co."
    if not _is_public_key(public):
        return "The public Supabase key must be the publishable (sb_publishable_…) or anon key."
    if not _is_server_key(server):
        return ("The server Supabase key must be the secret (sb_secret_…) or service_role key — "
                "a public key in that slot would let the app write rows it shouldn't.")
    return None


def _client_options():
    from supabase import ClientOptions

    # Streamlit serves many users from one process: never let a client
    # hold or refresh a user session between calls.
    return ClientOptions(auto_refresh_token=False, persist_session=False)


def _anon_client():
    """Fresh client per auth call so one user's session can't leak to another."""
    from supabase import create_client

    return create_client(st.secrets["supabase"]["url"], _secret(_PUBLIC_KEY_NAMES), options=_client_options())


@st.cache_resource(show_spinner=False)
def _service_client():
    """Server-side admin client. Only used for USERS writes and admin cleanup."""
    from supabase import create_client

    return create_client(st.secrets["supabase"]["url"], _secret(_SERVER_KEY_NAMES), options=_client_options())


# =====================================================================
# Validation
# =====================================================================

PASSWORD_RULES = [
    ("length", "At least 8 characters", lambda p: len(p) >= 8),
    ("upper", "One uppercase letter", lambda p: any(c.isupper() for c in p)),
    ("number", "One number", lambda p: any(c.isdigit() for c in p)),
    ("special", "One special character", lambda p: any(not c.isalnum() and not c.isspace() for c in p)),
]


def password_checks(password: str) -> list[tuple[str, bool]]:
    """[(rule label, passed), ...] for the live checklist."""
    return [(label, check(password or "")) for _, label, check in PASSWORD_RULES]


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email or ""))


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def app_url() -> str:
    """Public address of the dashboard, used in invite and confirmation emails."""
    return str(st.secrets.get("app", {}).get("base_url") or "http://localhost:8502").rstrip("/")


def _hash(code: str) -> str:
    return hashlib.sha256((code or "").strip().upper().encode()).hexdigest()


_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no 0/O or 1/I confusion


def new_invite_code() -> str:
    """Random code like K7QX-M2PD-9TAZ (about 60 bits)."""
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(12))
    return "-".join(raw[i:i + 4] for i in range(0, 12, 4))


def _open_invite(email: str) -> dict | None:
    """The unused, unrevoked, unexpired invite for this email (server key)."""
    rows = (_service_client().table("invites").select("*").eq("email", normalize_email(email))
            .is_("used_at", "null").is_("revoked_at", "null")
            .gt("expires_at", datetime.now(timezone.utc).isoformat()).limit(1).execute().data)
    return rows[0] if rows else None


def verify_invite(email: str, code: str) -> dict | None:
    """The invite if `code` is the open invite code for `email`, else None."""
    invite = _open_invite(email)
    if not invite or not (code or "").strip():
        return None
    return invite if hmac.compare_digest(_hash(code), invite["code_hash"]) else None


# =====================================================================
# Attempt throttling
# =====================================================================

def _failures(kind: str) -> list[float]:
    store = st.session_state.setdefault("_auth_failures", {})
    _, window = _LIMITS[kind]
    now = time.time()
    store[kind] = [t for t in store.get(kind, []) if now - t < window]
    return store[kind]


def lockout_remaining(kind: str) -> int:
    """Seconds until another attempt is allowed (0 = allowed)."""
    limit, window = _LIMITS[kind]
    recent = _failures(kind)
    if len(recent) < limit:
        return 0
    return max(1, int(window - (time.time() - recent[0])))


def record_failure(kind: str) -> None:
    _failures(kind).append(time.time())


def clear_failures(kind: str) -> None:
    st.session_state.setdefault("_auth_failures", {}).pop(kind, None)


# =====================================================================
# Supabase operations
# =====================================================================

def _service_boundary(action: str):
    """Turn unexpected errors (network, config, Supabase outages) into AuthFailure."""
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except AuthFailure:
                raise
            except Exception:
                log.exception("%s failed", action)
                raise AuthFailure(
                    f"We couldn't reach the authentication service to {action}. "
                    "Check your connection and try again."
                )
        return inner
    return wrap


def _is_rate_limited(err) -> bool:
    return getattr(err, "code", None) in ("over_request_rate_limit", "over_email_send_rate_limit") \
        or getattr(err, "status", None) == 429


@_service_boundary("create your account")
def sign_up(full_name: str, email: str, password: str, invite: dict) -> bool:
    """Create the Supabase Auth user and its USERS row with the invite's role, then use up the invite.

    Returns True if Supabase requires email confirmation before first login.
    Raises AuthFailure with a user-facing message on any error.
    """
    from supabase_auth.errors import AuthApiError, AuthError

    email = normalize_email(email)
    admin = _service_client()

    existing = admin.table("users").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        raise AuthFailure("This email is already registered. Sign in instead.", field="email")

    # A login left behind when a profile was deleted (no USERS row). The valid invite
    # proves this person may have the account, so reuse that login with the new password.
    orphan = _auth_user_by_email(email)
    if orphan is not None:
        admin.auth.admin.update_user_by_id(orphan.id, {
            "password": password, "email_confirm": True, "ban_duration": "none",
            "user_metadata": {"full_name": full_name}})
        _create_profile(admin, orphan.id, email, full_name, invite)
        return False

    try:
        res = _anon_client().auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}, "email_redirect_to": f"{app_url()}/login"},
        })
    except AuthApiError as err:
        if err.code in ("user_already_exists", "email_exists"):
            raise AuthFailure("This email is already registered. Sign in instead.", field="email")
        if err.code == "weak_password":
            raise AuthFailure(f"Password rejected: {err.message}")
        if err.code == "signup_disabled":
            raise AuthFailure("New sign-ups are currently disabled. Contact your administrator.")
        if _is_rate_limited(err):
            raise AuthFailure("Too many sign-up attempts. Please wait a few minutes and try again.")
        raise AuthFailure(f"Could not create account: {err.message}")
    except AuthError as err:
        raise AuthFailure(f"Could not create account: {err}")

    user = res.user
    if user is None:
        raise AuthFailure("Could not create account. Please try again.")
    # With email confirmation on, Supabase hides duplicates by returning a user
    # with no identities instead of an error.
    if user.identities is not None and len(user.identities) == 0:
        raise AuthFailure("This email is already registered. Sign in instead.", field="email")

    try:
        _create_profile(admin, user.id, email, full_name, invite)
    except AuthFailure:
        # Don't leave an auth user without a profile (they could never log in).
        try:
            admin.auth.admin.delete_user(user.id)
        except Exception:
            pass
        raise

    return res.session is None


def _create_profile(admin, user_id: str, email: str, full_name: str, invite: dict) -> None:
    """USERS row with the invite's role, then mark the invite as used."""
    try:
        admin.table("users").insert({"id": user_id, "email": email, "full_name": full_name,
                                     "role": invite["role"]}).execute()
        admin.table("invites").update({"used_at": datetime.now(timezone.utc).isoformat(), "used_by": user_id}) \
            .eq("invite_id", invite["invite_id"]).execute()
    except Exception as e:
        log.exception("Could not save profile")
        raise AuthFailure("Your account could not be saved. Please try again.") from e


def _auth_user_by_email(email: str):
    """The Supabase Auth login for this email that has no USERS profile (an orphan), or None."""
    admin = _service_client()
    page = 1
    while True:
        users = admin.auth.admin.list_users(page=page, per_page=1000)
        for u in users:
            if (u.email or "").lower() == email:
                has_profile = admin.table("users").select("id").eq("id", u.id).limit(1).execute().data
                return None if has_profile else u
        if len(users) < 1000:
            return None
        page += 1


@_service_boundary("sign you in")
def sign_in(email: str, password: str):
    """Authenticate; return (USERS row {id, email, full_name, role}, signed-in client)."""
    from postgrest.exceptions import APIError
    from supabase_auth.errors import AuthApiError, AuthError

    client = _anon_client()
    try:
        res = client.auth.sign_in_with_password({
            "email": normalize_email(email),
            "password": password,
        })
    except AuthApiError as err:
        if err.code == "email_not_confirmed":
            raise AuthFailure("Confirm your email address using the link we sent, then sign in.")
        if _is_rate_limited(err):
            raise AuthFailure("Too many sign-in attempts. Please wait a minute and try again.")
        if err.code == "invalid_credentials" or err.status == 400:
            raise AuthFailure("Incorrect email or password.")
        raise AuthFailure(f"Sign-in failed: {err.message}")
    except AuthError as err:
        raise AuthFailure(f"Sign-in failed: {err}")

    # Read the profile as the signed-in user, so grants + RLS apply.
    def _profile(columns: str):
        return client.table("users").select(columns).eq("id", res.user.id).limit(1).execute().data

    try:
        try:
            rows = _profile("id, email, full_name, role, is_active")
        except APIError as err:
            if err.code != "42703":          # 42703 = is_active not added yet (007 not run)
                raise
            rows = _profile("id, email, full_name, role")
    except APIError as err:
        _revoke(client)
        if err.code == "42501":
            raise AuthFailure("Signed-in users can't read their profile yet: apply the database grants "
                              "(supabase/002_app_tables.sql), then try again.")
        raise
    if not rows or rows[0].get("role") not in ROLES:
        _revoke(client)
        raise AuthFailure("No dashboard access is linked to this account. Contact your administrator.")
    if rows[0].get("is_active") is False:
        _revoke(client)
        raise AuthFailure("This account has been deactivated. Contact your system administrator.")
    return rows[0], client


def _revoke(client) -> None:
    """Sign this client's session out on the Auth server (other devices unaffected)."""
    with suppress(Exception):
        client.auth.sign_out({"scope": "local"})


# =====================================================================
# Session state
# =====================================================================

def init_auth_state() -> None:
    for key, value in _SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def start_session(profile: dict, client) -> None:
    st.session_state[_CLIENT_KEY] = client
    st.session_state[_VERIFIED_AT_KEY] = time.time()
    st.session_state.update({
        "logged_in": True,
        "user_id": profile["id"],
        "email": profile["email"],
        "full_name": profile["full_name"],
        "role": profile["role"],
    })


def logout(revoke: bool = True) -> None:
    """End the Supabase session and clear everything tied to the user, including page state."""
    client = st.session_state.get(_CLIENT_KEY)
    if client is not None and revoke:
        _revoke(client)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_auth_state()


def user_client():
    """Supabase client acting as the signed-in user (grants + RLS apply), or None.

    get_session() returns the current session and refreshes the access token
    first if it has expired or is about to.
    """
    client = st.session_state.get(_CLIENT_KEY)
    if client is None or client.auth.get_session() is None:
        return None
    return client


def session_valid() -> bool:
    """True while the Supabase session is usable; re-verifies the user periodically."""
    import httpx
    from supabase_auth.errors import AuthError

    try:
        client = user_client()
        if client is None:
            return False
        if time.time() - st.session_state.get(_VERIFIED_AT_KEY, 0) > VERIFY_EVERY:
            res = client.auth.get_user()   # verified by the Auth server, not just decoded locally
            if res is None or res.user is None or res.user.id != st.session_state.get("user_id"):
                return False
            try:
                me = client.table("users").select("is_active").eq("id", res.user.id).limit(1).execute().data
            except Exception:                 # 007 not run yet: no active flag to check
                me = [{"is_active": True}]
            if not me or me[0].get("is_active") is False:     # deactivated by the administrator
                return False
            st.session_state[_VERIFIED_AT_KEY] = time.time()
        return True
    except AuthError:          # refresh token revoked/expired, user deleted, …
        return False
    except httpx.HTTPError:    # Auth server unreachable: keep the user signed in, try again next run
        log.warning("Could not verify Supabase session; will retry", exc_info=True)
        return True


def is_logged_in() -> bool:
    return st.session_state.get("logged_in") is True


def current_role() -> str | None:
    return st.session_state.get("role") if is_logged_in() else None


def require_auth(allowed_roles: set[str] | None = None) -> None:
    """Guard for protected pages. Call at the top of every dashboard view.

    app.py already routes by role; this is the page's own last line of defence.
    """
    if not is_logged_in():
        set_flash("info", "Please sign in to continue.")
        st.switch_page(LOGIN_PAGE)
    if not session_valid():
        logout(revoke=False)
        set_flash("info", "Your session has expired. Please sign in again.")
        st.switch_page(LOGIN_PAGE)
    if current_role() not in (allowed_roles or STAFF_ROLES):
        st.error("Your role does not have access to this page.", icon=":material/lock:")
        st.stop()


# =====================================================================
# One-shot messages carried across a page switch
# =====================================================================

def set_flash(kind: str, message: str) -> None:
    st.session_state["_flash"] = (kind, message)


def pop_flash() -> tuple[str, str] | None:
    return st.session_state.pop("_flash", None)


@dataclass
class FormState:
    """Inline field errors + one form-level error, kept across reruns."""
    key: str

    @property
    def _store(self) -> dict:
        return st.session_state.setdefault(self.key, {"fields": {}, "form": None})

    def field(self, name: str) -> str | None:
        return self._store["fields"].get(name)

    def form(self) -> str | None:
        return self._store["form"]

    def set(self, fields: dict | None = None, form: str | None = None) -> None:
        st.session_state[self.key] = {"fields": fields or {}, "form": form}

    def clear_field(self, name: str) -> None:
        self._store["fields"].pop(name, None)
        self._store["form"] = None

    def reset(self) -> None:
        st.session_state.pop(self.key, None)


# =====================================================================
# Administration (System Administrator only) — invites, roles, deactivation
# =====================================================================
# Database writes go through the administrator's own session, so RLS
# (public.is_admin()) is the real guard; the server key is only used for the
# Supabase Auth admin API (ban / unban, last sign-in times).

def _require_admin():
    client = user_client()
    if client is None or current_role() != "admin":
        raise AuthFailure("Only the System Administrator can do this.")
    return client


def create_invite(email: str, role: str) -> str:
    """Create (or replace) the open invite for `email`; returns the plain code to send."""
    client = _require_admin()
    email = normalize_email(email)
    if not is_valid_email(email):
        raise AuthFailure("Enter a valid email address.", field="email")
    if role not in ROLES:
        raise AuthFailure("Choose a role.", field="role")
    if client.table("users").select("id").eq("email", email).limit(1).execute().data:
        raise AuthFailure("This person already has an account.", field="email")
    now = datetime.now(timezone.utc).isoformat()
    client.table("invites").update({"revoked_at": now}).eq("email", email) \
        .is_("used_at", "null").is_("revoked_at", "null").execute()
    code = new_invite_code()
    client.table("invites").insert({"email": email, "role": role, "code_hash": _hash(code),
                                    "invited_by": st.session_state.get("user_id")}).execute()
    return code


def revoke_invite(invite_id: str) -> None:
    _require_admin().table("invites").update({"revoked_at": datetime.now(timezone.utc).isoformat()}) \
        .eq("invite_id", invite_id).execute()


def send_invite_email(email: str, role: str, code: str) -> None:
    """Email the invite code (raises messaging.SendError if email is not set up or fails)."""
    import messaging

    body = (f"Hello,\n\nYou have been invited to the Hotel CLV dashboard as {ROLES[role]}.\n\n"
            f"1. Open {app_url()}/signup\n2. Use this email address: {email}\n3. Enter your invite code: {code}\n\n"
            f"The code works once and expires in {INVITE_DAYS} days.\n\n— System Administrator")
    messaging.send_email(email, "Your Hotel CLV dashboard invitation", body, "Hotel CLV Dashboard")


def set_role(user_id: str, role: str) -> None:
    if role not in ROLES:
        raise AuthFailure("Unknown role.")
    if user_id == st.session_state.get("user_id"):
        raise AuthFailure("You cannot change your own role.")
    _require_admin().table("users").update({"role": role}).eq("id", user_id).execute()


def set_active(user_id: str, active: bool) -> None:
    """Deactivate (staff member left) or reactivate an account. Deactivation also blocks sign-in."""
    client = _require_admin()
    if user_id == st.session_state.get("user_id"):
        raise AuthFailure("You cannot deactivate your own account.")
    client.table("users").update({
        "is_active": active,
        "deactivated_at": None if active else datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).execute()
    _service_client().auth.admin.update_user_by_id(user_id, {"ban_duration": "none" if active else "876000h"})


def last_sign_ins() -> dict[str, str]:
    """user id → last sign-in time (ISO), from Supabase Auth."""
    _require_admin()
    users = _service_client().auth.admin.list_users(page=1, per_page=1000)
    return {u.id: (u.last_sign_in_at.isoformat() if hasattr(u.last_sign_in_at, "isoformat")
                   else u.last_sign_in_at) for u in users if u.last_sign_in_at}


# =====================================================================
# Password reset — 6-digit code by email, 15 minutes, single use
# =====================================================================

GENERIC_RESET_MESSAGE = ("If that email belongs to an active account, a 6-digit code has been sent to it. "
                         "It expires in 15 minutes.")


@_service_boundary("send a reset code")
def request_password_reset(email: str) -> None:
    """Email a reset code. Says nothing about whether the account exists (no account guessing)."""
    import messaging

    admin = _service_client()
    rows = admin.table("users").select("id, full_name, is_active").eq("email", normalize_email(email)) \
        .limit(1).execute().data
    if not rows or rows[0].get("is_active") is False:
        return
    uid = rows[0]["id"]
    hour_ago = datetime.fromtimestamp(time.time() - 3600, timezone.utc).isoformat()
    recent = admin.table("password_resets").select("reset_id").eq("user_id", uid).gte("created_at", hour_ago) \
        .execute().data
    if len(recent) >= 3:
        raise AuthFailure("Too many reset requests for this account. Please try again in an hour.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    admin.table("password_resets").insert({"user_id": uid, "code_hash": _hash(code)}).execute()
    body = (f"Hello {rows[0]['full_name']},\n\nYour Hotel CLV dashboard password reset code is: {code}\n\n"
            f"It expires in {RESET_MINUTES} minutes. If you did not ask for this, ignore this email.")
    try:
        messaging.send_email(normalize_email(email), "Your password reset code", body, "Hotel CLV Dashboard")
    except messaging.SendError as e:
        raise AuthFailure(f"The reset code could not be emailed: {e}")


@_service_boundary("reset your password")
def complete_password_reset(email: str, code: str, new_password: str) -> None:
    admin = _service_client()
    rows = admin.table("users").select("id").eq("email", normalize_email(email)).limit(1).execute().data
    now = datetime.now(timezone.utc).isoformat()
    reset = None
    if rows:
        found = (admin.table("password_resets").select("*").eq("user_id", rows[0]["id"]).is_("used_at", "null")
                 .gt("expires_at", now).order("created_at", desc=True).limit(1).execute().data)
        reset = found[0] if found else None
    if reset is None or reset["attempts"] >= 5:
        raise AuthFailure("This code is invalid or has expired. Request a new one.", field="code")
    if not hmac.compare_digest(_hash(code), reset["code_hash"]):
        admin.table("password_resets").update({"attempts": reset["attempts"] + 1}) \
            .eq("reset_id", reset["reset_id"]).execute()
        raise AuthFailure("Incorrect code. Check the email and try again.", field="code")
    admin.auth.admin.update_user_by_id(rows[0]["id"], {"password": new_password})
    admin.table("password_resets").update({"used_at": now}).eq("reset_id", reset["reset_id"]).execute()
