"""
Create the invitation for the first System Administrator (run once, at installation).

    frontend/.venv/Scripts/python.exe supabase/create_admin_invite.py admin@hotel.com

After this, the administrator signs up in the dashboard with that email and the
printed code, and invites everyone else from the Administration page. Uses the
server key from .streamlit/secrets.toml — run it only on a trusted machine.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import auth  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2 or not auth.is_valid_email(sys.argv[1]):
        print("Usage: create_admin_invite.py <administrator email>")
        return 1
    problem = auth.config_error()
    if problem:
        print(problem)
        return 1
    email = auth.normalize_email(sys.argv[1])
    admin = auth._service_client()
    if admin.table("users").select("id").eq("email", email).limit(1).execute().data:
        print(f"{email} already has an account.")
        return 1
    admin.table("invites").update({"revoked_at": datetime.now(timezone.utc).isoformat()}).eq("email", email) \
        .is_("used_at", "null").is_("revoked_at", "null").execute()
    code = auth.new_invite_code()
    admin.table("invites").insert({"email": email, "role": "admin", "code_hash": auth._hash(code)}).execute()
    print(f"Administrator invite created for {email} (expires in {auth.INVITE_DAYS} days).")
    try:
        auth.send_invite_email(email, "admin", code)
        print(f"Invitation emailed to {email}.")
    except Exception as e:  # noqa: BLE001  (email not set up / unreachable: the printed code still works)
        print(f"The email could not be sent ({e}). Use the code below instead.")
    print(f"Invite code (backup): {code}")
    print(f"Sign up at {auth.app_url()}/signup with this email and code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
