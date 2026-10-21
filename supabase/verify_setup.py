"""
Verify the Supabase setup after running 001–004 and supabase/load_predictions.py.

    frontend/.venv/Scripts/python.exe supabase/verify_setup.py      (from the repo root)

Checks tables, Data API grants, RLS and the private ml-models bucket. The
end-to-end RLS test creates a temporary auth user + guest and removes them
(and anything they created) before exiting.
"""

from __future__ import annotations
from postgrest.types import CountMethod

import secrets
from typing import Any, cast
from datetime import datetime, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import auth  # noqa: E402  (reads .streamlit/secrets.toml through st.secrets)
from postgrest.exceptions import APIError  # noqa: E402
from postgrest.types import CountMethod  # noqa: E402
from supabase import ClientOptions, create_client  # noqa: E402

TABLES = ["users", "guests", "clv_predictions", "action_logs"]
results: list[tuple[str, bool, str]] = []


def rows(res) -> list[dict[str, Any]]:
    """Rows from a Supabase response. `.data` is typed as generic JSON; our tables return row dicts."""
    return cast(list[dict[str, Any]], res.data or [])


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    return ok


def denied(fn) -> tuple[bool, str]:
    """True if the call is refused (error) or silently affects/returns nothing."""
    try:
        res = fn()
        return (not getattr(res, "data", None)), "no rows"
    except APIError as e:
        return True, e.code or "error"


