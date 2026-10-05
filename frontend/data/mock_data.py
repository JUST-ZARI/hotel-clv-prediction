"""
Deterministic mock data shaped like the planned Supabase tables.

    GUESTS           one row per guest (booking-behaviour features)
    CLV_PREDICTIONS  one row per guest per model run (guest_id FK)
    ACTION_LOGS      one row per action taken (guest_id FK, user_id FK)

Column names match the planned schema so data/repository.py can swap these
frames for Supabase queries without the views changing.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

SEED = 20250612
MODEL_USED = "XGBoost"
PREDICTED_AT = datetime(2025, 6, 12, 6, 0)

# Guest counts and mean predicted CLV per tier (KSh).
TIER_PLAN = {
    "High":   {"count": 1842, "mean": 284_600, "low": 150_000, "high": 650_000},
    "Medium": {"count": 4210, "mean": 78_200,  "low": 50_000,  "high": 149_999},
    "Low":    {"count": 6428, "mean": 18_400,  "low": 2_000,   "high": 49_999},
}
AT_RISK_DAYS = 60          # inactivity threshold for "at-risk"
AT_RISK_HIGH_VALUE = 326   # High-tier guests beyond the threshold
ACTION_QUEUE_SIZE = 336    # guests currently on the Action Board
QUEUE_AT_RISK_SHARE = 120  # of which at-risk High guests

BOOKING_CHANNELS = ["Direct / Website", "Online TA", "Offline TA/TO", "Corporate", "Groups"]
GUEST_TYPES = ["Transient", "Transient-Party", "Contract", "Group"]
ROOM_TYPES = ["Standard Room", "Deluxe Room", "Executive Suite", "Junior Suite"]


def _clv_values(rng, n, mean, low, high):
    """Right-skewed values inside [low, high] whose mean is `mean`."""
    x = rng.lognormal(0, 0.55, n)
    x = low + (x / x.mean()) * (mean - low)
    x = np.clip(x, low, high)
    x = low + (x - low) * (mean - low) / (x.mean() - low)   # re-centre after clipping
    return np.clip(np.round(x, -2), low, high).astype(int)


def recommend(tier: str, clv: int, days: int) -> tuple[str, str]:
    """Rule-based recommended action + reason, as the prediction job will store it."""
    if tier == "High":
        if days >= 90:
            if clv >= 400_000:
                return "Personal call from manager", "Top-value guest inactive for 90+ days."
            return "Send VIP win-back offer", "High predicted CLV but inactive for 90+ days."
        if days >= AT_RISK_DAYS:
            if clv >= 250_000:
                return "Priority retention campaign", "High-value guest approaching churn risk."
            return "Email loyalty bonus", "High-value guest showing reduced visit frequency."
        if days < 30:
            return "VIP concierge outreach", "High predicted CLV and strong repeat-visit behaviour."
        if clv >= 400_000:
            return "Upsell suite package", "Premium spender with recent stays; strong upsell potential."
        return "Send loyalty offer", "High predicted CLV; reinforce loyalty before the next booking."
    if tier == "Medium":
        if days < 90:
            return "Targeted upsell offer", "Moderate value with recent activity; room to grow spend."
        return "Re-engagement email", "Moderate value but no recent stay."
    if days < 120:
        return "Cost-efficient engagement", "Low predicted CLV; keep contact low-cost."
    return "Win-back discount", "Low predicted CLV and long inactivity."


def build() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    n = sum(p["count"] for p in TIER_PLAN.values())

    tiers = np.concatenate([[t] * p["count"] for t, p in TIER_PLAN.items()])
    clv = np.concatenate([
        _clv_values(rng, p["count"], p["mean"], p["low"], p["high"]) for p in TIER_PLAN.values()
    ])
    order = rng.permutation(n)
    tiers, clv = tiers[order], clv[order]

    # G-10234 is the wireframe's reference guest: make sure that slot holds a High guest.
    ref = 234
    if tiers[ref] != "High":
        j = np.flatnonzero(tiers == "High")[0]
        tiers[[ref, j]], clv[[ref, j]] = tiers[[j, ref]], clv[[j, ref]]
    clv[ref] = 485_200

    # Recency: exactly AT_RISK_HIGH_VALUE High-tier guests beyond the threshold.
    days = np.empty(n, dtype=int)
    high_idx = np.flatnonzero(tiers == "High")
    at_risk = rng.choice(high_idx[high_idx != ref], AT_RISK_HIGH_VALUE, replace=False)
    days[high_idx] = rng.integers(3, AT_RISK_DAYS, high_idx.size)
    days[at_risk] = rng.integers(AT_RISK_DAYS, 181, at_risk.size)
    med_idx = np.flatnonzero(tiers == "Medium")
    low_idx = np.flatnonzero(tiers == "Low")
    days[med_idx] = rng.integers(5, 240, med_idx.size)
    days[low_idx] = rng.integers(20, 400, low_idx.size)

    scale = np.select([tiers == "High", tiers == "Medium"], [1.0, 0.55], 0.25)
    stays = np.maximum(1, np.round(rng.gamma(2.2, 3.2, n) * scale + (tiers == "High") * 4)).astype(int)
    adr = np.round(rng.normal(8_000, 1_800, n) + scale * 12_000, -2).astype(int)
    los = np.round(np.clip(rng.normal(2.4 + scale * 1.8, 0.8, n), 1, 9), 1)
    cancel = np.clip(np.round(rng.beta(2, 9, n) * 100 * (1.2 - scale * 0.8)), 0, 60).astype(int)
    lead = np.clip(np.round(rng.gamma(2.0, 22, n)), 0, 365).astype(int)
    channel_p = np.array([[.40, .25, .10, .20, .05], [.25, .40, .15, .12, .08], [.12, .50, .18, .08, .12]])
    tier_row = np.select([tiers == "High", tiers == "Medium"], [0, 1], 2)
    channel = np.array([rng.choice(BOOKING_CHANNELS, p=channel_p[r]) for r in tier_row])
    gtype = rng.choice(GUEST_TYPES, n, p=[.62, .22, .10, .06])
    first_year = rng.choice(np.arange(2017, 2024), n, p=[.20, .17, .13, .09, .12, .14, .15])

    ids = [f"G-{10000 + i}" for i in range(n)]
    guests = pd.DataFrame({
        "guest_id": ids,
        "total_previous_stays": stays,
        "avg_daily_rate": adr,
        "avg_length_of_stay": los,
        "cancellation_rate": cancel,
        "booking_lead_time": lead,
        "booking_channel": channel,
        "guest_type": gtype,
        "is_repeat_guest": stays > 1,
        "days_since_last_stay": days,
        "first_booking_year": first_year,
    })

    # Pin the reference guest's profile to the wireframe values.
    guests.loc[ref, ["total_previous_stays", "avg_daily_rate", "avg_length_of_stay", "cancellation_rate",
                     "booking_lead_time", "booking_channel", "guest_type", "is_repeat_guest",
                     "days_since_last_stay"]] = [18, 22_400, 4.2, 4, 14, "Direct / Website", "Transient", True, 12]

    actions = [recommend(t, int(c), int(d)) for t, c, d in zip(tiers, clv, guests.days_since_last_stay)]
    predictions = pd.DataFrame({
        "prediction_id": np.arange(1, n + 1),
        "guest_id": ids,
        "predicted_clv": clv,
        "clv_tier": tiers,
        "recommended_action": [a for a, _ in actions],
        "recommended_action_reason": [r for _, r in actions],
        "model_used": MODEL_USED,
        "predicted_at": PREDICTED_AT,
    })

    # Action Board queue: a slice of at-risk High guests plus guests from every tier.
    queued_risk = rng.choice(at_risk, QUEUE_AT_RISK_SHARE, replace=False)
    others = rng.choice(np.setdiff1d(np.arange(n), np.append(at_risk, ref)),
                        ACTION_QUEUE_SIZE - QUEUE_AT_RISK_SHARE - 1, replace=False)
    in_queue = np.zeros(n, dtype=bool)
    in_queue[np.concatenate([queued_risk, others, [ref]])] = True
    predictions["in_action_queue"] = in_queue

    action_logs = _seed_action_logs(rng, predictions[in_queue])

    return {"guests": guests, "clv_predictions": predictions, "action_logs": action_logs}


OUTCOMES = ["Waiting", "Came back", "Didn't come back"]
CHANNELS = ["Email", "SMS", "Phone call", "Front desk (in-stay)"]
LOG_HISTORY_DAYS = 75     # seeded action history spans this many days back from today
SETTLE_DAYS = 21          # after this long most outcomes are known


def _seed_action_logs(rng, queued: pd.DataFrame) -> pd.DataFrame:
    """Past actions taken by the Marketing Team on Action Board guests, with outcomes."""
    now = datetime.now().replace(second=0, microsecond=0)
    picks = queued.sample(n=min(90, len(queued)), random_state=int(rng.integers(1_000_000)))
    rows = []
    for log_id, (_, p) in enumerate(picks.iterrows(), start=2):
        age = int(rng.integers(0, LOG_HISTORY_DAYS))
        logged_at = now - pd.Timedelta(days=age, hours=int(rng.integers(0, 9)))
        completed = rng.random() > 0.08
        if not completed:
            outcome = None
        elif age >= SETTLE_DAYS:
            outcome = rng.choice(OUTCOMES, p=[0.25, 0.47, 0.28])
        else:
            outcome = rng.choice(OUTCOMES, p=[0.78, 0.18, 0.04])
        rows.append({
            "log_id": log_id, "user_id": None, "user_name": "Marketing Team", "user_role": "marketing",
            "guest_id": p.guest_id, "action_taken": p.recommended_action,
            "action_status": "Completed" if completed else "Pending",
            "delivery_channel": rng.choice(CHANNELS[:3], p=[0.6, 0.25, 0.15]),
            "logged_at": logged_at,
            "outcome": outcome,
            "outcome_at": None if outcome in (None, "Waiting") else logged_at + pd.Timedelta(days=int(rng.integers(3, 20))),
        })
    # The wireframe's reference guest: an earlier concierge outreach that worked.
    rows.append({
        "log_id": 1, "user_id": None, "user_name": "Marketing Team", "user_role": "marketing",
        "guest_id": "G-10234", "action_taken": "VIP concierge outreach", "action_status": "Completed",
        "delivery_channel": "Email", "logged_at": datetime(2025, 6, 12, 9, 14),
        "outcome": "Came back", "outcome_at": datetime(2025, 6, 26, 15, 0),
    })
    return pd.DataFrame(rows).sort_values("logged_at", ignore_index=True)


def stay_history(guest_id: str, stays: int, adr: int, los: float, days_since: int) -> list[dict]:
    """Per-guest stay timeline (most recent first), derived deterministically."""
    rng = np.random.default_rng(int(guest_id[2:]))
    ref = pd.Timestamp(PREDICTED_AT) - pd.Timedelta(days=int(days_since))
    out = []
    for i in range(min(stays, 4)):
        date = ref - pd.Timedelta(days=int(i * rng.integers(60, 200)))
        nights = int(max(1, round(rng.normal(los, 1))))
        out.append({
            "date": date.strftime("%b %Y"),
            "nights": nights,
            "amount": int(round(adr * rng.uniform(0.9, 1.12), -2)),   # nightly rate
            "room_type": ROOM_TYPES[int(rng.integers(0, len(ROOM_TYPES)))],
        })
    return out


FEATURE_LABELS = ["Repeat Visits", "Average Daily Rate", "Length of Stay", "Booking Lead Time", "Cancellation Rate"]


def prediction_drivers(guest_id: str) -> list[tuple[str, int]]:
    """Per-guest feature contributions (%), ordered by strength."""
    if guest_id == "G-10234":
        return list(zip(FEATURE_LABELS, [92, 78, 65, 50, 30]))
    rng = np.random.default_rng(int(guest_id[2:]) + 7)
    vals = np.sort(rng.integers(15, 96, len(FEATURE_LABELS)))[::-1]
    labels = rng.permutation(FEATURE_LABELS)
    return [(str(label), int(v)) for label, v in zip(labels, vals)]
