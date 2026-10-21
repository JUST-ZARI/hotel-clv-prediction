"""
Live CLV prediction for one booking, with the saved XGBoost model.

The 28 model inputs are rebuilt exactly as in notebook 05 (same label
encodings, caps and KSh conversion, read from preprocessing_metadata.json),
so the same booking always gives the same prediction. Inputs are validated
first: impossible bookings are rejected, unusual ones are flagged.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "xgboost.json"
META_PATH = ROOT / "data" / "processed" / "preprocessing_metadata.json"
CLEANED_PATH = ROOT / "data" / "processed" / "cleaned_dataset.csv"

FEATURE_LABELS = {
    "lead_time": "Booking lead time", "arrival_year": "Arrival year", "arrival_month": "Arrival month",
    "stays_weekend_nights": "Weekend nights", "stays_week_nights": "Week nights", "total_nights": "Length of stay",
    "num_adults": "Adults", "num_children": "Children", "num_babies": "Babies", "total_guests": "Party size",
    "adr_ksh": "Average daily rate", "is_repeated_guest": "Repeat guest",
    "previous_cancellations": "Previous cancellations", "previous_bookings_not_canceled": "Previous stays",
    "hist_cancellation_rate": "Cancellation rate", "has_previous_bookings": "Has stayed before",
    "booking_changes": "Booking changes", "required_car_parking_spaces": "Parking requested",
    "total_special_requests": "Special requests", "has_agent": "Booked through an agent",
    "has_company": "Company booking", "booking_channel_enc": "Booking channel",
    "room_type_reserved_enc": "Room type", "deposit_type_enc": "Deposit type",
    "market_segment_enc": "Market segment", "meal_plan_enc": "Meal plan",
    "customer_type_enc": "Guest type", "hotel_type_enc": "Hotel type",
}
CATEGORICAL = ["booking_channel", "room_type_reserved", "deposit_type", "market_segment", "meal_plan",
               "customer_type", "hotel_type"]


@st.cache_resource(show_spinner="Loading the prediction model…")
def _model():
    import xgboost

    booster = xgboost.Booster()
    booster.load_model(str(MODEL_PATH))
    return booster


@st.cache_data(show_spinner=False)
def meta() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def options(column: str) -> list[str]:
    """Allowed values of a categorical input (the categories the model was trained on)."""
    return list(meta()["label_encodings"][column])


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

@dataclass
class Booking:
    hotel_type: str = "City Hotel"
    arrival: date = field(default_factory=lambda: date(2018, 8, 15))
    weekend_nights: int = 1
    week_nights: int = 2
    adults: int = 2
    children: int = 0
    babies: int = 0
    adr_ksh: float = 15_000.0
    lead_time: int = 30
    meal_plan: str = "BB"
    room_type: str = "A"
    market_segment: str = "Online TA"
    booking_channel: str = "TA/TO"
    deposit_type: str = "No Deposit"
    customer_type: str = "Transient"
    booked_through_agent: bool = True
    company_booking: bool = False
    booking_changes: int = 0
    special_requests: int = 0
    parking_spaces: int = 0
    repeat_guest: bool = False
    previous_stays: int = 0
    previous_cancellations: int = 0
    days_since_last_stay: int = 0

    def fingerprint(self) -> str:
        """Short ID of these exact inputs: the same booking always has the same fingerprint."""
        return hashlib.sha256(json.dumps(self.__dict__, default=str, sort_keys=True).encode()).hexdigest()[:10]


def validate(b: Booking) -> tuple[list[str], list[str]]:
    """(errors, warnings). Errors = impossible booking (rejected); warnings = unusual but allowed."""
    errors, warnings = [], []
    counts = {"Weekend nights": b.weekend_nights, "Week nights": b.week_nights, "Adults": b.adults,
              "Children": b.children, "Babies": b.babies, "Lead time": b.lead_time,
              "Booking changes": b.booking_changes, "Special requests": b.special_requests,
              "Parking spaces": b.parking_spaces, "Previous stays": b.previous_stays,
              "Previous cancellations": b.previous_cancellations, "Days since last stay": b.days_since_last_stay}
    for name, v in counts.items():
        if v is None or v < 0:
            errors.append(f"{name} cannot be negative.")
        elif float(v) != int(v):
            errors.append(f"{name} must be a whole number.")
    if b.adr_ksh is None or b.adr_ksh <= 0:
        errors.append("The daily rate must be more than KSh 0 — a paid stay cannot be free or negative.")
    if (b.weekend_nights or 0) + (b.week_nights or 0) < 1:
        errors.append("A stay must have at least one night.")
    if (b.adults or 0) < 1:
        errors.append("A booking needs at least one adult.")
    if (b.adults or 0) > 60 or (b.children or 0) > 20 or (b.babies or 0) > 10:
        errors.append("The number of guests is not realistic for one booking.")
    if (b.lead_time or 0) > 730:
        errors.append("Lead time over two years is not a realistic booking.")
    if (b.weekend_nights or 0) + (b.week_nights or 0) > 90:
        errors.append("Stays longer than 90 nights are not hotel bookings.")
    if (b.special_requests or 0) > 10 or (b.parking_spaces or 0) > 10 or (b.booking_changes or 0) > 50:
        errors.append("Special requests, parking spaces or booking changes are unrealistically high.")
    if not b.repeat_guest and (b.previous_stays or 0) > 0:
        errors.append("A guest with previous stays is a repeat guest — tick “Repeat guest”.")
    for col, value in [("hotel_type", b.hotel_type), ("meal_plan", b.meal_plan), ("room_type_reserved", b.room_type),
                       ("market_segment", b.market_segment), ("booking_channel", b.booking_channel),
                       ("deposit_type", b.deposit_type), ("customer_type", b.customer_type)]:
        if value not in options(col):
            errors.append(f"“{value}” is not a known {col.replace('_', ' ')}.")
    if errors:
        return errors, warnings

    m = meta()
    cap_ksh = m["caps"]["adr_eur"] * m["currency"]["eur_to_ksh"]
    if b.adr_ksh > cap_ksh:
        warnings.append(f"Daily rate above KSh {cap_ksh:,.0f} is treated as KSh {cap_ksh:,.0f}, the highest rate "
                        "the model learned from.")
    if b.lead_time > m["caps"]["lead_time_days"]:
        warnings.append(f"Lead time above {m['caps']['lead_time_days']:.0f} days is treated as "
                        f"{m['caps']['lead_time_days']:.0f}, as in training.")
    if not 2015 <= b.arrival.year <= 2018:
        warnings.append("The model learned from 2015–2018 bookings; for other years it uses the nearest year's "
                        "patterns.")
    if b.weekend_nights + b.week_nights > 30 or b.previous_stays > 72 or b.adults > 4:
        warnings.append("Some values are far outside typical bookings, so the prediction is less certain.")
    return errors, warnings


def features(b: Booking) -> pd.DataFrame:
    """The 28 model inputs, built exactly as in preprocessing (notebook 05)."""
    m = meta()
    enc = m["label_encodings"]
    adr_eur = min(b.adr_ksh / m["currency"]["eur_to_ksh"], m["caps"]["adr_eur"])
    prev_total = b.previous_stays + b.previous_cancellations
    row = {
        "lead_time": min(b.lead_time, m["caps"]["lead_time_days"]),
        "arrival_year": b.arrival.year,
        "arrival_month": b.arrival.month,
        "stays_weekend_nights": b.weekend_nights,
        "stays_week_nights": b.week_nights,
        "total_nights": b.weekend_nights + b.week_nights,
        "num_adults": b.adults,
        "num_children": b.children,
        "num_babies": b.babies,
        "total_guests": b.adults + b.children + b.babies,
        "adr_ksh": adr_eur * m["currency"]["eur_to_ksh"],
        "is_repeated_guest": int(b.repeat_guest),
        "previous_cancellations": b.previous_cancellations,
        "previous_bookings_not_canceled": b.previous_stays,
        "hist_cancellation_rate": round(b.previous_cancellations / prev_total, 4) if prev_total else 0.0,
        "has_previous_bookings": int(b.previous_stays > 0),
        "booking_changes": b.booking_changes,
        "required_car_parking_spaces": b.parking_spaces,
        "total_special_requests": b.special_requests,
        "has_agent": int(b.booked_through_agent),
        "has_company": int(b.company_booking),
        "booking_channel_enc": enc["booking_channel"][b.booking_channel],
        "room_type_reserved_enc": enc["room_type_reserved"][b.room_type],
        "deposit_type_enc": enc["deposit_type"][b.deposit_type],
        "market_segment_enc": enc["market_segment"][b.market_segment],
        "meal_plan_enc": enc["meal_plan"][b.meal_plan],
        "customer_type_enc": enc["customer_type"][b.customer_type],
        "hotel_type_enc": enc["hotel_type"][b.hotel_type],
    }
    return pd.DataFrame([row], columns=m["features"]).astype(float)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def recommend(tier: str, platinum: bool, days: int, at_risk_days: int) -> tuple[str, str]:
    """Same rules as notebook 08 (first match wins)."""
    past, far = days >= at_risk_days, days >= at_risk_days + 30
    if tier == "High":
        if far and platinum:
            return "Personal call from manager", "Top-value guest with no stay for a long time."
        if far:
            return "Send VIP win-back offer", "High predicted CLV but no stay for a long time."
        if past and platinum:
            return "Priority retention campaign", "Top-value guest now at risk of not returning."
        if past:
            return "Email loyalty bonus", "High-value guest showing reduced visit frequency."
        if days < 30:
            return "VIP concierge outreach", "High predicted CLV and a recent stay."
        if platinum:
            return "Upsell suite package", "Premium guest with a recent stay; strong upsell potential."
        return "Send loyalty offer", "High predicted CLV; reinforce loyalty before the next booking."
    if tier == "Medium":
        if days < 90:
            return "Targeted upsell offer", "Moderate value with recent activity; room to grow spend."
        return "Re-engagement email", "Moderate value but no recent stay."
    if days < 120:
        return "Cost-efficient engagement", "Low predicted CLV; keep contact low-cost."
    return "Win-back discount", "Low predicted CLV and a long time since the last stay."


def predict(b: Booking, high_min: float, low_max: float, platinum_min: float, at_risk_days: int) -> dict:
    """Predicted CLV, tier, badge, top-5 drivers and recommended action for a valid booking."""
    import xgboost

    x = features(b)
    dm = xgboost.DMatrix(x, feature_names=list(x.columns))
    booster = _model()
    clv = max(0.0, float(booster.predict(dm)[0]))
    contrib = booster.predict(dm, pred_contribs=True)[0][:-1]
    share = 100 * np.abs(contrib) / max(np.abs(contrib).sum(), 1e-9)
    order = np.argsort(-np.abs(contrib))[:5]
    drivers = [(FEATURE_LABELS[x.columns[j]], round(float(share[j]), 1), "up" if contrib[j] >= 0 else "down")
               for j in order]
    tier = "High" if clv >= high_min else "Low" if clv <= low_max else "Medium"
    platinum = tier == "High" and clv >= platinum_min
    action, reason = recommend(tier, platinum, b.days_since_last_stay, at_risk_days)
    return {"clv": round(clv, 2), "tier": tier, "badge": "Platinum" if platinum else tier, "drivers": drivers,
            "action": action, "reason": reason, "fingerprint": b.fingerprint()}


# ---------------------------------------------------------------------------
# Start from an existing guest's booking
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading booking records…", max_entries=1)
def _bookings() -> pd.DataFrame:
    cols = ["guest_id", "hotel_type", "arrival_date", "stays_weekend_nights", "stays_week_nights", "num_adults",
            "num_children", "num_babies", "adr_ksh", "lead_time", "meal_plan", "room_type_reserved",
            "market_segment", "booking_channel", "deposit_type", "customer_type", "has_agent", "has_company",
            "booking_changes", "total_special_requests", "required_car_parking_spaces", "is_repeated_guest",
            "previous_bookings_not_canceled", "previous_cancellations"]
    return pd.read_csv(CLEANED_PATH, usecols=cols).set_index("guest_id")


def booking_of(guest_id: str, days_since_last_stay: int = 0) -> Booking | None:
    """The guest's booking from the cleaned dataset, as editable inputs."""
    df = _bookings()
    if guest_id not in df.index:
        return None
    r = df.loc[guest_id]
    return Booking(
        hotel_type=r.hotel_type, arrival=pd.Timestamp(r.arrival_date).date(),
        weekend_nights=int(r.stays_weekend_nights), week_nights=int(r.stays_week_nights),
        adults=int(r.num_adults), children=int(r.num_children), babies=int(r.num_babies),
        adr_ksh=float(r.adr_ksh), lead_time=int(r.lead_time), meal_plan=r.meal_plan,
        room_type=r.room_type_reserved, market_segment=r.market_segment, booking_channel=r.booking_channel,
        deposit_type=r.deposit_type, customer_type=r.customer_type, booked_through_agent=bool(r.has_agent),
        company_booking=bool(r.has_company), booking_changes=int(r.booking_changes),
        special_requests=int(r.total_special_requests), parking_spaces=int(r.required_car_parking_spaces),
        repeat_guest=bool(r.is_repeated_guest), previous_stays=int(r.previous_bookings_not_canceled),
        previous_cancellations=int(r.previous_cancellations), days_since_last_stay=days_since_last_stay)
