"""
Data access for the dashboard views.

Views call only these functions. Today they read the mock tables in
data/mock_data.py; Phase 3 replaces the bodies with Supabase queries against
GUESTS, CLV_PREDICTIONS, ACTION_LOGS and APP_SETTINGS without touching the views.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from data import mock_data

TIERS = ["High", "Medium", "Low"]
PLATINUM_MIN_CLV = 400_000        # High-tier guests shown with a Platinum badge
AT_RISK_DEFAULT_DAYS = mock_data.AT_RISK_DAYS
AT_RISK_OPTIONS = [30, 60, 90, 120]   # choices offered to the Revenue Manager
OUTCOMES = mock_data.OUTCOMES          # Waiting / Came back / Didn't come back
HIGH_VALUE_MIN_CLV = mock_data.TIER_PLAN["High"]["low"]
BOOKING_CHANNELS = mock_data.BOOKING_CHANNELS
GUEST_TYPES = mock_data.GUEST_TYPES

# Change vs previous prediction run, per tier (shown on Segments cards).
TIER_TREND = {"High": ("up", "+8% vs prev. period"),
              "Medium": ("flat", "Stable vs prev. period"),
              "Low": ("down", "-3% vs prev. period")}
TIER_STRATEGY = {
    "High": "Priority retention / loyalty incentives / personalised service",
    "Medium": "Targeted re-engagement / upselling",
    "Low": "Cost-efficient engagement / win-back offers",
}


@st.cache_data(show_spinner=False)
def _tables() -> dict[str, pd.DataFrame]:
    return mock_data.build()


@st.cache_data(show_spinner=False)
def guests() -> pd.DataFrame:
    """GUESTS joined to each guest's latest CLV_PREDICTIONS row."""
    t = _tables()
    latest = (t["clv_predictions"].sort_values("predicted_at")
              .drop_duplicates("guest_id", keep="last"))
    df = t["guests"].merge(latest, on="guest_id", how="inner")
    df["tier_badge"] = df["clv_tier"].where(
        ~((df["clv_tier"] == "High") & (df["predicted_clv"] >= PLATINUM_MIN_CLV)), "Platinum")
    df["clv_percentile"] = df["predicted_clv"].rank(pct=True)
    return df


# ---------------------------------------------------------------------------
# APP_SETTINGS — shared by every user (a process-wide store stands in for the
# Supabase table until Phase 3).
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _settings() -> dict:
    return {"at_risk_days": AT_RISK_DEFAULT_DAYS, "updated_by": None, "updated_at": None}


def at_risk_days() -> int:
    """Days without a stay after which a High-tier guest counts as at-risk."""
    return int(_settings()["at_risk_days"])


def set_at_risk_days(days: int) -> None:
    """Revenue Manager only (enforced by the page now, by RLS in Phase 3)."""
    if days not in AT_RISK_OPTIONS:
        raise ValueError(f"Unsupported threshold: {days}")
    _settings().update(at_risk_days=days, updated_by=st.session_state.get("full_name"),
                       updated_at=datetime.now().replace(microsecond=0))


def settings_meta() -> dict:
    return dict(_settings())


def risk_level(days: int, threshold: int) -> str:
    """How far past the threshold a guest is: 30+ days over → High, 10+ → Medium."""
    if days >= threshold + 30:
        return "High Risk"
    if days >= threshold + 10:
        return "Medium Risk"
    return "Low Risk"


@dataclass(frozen=True)
class ModelMeta:
    model_used: str
    predicted_at: datetime

    @property
    def updated_label(self) -> str:
        return f"{self.predicted_at.day} {self.predicted_at:%b %Y}"


def model_meta() -> ModelMeta:
    p = _tables()["clv_predictions"]
    return ModelMeta(p["model_used"].iloc[-1], p["predicted_at"].max())


def overview() -> dict:
    df = guests()
    return {
        "total_guests": len(df),
        "high_value_guests": int((df["clv_tier"] == "High").sum()),
        "at_risk_high_value": int(((df["clv_tier"] == "High") & (df["days_since_last_stay"] >= at_risk_days())).sum()),
        "avg_predicted_clv": int(round(df["predicted_clv"].mean(), -2)),
    }


def action_queue() -> pd.DataFrame:
    """Guests on the Action Board, highest predicted CLV first."""
    df = guests()
    return df[df["in_action_queue"]].sort_values("predicted_clv", ascending=False)


