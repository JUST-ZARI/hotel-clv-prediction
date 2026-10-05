"""
auth.py — Supabase authentication, invite tokens and role-based session state.

Signup:  form → password rules → invite token → Supabase Auth → USERS table
Login:   Supabase Auth → USERS row (role) → st.session_state

Required secrets (see .streamlit/secrets.example.toml):
    [supabase]       url, publishable_key|anon_key, secret_key|service_role_key
    [invite_tokens]  revenue_manager, marketing
"""

from __future__ import annotations

import base64
import functools
import hmac
from contextlib import suppress
import json
import logging
import re
import time
from dataclasses import dataclass

import streamlit as st

ROLES = {
    "revenue_manager": "Revenue Manager",
    "marketing": "Marketing Team",
}

LOGIN_PAGE = "views/login.py"
SIGNUP_PAGE = "views/signup.py"

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
    "invite_token": (5, 300), # 5 wrong tokens → wait 5 min
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
    """Return a setup message if Supabase / invite-token secrets are missing or misplaced.

    for_signup additionally enforces invite-token strength (only signup uses them).
    """
    try:
        url = str(st.secrets["supabase"].get("url", "")).strip()
        tokens = st.secrets["invite_tokens"]
    except (KeyError, FileNotFoundError):
        return "Supabase is not configured. Add .streamlit/secrets.toml (see secrets.example.toml)."
    public, server = _secret(_PUBLIC_KEY_NAMES), _secret(_SERVER_KEY_NAMES)
    missing = [] if url else ["supabase.url"]
    missing += [] if public else ["supabase.publishable_key (or anon_key)"]
    missing += [] if server else ["supabase.secret_key (or service_role_key)"]
    missing += [f"invite_tokens.{r}" for r in ROLES
                if not tokens.get(r) or _is_placeholder(str(tokens[r]))]
    if missing:
        return "Missing secrets: " + ", ".join(missing) + "."
    if not url.startswith("https://"):
        return "supabase.url must be your project URL, e.g. https://<project-ref>.supabase.co."
    if not _is_public_key(public):
        return "The public Supabase key must be the publishable (sb_publishable_…) or anon key."
    if not _is_server_key(server):
        return ("The server Supabase key must be the secret (sb_secret_…) or service_role key — "
                "a public key in that slot would let the app write rows it shouldn't.")
    if len(set(str(tokens[r]) for r in ROLES)) < len(ROLES):
        return "Each role needs its own invite token."
    if for_signup and any(len(str(tokens[r])) < 12 for r in ROLES):
        return "Invite tokens must be at least 12 characters (generate with secrets.token_urlsafe)."
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


def verify_invite_token(role: str, token: str) -> bool:
    """True only if `token` is the configured invite token for `role`."""
    expected = st.secrets["invite_tokens"].get(role, "")
    supplied = (token or "").strip()
    if not expected or not supplied:
        return False
    return hmac.compare_digest(supplied.encode(), str(expected).encode())


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
def sign_up(full_name: str, email: str, password: str, role: str) -> bool:
    """Create the Supabase Auth user and its USERS row.

    Returns True if Supabase requires email confirmation before first login.
    Raises AuthFailure with a user-facing message on any error.
    """
    from supabase_auth.errors import AuthApiError, AuthError

    email = normalize_email(email)
    admin = _service_client()

    existing = admin.table("users").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        raise AuthFailure("This email is already registered. Sign in instead.", field="email")

    try:
        res = _anon_client().auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}, "email_redirect_to": "http://localhost:8502/login",},
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
        admin.table("users").insert({
            "id": user.id,
            "email": email,
            "full_name": full_name,
            "role": role,
        }).execute()
    except Exception:
        # Don't leave an auth user without a profile (they could never log in).
        try:
            admin.auth.admin.delete_user(user.id)
        except Exception:
            pass
        raise AuthFailure("Your account could not be saved. Please try again.")

    return res.session is None


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
    try:
        rows = (
            client.table("users")
            .select("id, email, full_name, role")
            .eq("id", res.user.id)
            .limit(1)
            .execute()
            .data
        )
    except APIError as err:
        _revoke(client)
        if err.code == "42501":
            raise AuthFailure("Signed-in users can't read their profile yet: apply the database grants "
                              "(supabase/002_app_tables.sql), then try again.")
        raise
    if not rows or rows[0].get("role") not in ROLES:
        _revoke(client)
        raise AuthFailure("No dashboard access is linked to this account. Contact your administrator.")
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
    if current_role() not in (allowed_roles or ROLES):
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