def main() -> int:
    problem = auth.config_error()
    if not check("secrets configured", problem is None, problem or ""):
        return 1

    url = auth.st.secrets["supabase"]["url"]
    opts = ClientOptions(auto_refresh_token=False, persist_session=False)
    admin = auth._service_client()
    anon = create_client(url, auth._secret(auth._PUBLIC_KEY_NAMES), options=opts)

    # 1. Tables exist and are reachable by the server role
    missing = []
    for t in TABLES:
        try:
            admin.table(t).select("*", count=CountMethod.exact).limit(0).execute()
        except APIError as e:
            missing.append(f"{t} ({e.code})")
    if not check("all 4 tables exist", not missing, ", ".join(missing)):
        print("\nRun supabase/002_app_tables.sql in the SQL Editor, then re-run this script.")
        return 1

    # 2. Anonymous (not signed in) access is refused everywhere
    for t in TABLES:
        ok, how = denied(lambda t=t: anon.table(t).select("*").limit(1).execute())
        check(f"anon cannot read {t}", ok, how)

    # 3. Private model bucket
    try:
        bucket = admin.storage.get_bucket("ml-models")
        check("ml-models bucket is private", not bucket.public)
    except Exception as e:  # noqa: BLE001
        check("ml-models bucket exists", False, str(e)[:80])

    # 4. End-to-end as a real signed-in user
    email = f"verify-{secrets.token_hex(4)}@example.invalid"
    password = "Tmp#" + secrets.token_urlsafe(12)
    guest_id = f"VERIFY-{secrets.token_hex(3)}"
    uid = rm_uid = adm_uid = None
    original_threshold = None
    try:
        uid = admin.auth.admin.create_user({"email": email, "password": password, "email_confirm": True}).user.id
        admin.table("users").insert({"id": uid, "email": email, "full_name": "Setup Check", "role": "marketing"}).execute()
        admin.table("guests").insert({"guest_id": guest_id, "total_previous_stays": 1}).execute()
        pred = rows(admin.table("clv_predictions").insert({"guest_id": guest_id, "predicted_clv": 1000, "clv_tier": "Low",
                                                      "model_used": "verify"}).execute())[0]

        profile, user = auth.sign_in(email, password)
        check("sign-in reads own USERS row (grant + RLS)", profile["id"] == uid)

        other = rows(admin.table("users").select("id").neq("id", uid).limit(1).execute())
        if other:
            visible = rows(user.table("users").select("id").eq("id", other[0]["id"]).execute())
            check("cannot read other users' rows", visible == [])

        check("can read guests", bool(rows(user.table("guests").select("guest_id").eq("guest_id", guest_id).execute())))
        check("can read clv_predictions",
              bool(rows(user.table("clv_predictions").select("prediction_id").eq("guest_id", guest_id).execute())))

        log = rows(user.table("action_logs").insert({
            "user_id": uid, "guest_id": guest_id, "prediction_id": pred["prediction_id"],
            "action_taken": "Setup check", "action_status": "Completed", "delivery_channel": "Email",
        }).execute())
        check("can insert action log as self", bool(log))

        forged = other[0]["id"] if other else "00000000-0000-0000-0000-000000000000"
        ok, how = denied(lambda: user.table("action_logs").insert({
            "user_id": forged, "guest_id": guest_id, "action_taken": "Forged"}).execute())
        check("cannot insert action log as another user", ok, how)

        ok, how = denied(lambda: user.table("action_logs").insert({
            "user_id": uid, "guest_id": guest_id, "action_taken": "x", "action_status": "Done?"}).execute())
        check("action_status must be Pending/Completed/Failed", ok, how)

        if log:
            lid = log[0]["log_id"]
            ok, how = denied(lambda: user.table("action_logs").update({"action_status": "Failed"}).eq("log_id", lid).execute())
            check("cannot change an action log's status", ok, how)
            ok, how = denied(lambda: user.table("action_logs").delete().eq("log_id", lid).execute())
            check("cannot delete action logs", ok, how)

        ok, how = denied(lambda: user.table("guests").insert({"guest_id": guest_id + "-X"}).execute())
        check("cannot write guests", ok, how)
        ok, how = denied(lambda: user.table("users").update({"role": "revenue_manager"}).eq("id", uid).execute())
        check("cannot change own role", ok, how)

        # ---- 003: outcomes + shared settings --------------------------------
        has_003 = True
        try:
            admin.table("app_settings").select("key").limit(1).execute()
        except APIError:
            has_003 = False
            print("SKIP  outcome/settings checks — run supabase/003_outcomes_settings.sql first")
        if has_003 and log:
            lid = log[0]["log_id"]
            res = rows(user.table("action_logs").update({"outcome": "Came back", "outcome_at": datetime.now(timezone.utc).isoformat()})                 .eq("log_id", lid).execute())
            check("marketing can record an outcome", bool(res) and res[0]["outcome"] == "Came back")
            ok, how = denied(lambda: user.table("action_logs").update({"outcome": "Maybe"}).eq("log_id", lid).execute())
            check("outcome must be Waiting/Came back/Didn't come back", ok, how)

            row = rows(user.table("app_settings").select("value").eq("key", "at_risk_days").execute())
            check("signed-in users can read the at-risk threshold", bool(row))
            original_threshold = row[0]["value"] if row else None
            ok, how = denied(lambda: user.table("app_settings").update({"value": 90, "updated_by": uid})
                             .eq("key", "at_risk_days").execute())
            check("marketing cannot change the threshold", ok, how)

            rm_email = f"verify-rm-{secrets.token_hex(4)}@example.invalid"
            rm_uid = admin.auth.admin.create_user({"email": rm_email, "password": password, "email_confirm": True}).user.id
            admin.table("users").insert({"id": rm_uid, "email": rm_email, "full_name": "Setup Check RM",
                                         "role": "revenue_manager"}).execute()
            _, rm = auth.sign_in(rm_email, password)
            res = rows(rm.table("app_settings").update({"value": 90, "updated_by": rm_uid})                 .eq("key", "at_risk_days").execute())
            check("revenue manager can change the threshold", bool(res) and res[0]["value"] == 90)
            ok, how = denied(lambda: rm.table("app_settings").update({"value": 45, "updated_by": rm_uid})
                             .eq("key", "at_risk_days").execute())
            check("threshold limited to 30/60/90/120", ok, how)
            ok, how = denied(lambda: rm.table("action_logs").update({"outcome": "Waiting"}).eq("log_id", lid).execute())
            check("revenue manager cannot edit outcomes", ok, how)

            # ---- 006: Revenue Manager decisions + settings history ----------
            try:
                admin.table("rm_decisions").select("decision_id").limit(1).execute()
                has_006 = True
            except APIError:
                has_006 = False
                print("SKIP  decision checks — run supabase/006_rm_decisions.sql first")
            if has_006:
                res = rows(rm.table("rm_decisions").insert({
                    "guest_id": guest_id, "user_id": rm_uid, "decision_type": "Override action",
                    "original_action": "Win-back discount", "new_action": "Personal call from manager",
                    "reason": "Setup check decision"}).execute())
                check("revenue manager can record a decision", bool(res))
                ok, how = denied(lambda: user.table("rm_decisions").insert({
                    "guest_id": guest_id, "user_id": uid, "decision_type": "Flag priority",
                    "reason": "Marketing should not"}).execute())
                check("marketing cannot record decisions", ok, how)
                ok, how = denied(lambda: rm.table("rm_decisions").insert({
                    "guest_id": guest_id, "user_id": rm_uid, "decision_type": "Flag priority",
                    "reason": "no"}).execute())
                check("a decision needs a reason of 5+ characters", ok, how)
                check("everyone can read decisions",
                      bool(rows(user.table("rm_decisions").select("decision_id").eq("guest_id", guest_id).execute())))
                hist = rows(user.table("settings_history").select("new_value, changed_by").eq("key", "at_risk_days")
                            .eq("changed_by", rm_uid).execute())
                check("threshold changes are kept in settings_history", any(h["new_value"] == 90 for h in hist))
                ok, how = denied(lambda: user.table("settings_history").insert({
                    "key": "at_risk_days", "new_value": 30}).execute())
                check("users cannot write settings_history", ok, how)
            auth._revoke(rm)

        # ---- 004: model runs, prediction columns, staff names ---------------
        has_004 = True
        try:
            admin.table("model_runs").select("predicted_at").limit(1).execute()
        except APIError:
            has_004 = False
            print("SKIP  model/dashboard checks — run supabase/004_predictions_dashboard.sql first")
        if has_004:
            new_cols = {"guests": "market_segment, hotel_type, room_type, meal_plan, booking_canceled, "
                                  "first_booking_year",
                        "clv_predictions": "tier_badge, clv_percentile, top_drivers, in_action_queue"}
            for table, cols in new_cols.items():
                try:
                    user.table(table).select(cols).limit(1).execute()
                    check(f"can read the 004 columns on {table}", True)
                except APIError as e:
                    check(f"can read the 004 columns on {table}", False, e.message or "")
            for view in ("model_runs", "staff_directory"):
                ok, how = denied(lambda view=view: anon.table(view).select("*").limit(1).execute())
                check(f"anon cannot read {view}", ok, how)
            check("signed-in users can read staff names",
                  bool(rows(user.table("staff_directory").select("full_name, role").eq("id", uid).execute())))
            ok, how = denied(lambda: user.table("staff_directory").select("email").limit(1).execute())
            check("staff directory does not expose emails", ok, how)
            ok, how = denied(lambda: user.table("model_runs").insert({
                "predicted_at": datetime.now(timezone.utc).isoformat(), "model_used": "x", "as_of_date": "2019-01-01",
                "high_min_clv": 1, "low_max_clv": 0, "platinum_min_clv": 2}).execute())
            check("cannot write model_runs", ok, how)
            runs = rows(user.table("model_runs").select("predicted_at, guests_predicted")
                        .order("predicted_at", desc=True).limit(1).execute())
            if runs:
                stored = user.table("clv_predictions").select("guest_id", count=CountMethod.exact).limit(0) \
                    .eq("predicted_at", runs[0]["predicted_at"]).execute().count
                check("latest run is fully loaded", stored == runs[0]["guests_predicted"],
                      f"{stored:,} of {runs[0]['guests_predicted']:,} predictions")
            else:
                print("SKIP  no predictions loaded yet — run supabase/load_predictions.py")

        # ---- 007: System Administrator, invites, least privilege ----------
        has_007 = True
        try:
            admin.table("invites").select("invite_id").limit(1).execute()
        except APIError:
            has_007 = False
            print("SKIP  administrator checks — run supabase/007_admin_invites.sql first")
        if has_007:
            adm_email = f"verify-adm-{secrets.token_hex(4)}@example.invalid"
            adm_uid = admin.auth.admin.create_user({"email": adm_email, "password": password,
                                                    "email_confirm": True}).user.id
            admin.table("users").insert({"id": adm_uid, "email": adm_email, "full_name": "Setup Check Admin",
                                         "role": "admin"}).execute()
            _, adm = auth.sign_in(adm_email, password)
            check("admin can list all staff accounts",
                  len(rows(adm.table("users").select("id").execute())) >= 2)
            ok, how = denied(lambda: adm.table("guests").select("guest_id").limit(1).execute())
            check("admin cannot read guest data (least privilege)", ok, how)
            ok, how = denied(lambda: adm.table("clv_predictions").select("prediction_id").limit(1).execute())
            check("admin cannot read predictions", ok, how)
            inv = rows(adm.table("invites").insert({"email": f"new-{secrets.token_hex(3)}@example.invalid",
                                                    "role": "marketing", "code_hash": "x" * 64,
                                                    "invited_by": adm_uid}).execute())
            check("admin can create an invite", bool(inv))
            ok, how = denied(lambda: user.table("invites").insert({"email": "x@example.invalid", "role": "admin",
                                                                   "code_hash": "y" * 64, "invited_by": uid}).execute())
            check("staff cannot create invites", ok, how)
            ok, how = denied(lambda: user.table("invites").select("invite_id").limit(1).execute())
            check("staff cannot read invites", ok, how)
            ok, how = denied(lambda: user.table("users").update({"role": "admin"}).eq("id", uid).execute())
            check("staff cannot change roles", ok, how)
            res = rows(adm.table("users").update({"is_active": False}).eq("id", uid).execute())
            check("admin can deactivate an account", bool(res) and res[0]["is_active"] is False)
            ok, how = denied(lambda: user.table("guests").select("guest_id").eq("guest_id", guest_id).execute())
            check("a deactivated account loses data access", ok, how)
            try:
                auth.sign_in(email, password)
                check("a deactivated account cannot sign in", False)
            except auth.AuthFailure:
                check("a deactivated account cannot sign in", True)
            ok, how = denied(lambda: anon.table("password_resets").select("reset_id").limit(1).execute())
            check("reset codes are not readable from the app keys", ok, how)
            if inv:
                admin.table("invites").delete().eq("invite_id", inv[0]["invite_id"]).execute()
            auth._revoke(adm)

        auth._revoke(user)
    finally:
        if original_threshold is not None:
            admin.table("app_settings").update({"value": original_threshold}).eq("key", "at_risk_days").execute()
        if rm_uid:   # the test's threshold changes are not real history
            try:
                admin.table("settings_history").delete().eq("changed_by", rm_uid).execute()
            except APIError:
                pass
        # guests → cascades clv_predictions + action_logs; auth user → cascades users row
        admin.table("guests").delete().like("guest_id", f"{guest_id}%").execute()
        for u in (uid, rm_uid, adm_uid):
            if u:
                admin.auth.admin.delete_user(u)
        print("cleanup: temporary users, guest, prediction and logs removed; threshold restored")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
