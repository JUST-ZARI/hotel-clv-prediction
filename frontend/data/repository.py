"""
Data access for the dashboard views.

Views call only these functions. Everything is read from Supabase as the
signed-in user, so the grants and RLS policies in supabase/*.sql apply:

    MODEL_RUNS       one row per prediction run (thresholds, as-of date, test scores)
    GUESTS           one row per guest
    CLV_PREDICTIONS  one row per guest per run — the app shows the newest run
    ACTION_LOGS      actions taken by staff, with outcomes
    APP_SETTINGS     shared settings (at-risk threshold)
    STAFF_DIRECTORY  staff names for action logs

The guest table is loaded once per run and shared by every session (all
signed-in staff may read all guests); action logs and settings are read fresh.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import pandas as pd
import streamlit as st
from postgrest import SyncPostgrestClient
from postgrest.exceptions import APIError
from postgrest.types import CountMethod

import auth

TIERS = ["High", "Medium", "Low"]
AT_RISK_DEFAULT_DAYS = 60
AT_RISK_OPTIONS = [30, 60, 90, 120]   # choices offered to the Revenue Manager
OUTCOMES = ["Waiting", "Came back", "Didn't come back"]
TIER_STRATEGY = {
    "High": "Priority retention / loyalty incentives / personalised service",
    "Medium": "Targeted re-engagement / upselling",
    "Low": "Cost-efficient engagement / win-back offers",
}

PAGE_ROWS = 1000      # Supabase returns at most 1,000 rows per request
FETCH_THREADS = 8
# Lists and charts need only these columns (kept small: they are loaded for every guest).
# Guest Lookup reads one guest's full row with get_guest().
GUEST_COLUMNS = ("guest_id, avg_daily_rate, total_previous_stays, booking_channel, last_stay_date, guest_type, "
                 "first_booking_year")
PREDICTION_COLUMNS = "guest_id, predicted_clv, tier_badge, recommended_action, in_action_queue"


def _rows(res) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], res.data or [])


def _client():
    client = auth.user_client()
    if client is None:
        st.error("Your session has ended. Please sign in again.")
        st.stop()
    return client


def _setup_problem(message: str) -> None:
    st.error(message)
    st.stop()


# ---------------------------------------------------------------------------
# MODEL_RUNS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def _runs(_client) -> list[dict]:
    """The two newest prediction runs, newest first."""
    return _rows(_client.table("model_runs").select("*").order("predicted_at", desc=True).limit(2).execute())


def _run() -> dict:
    try:
        runs = _runs(_client())
    except APIError:
        _setup_problem("The model tables are missing. Run supabase/004_predictions_dashboard.sql in Supabase.")
    if not runs:
        _setup_problem("No predictions loaded yet. Run supabase/load_predictions.py to load the model output.")
    return runs[0]


@dataclass(frozen=True)
class ModelMeta:
    model_used: str
    predicted_at: datetime
    as_of_date: datetime
    high_min_clv: float
    low_max_clv: float
    platinum_min_clv: float

    @property
    def updated_label(self) -> str:
        return f"{self.predicted_at.day} {self.predicted_at:%b %Y}"

    @property
    def tier_rule(self) -> str:
        return (f"CLV tiers: High (≥ KSh {self.high_min_clv:,.0f}), "
                f"Medium (KSh {self.low_max_clv:,.0f}–{self.high_min_clv:,.0f}), "
                f"Low (≤ KSh {self.low_max_clv:,.0f}); Platinum = High and ≥ KSh {self.platinum_min_clv:,.0f}.")


def model_meta() -> ModelMeta:
    r = _run()
    return ModelMeta(r["model_used"], pd.Timestamp(r["predicted_at"]).to_pydatetime(),
                     pd.Timestamp(r["as_of_date"]).to_pydatetime(), float(r["high_min_clv"]),
                     float(r["low_max_clv"]), float(r["platinum_min_clv"]))


# ---------------------------------------------------------------------------
# GUESTS + CLV_PREDICTIONS (newest run)
# ---------------------------------------------------------------------------

def _fetch_all(base_url: str, headers: dict, table: str, columns: str, run_at: str | None = None) -> pd.DataFrame:
    """Every row of a table (or of one run), fetched in parallel pages of PAGE_ROWS.

    An HTTP connection must not be shared between threads, so every thread
    opens its own Data API client with the signed-in user's headers (same
    token, so the same grants and RLS apply).
    """
    local = threading.local()
    opened: list[SyncPostgrestClient] = []
    lock = threading.Lock()

    def rest() -> SyncPostgrestClient:
        if not hasattr(local, "rest"):
            local.rest = SyncPostgrestClient(base_url, headers=headers)
            with lock:
                opened.append(local.rest)
        return local.rest

    def query(columns: str, **kwargs):
        q = rest().from_(table).select(columns, **kwargs)
        return q.eq("predicted_at", run_at) if run_at else q

    def page(start: int) -> list[dict]:
        return _rows(query(columns).order("guest_id").range(start, start + PAGE_ROWS - 1).execute())

    try:
        total = query("guest_id", count=CountMethod.exact).limit(0).execute().count or 0
        with ThreadPoolExecutor(FETCH_THREADS) as pool:
            pages = list(pool.map(page, range(0, total, PAGE_ROWS)))
    finally:
        for client in opened:
            client.session.close()
    return pd.DataFrame([row for p in pages for row in p])


@st.cache_resource(ttl=3600, max_entries=2, show_spinner="Loading guest predictions…")
def _guest_frame(_client, run_at: str, as_of: str) -> pd.DataFrame:
    """GUESTS joined to their prediction in run `run_at`. Shared read-only: never modify it."""
    conn = (str(_client.postgrest.base_url), dict(_client.postgrest.session.headers))
    with ThreadPoolExecutor(2) as pool:     # both tables at once
        g = pool.submit(_fetch_all, *conn, "guests", GUEST_COLUMNS)
        p = pool.submit(_fetch_all, *conn, "clv_predictions", PREDICTION_COLUMNS, run_at)
        g, p = g.result(), p.result()
    df = _prepare(g.merge(p, on="guest_id", how="inner", validate="one_to_one"), as_of)
    for col in ("booking_channel", "guest_type", "clv_tier", "tier_badge", "recommended_action"):
        df[col] = df[col].astype("category")
    return df.sort_values("predicted_clv", ascending=False, ignore_index=True)


def _prepare(df: pd.DataFrame, as_of: str) -> pd.DataFrame:
    """Types and derived columns shared by the guest list and a single guest."""
    for col in ("last_stay_date", "first_stay_date"):
        if col in df:
            df[col] = pd.to_datetime(df[col])
    df["predicted_clv"] = df["predicted_clv"].round().astype(int)
    df["avg_daily_rate"] = df["avg_daily_rate"].round().astype(int)
    df["clv_tier"] = df["tier_badge"].replace({"Platinum": "High"})
    df["days_since_last_stay"] = (pd.Timestamp(as_of) - df["last_stay_date"]).dt.days.astype(int)
    return df


def guests() -> pd.DataFrame:
    """Every guest with their newest prediction, highest predicted CLV first. Read-only."""
    run = _run()
    return _guest_frame(_client(), run["predicted_at"], run["as_of_date"])


def booking_channels() -> list[str]:
    return guests()["booking_channel"].value_counts().index.astype(str).tolist()


def guest_types() -> list[str]:
    return guests()["guest_type"].value_counts().index.astype(str).tolist()


def default_guest_id() -> str:
    """Guest shown when Guest Lookup opens: the top of the Action Board."""
    return str(action_queue()["guest_id"].iloc[0])


def overview() -> dict:
    df = guests()
    high = df["clv_tier"] == "High"
    return {
        "total_guests": len(df),
        "high_value_guests": int(high.sum()),
        "at_risk_high_value": int((high & (df["days_since_last_stay"] >= at_risk_days())).sum()),
        "avg_predicted_clv": int(round(df["predicted_clv"].mean(), -2)),
    }


def action_queue() -> pd.DataFrame:
    """Guests on the Action Board, highest predicted CLV first."""
    df = guests()
    return df[df["in_action_queue"]]


def min_clv_options() -> list[int]:
    """At-Risk "Min CLV" choices: the High-tier floor, then round steps above it."""
    floor = int(model_meta().high_min_clv)
    return [floor] + [v for v in (100_000, 150_000, 250_000, 500_000) if v > floor]


def risk_level(days: int, threshold: int) -> str:
    """How far past the threshold a guest is: 30+ days over → High, 10+ → Medium."""
    if days >= threshold + 30:
        return "High Risk"
    if days >= threshold + 10:
        return "Medium Risk"
    return "Low Risk"


def at_risk(min_clv: int | None = None, min_days: int | None = None) -> pd.DataFrame:
    """High-tier guests inactive for at least min_days (default: the shared threshold)."""
    threshold = at_risk_days()
    df = guests()
    mask = (df["clv_tier"] == "High") & (df["days_since_last_stay"] >= (min_days or threshold))
    if min_clv:
        mask &= df["predicted_clv"] >= min_clv
    out = df[mask].copy()
    over = out["days_since_last_stay"] - threshold
    out["risk_level"] = pd.cut(over, [-1, 9, 29, float("inf")], labels=["Low Risk", "Medium Risk", "High Risk"]
                               ).astype(str)
    return out


@st.cache_data(ttl=600, max_entries=500, show_spinner=False)
def _guest_row(_client, guest_id: str, run_at: str, as_of: str) -> dict | None:
    g = _rows(_client.table("guests").select("*").eq("guest_id", guest_id).limit(1).execute())
    p = _rows(_client.table("clv_predictions").select("*").eq("guest_id", guest_id)
              .eq("predicted_at", run_at).limit(1).execute())
    if not g or not p:
        return None
    return _prepare(pd.DataFrame([{**g[0], **p[0]}]), as_of).iloc[0].to_dict()


def get_guest(guest_id: str) -> pd.Series | None:
    """One guest with every stored detail and their newest prediction (incl. top_drivers)."""
    run = _run()
    row = _guest_row(_client(), guest_id, run["predicted_at"], run["as_of_date"])
    return None if row is None else pd.Series(row)


def normalize_guest_id(raw: str) -> str:
    """Accept 'G-000123', 'g123', 'G-123' or '123'."""
    s = (raw or "").strip().upper().replace(" ", "")
    s = s[2:] if s.startswith("G-") else s[1:] if s.startswith("G") else s
    return f"G-{int(s):06d}" if s.isdigit() else (raw or "").strip().upper()


def stay_history(g: pd.Series) -> list[dict]:
    """The guest's booking in the data (one per guest), most recent first."""
    return [{
        "date": f"{g['first_stay_date']:%d %b %Y}",
        "nights": int(g["avg_length_of_stay"]),
        "amount": int(g["avg_daily_rate"]),     # nightly rate
        "room_type": f"Room type {g['room_type']}" if isinstance(g["room_type"], str) else "—",
        "status": "Cancelled" if g["booking_canceled"] else "Stayed",
    }]