def at_risk(min_clv: int = HIGH_VALUE_MIN_CLV, min_days: int | None = None) -> pd.DataFrame:
    """High-tier guests inactive for at least min_days (default: the shared threshold)."""
    threshold = at_risk_days()
    df = guests()
    mask = ((df["clv_tier"] == "High") & (df["predicted_clv"] >= min_clv)
            & (df["days_since_last_stay"] >= (min_days or threshold)))
    out = df[mask].copy()
    out["risk_level"] = out["days_since_last_stay"].map(lambda d: risk_level(d, threshold))
    return out


def get_guest(guest_id: str) -> pd.Series | None:
    df = guests()
    hit = df[df["guest_id"] == guest_id]
    return None if hit.empty else hit.iloc[0]


def normalize_guest_id(raw: str) -> str:
    """Accept 'g-10234', 'G10234' or '10234'."""
    s = (raw or "").strip().upper().replace(" ", "")
    if s.startswith("G-"):
        s = s[2:]
    elif s.startswith("G"):
        s = s[1:]
    return f"G-{s}" if s.isdigit() else (raw or "").strip().upper()


def stay_history(g: pd.Series) -> list[dict]:
    return mock_data.stay_history(g["guest_id"], int(g["total_previous_stays"]), int(g["avg_daily_rate"]),
                                  float(g["avg_length_of_stay"]), int(g["days_since_last_stay"]))


def prediction_drivers(guest_id: str) -> list[tuple[str, int]]:
    return mock_data.prediction_drivers(guest_id)


def tier_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Guests per tier by first booking year (rows = years, columns = tiers)."""
    out = df.pivot_table(index="first_booking_year", columns="clv_tier", values="guest_id",
                         aggfunc="count", fill_value=0)
    return out.reindex(columns=TIERS, fill_value=0).sort_index()


def segment_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("clv_tier").agg(
        guests=("guest_id", "count"),
        avg_clv=("predicted_clv", "mean"),
        avg_stays=("total_previous_stays", "mean"),
        avg_adr=("avg_daily_rate", "mean"),
        avg_days=("days_since_last_stay", "mean"),
    ).reindex(TIERS)
    g["strategy"] = [TIER_STRATEGY[t] for t in g.index]
    return g


# ---------------------------------------------------------------------------
# ACTION_LOGS — kept in the browser session until Phase 3 writes to Supabase.
# ---------------------------------------------------------------------------

def _log_store() -> pd.DataFrame:
    if "_action_logs" not in st.session_state:
        st.session_state["_action_logs"] = _tables()["action_logs"].copy()
    return st.session_state["_action_logs"]


def action_logs(guest_id: str) -> pd.DataFrame:
    logs = _log_store()
    return logs[logs["guest_id"] == guest_id].sort_values("logged_at", ascending=False)


def log_action(guest_id: str, action_taken: str, delivery_channel: str,
               action_status: str = "Completed") -> None:
    """Record an action. Completed actions start with outcome 'Waiting'."""
    logs = _log_store()
    s = st.session_state
    row = {
        "log_id": int(logs["log_id"].max()) + 1 if len(logs) else 1,
        "user_id": s.get("user_id"),
        "user_name": s.get("full_name") or "",
        "user_role": s.get("role"),
        "guest_id": guest_id,
        "action_taken": action_taken,
        "action_status": action_status,
        "delivery_channel": delivery_channel,
        "logged_at": datetime.now().replace(microsecond=0),
        "outcome": "Waiting" if action_status == "Completed" else None,
        "outcome_at": None,
    }
    st.session_state["_action_logs"] = pd.concat([logs, pd.DataFrame([row])], ignore_index=True)


def set_outcome(log_id: int, outcome: str) -> None:
    """Record whether the guest came back after a completed action."""
    if outcome not in OUTCOMES:
        raise ValueError(f"Unknown outcome: {outcome}")
    logs = _log_store()
    i = logs.index[logs["log_id"] == log_id]
    logs.loc[i, "outcome"] = outcome
    logs.loc[i, "outcome_at"] = None if outcome == "Waiting" else datetime.now().replace(microsecond=0)


def outcome_summary(days: int = 30) -> dict:
    """Completed actions in the last `days` days, counted per guest.

    value_retained is the predicted CLV of guests who came back — a prediction,
    not booked revenue.
    """
    logs = _log_store()
    recent = logs[(logs["action_status"] == "Completed")
                  & (logs["logged_at"] >= datetime.now() - timedelta(days=days))]
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