def prediction_drivers(guest_id: str) -> list[tuple[str, float, str]]:
    """Top features behind this guest's prediction: (label, share %, 'up' | 'down')."""
    g = get_guest(guest_id)
    drivers = (g["top_drivers"] if g is not None else None) or []
    return [(d["feature"], float(d["impact_pct"]), d["direction"]) for d in drivers]


def tier_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Guests per tier by first booking year (rows = years, columns = tiers)."""
    out = df.pivot_table(index="first_booking_year", columns="clv_tier", values="guest_id",
                         aggfunc="count", fill_value=0, observed=False)
    return out.reindex(columns=TIERS, fill_value=0).sort_index()


def segment_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("clv_tier", observed=False).agg(
        guests=("guest_id", "count"),
        avg_clv=("predicted_clv", "mean"),
        avg_stays=("total_previous_stays", "mean"),
        avg_adr=("avg_daily_rate", "mean"),
        avg_days=("days_since_last_stay", "mean"),
    ).reindex(TIERS)
    g["strategy"] = [TIER_STRATEGY[t] for t in g.index]
    return g


@st.cache_data(ttl=3600, show_spinner=False)
def _tier_counts(_client, run_at: str) -> dict[str, int]:
    def count(tier: str) -> int:
        return (_client.table("clv_predictions").select("guest_id", count=CountMethod.exact).limit(0)
                .eq("predicted_at", run_at).eq("clv_tier", tier).execute().count or 0)
    return {t: count(t) for t in TIERS}


def tier_trend() -> dict[str, tuple[str, str]]:
    """Change in guests per tier vs the previous prediction run: tier → (direction, label)."""
    runs = _runs(_client())
    if len(runs) < 2:
        return {t: ("flat", "First prediction run") for t in TIERS}
    now = guests()["clv_tier"].value_counts()
    before = _tier_counts(_client(), runs[1]["predicted_at"])
    out = {}
    for t in TIERS:
        change = (now.get(t, 0) - before[t]) / before[t] if before[t] else 0.0
        direction = "up" if change > 0.005 else "down" if change < -0.005 else "flat"
        out[t] = (direction, "Stable vs prev. run" if direction == "flat" else f"{change:+.0%} vs prev. run")
    return out


# ---------------------------------------------------------------------------
# APP_SETTINGS + STAFF_DIRECTORY
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def _settings(_client) -> dict:
    res = _client.table("app_settings").select("value, updated_by, updated_at").eq("key", "at_risk_days").execute()
    row = (_rows(res) or [{}])[0]
    return {"at_risk_days": int(row.get("value") or AT_RISK_DEFAULT_DAYS),
            "updated_by": row.get("updated_by"), "updated_at": row.get("updated_at")}


def at_risk_days() -> int:
    """Days without a stay after which a High-tier guest counts as at-risk."""
    return _settings(_client())["at_risk_days"]


def set_at_risk_days(days: int) -> None:
    """Revenue Manager only — enforced by RLS (other roles update no rows)."""
    if days not in AT_RISK_OPTIONS:
        raise ValueError(f"Unsupported threshold: {days}")
    res = (_client().table("app_settings")
           .update({"value": days, "updated_by": st.session_state.get("user_id"),
                    "updated_at": datetime.now(timezone.utc).isoformat()})
           .eq("key", "at_risk_days").execute())
    if not _rows(res):
        raise PermissionError("Only the Revenue Manager can change the at-risk threshold.")
    _settings.clear()


@st.cache_data(ttl=300, show_spinner=False)
def _staff(_client) -> dict[str, dict]:
    return {r["id"]: r for r in _rows(_client.table("staff_directory").select("id, full_name, role").execute())}


def settings_meta() -> dict:
    s = dict(_settings(_client()))
    s["updated_by"] = _staff(_client()).get(s["updated_by"] or "", {}).get("full_name")
    return s


# ---------------------------------------------------------------------------
# ACTION_LOGS
# ---------------------------------------------------------------------------

LOG_COLUMNS = ("log_id, user_id, guest_id, prediction_id, action_taken, action_status, delivery_channel, "
               "logged_at, outcome, outcome_at")


def action_logs(guest_id: str) -> pd.DataFrame:
    client = _client()
    res = client.table("action_logs").select(LOG_COLUMNS).eq("guest_id", guest_id) \
        .order("logged_at", desc=True).execute()
    logs = pd.DataFrame(_rows(res), columns=[c.strip() for c in LOG_COLUMNS.split(",")])
    staff = _staff(client)
    logs["user_name"] = logs["user_id"].map(lambda u: staff.get(u, {}).get("full_name", ""))
    logs["user_role"] = logs["user_id"].map(lambda u: staff.get(u, {}).get("role"))
    logs["logged_at"] = pd.to_datetime(logs["logged_at"], utc=True).dt.tz_convert("Africa/Nairobi")
    return logs


def log_action(guest_id: str, action_taken: str, delivery_channel: str,
               action_status: str = "Completed") -> None:
    """Record an action as the signed-in user. Completed actions start with outcome 'Waiting'."""
    g = get_guest(guest_id)
    _client().table("action_logs").insert({
        "user_id": st.session_state.get("user_id"),
        "guest_id": guest_id,
        "prediction_id": None if g is None else g["prediction_id"],
        "action_taken": action_taken,
        "action_status": action_status,
        "delivery_channel": delivery_channel,
        "outcome": "Waiting" if action_status == "Completed" else None,
    }).execute()


def set_outcome(log_id: str, outcome: str) -> None:
    """Record whether the guest came back after a completed action (Marketing Team, enforced by RLS)."""
    if outcome not in OUTCOMES:
        raise ValueError(f"Unknown outcome: {outcome}")
    res = (_client().table("action_logs")
           .update({"outcome": outcome,
                    "outcome_at": None if outcome == "Waiting" else datetime.now(timezone.utc).isoformat()})
           .eq("log_id", log_id).execute())
    if not _rows(res):
        raise PermissionError("Only the Marketing Team can record outcomes.")


def outcome_summary(days: int = 30) -> dict:
    """Completed actions in the last `days` days, counted per guest.

    value_retained is the predicted CLV of guests who came back — a prediction,
    not booked revenue.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    res = (_client().table("action_logs").select("guest_id, outcome").eq("action_status", "Completed")
           .gte("logged_at", since).execute())
    recent = pd.DataFrame(_rows(res), columns=["guest_id", "outcome"])
    contacted = recent["guest_id"].nunique()
    came_back = recent.loc[recent["outcome"] == "Came back", "guest_id"].unique()
    no_return = recent.loc[recent["outcome"] == "Didn't come back", "guest_id"].unique()
    waiting = recent.loc[recent["outcome"] == "Waiting", "guest_id"].unique()
    clv = guests().set_index("guest_id")["predicted_clv"]
    return {
        "days": days,
        "contacted": int(contacted),
        "came_back": len(came_back),
        "did_not": len(no_return),
        "waiting": len(waiting),
        "return_rate": (len(came_back) / contacted) if contacted else 0.0,
        "value_retained": int(clv.reindex(came_back).fillna(0).sum()),
    }
