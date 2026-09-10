"""
Hardcoded/dummy data for frontend-first development.
Field names mirror the GUESTS / CLV_PREDICTIONS / ACTION_LOGS Supabase schema
so swapping this for real Supabase queries later is a drop-in replacement.
"""

# ---- Top-level dashboard stats (Action Board summary cards) ----
DASHBOARD_STATS = {
    "total_guests": 12480,
    "high_value_guests": 1842,
    "at_risk_high_value": 326,
    "avg_predicted_clv": 84600,
    "model_updated": "12 Jun 2025",
    "active_model": "XGBoost",
}

TIER_COLORS = {"Platinum": "blue", "High": "green", "Medium": "orange", "Low": "red"}
RISK_COLORS = {"High Risk": "red", "Medium Risk": "orange", "Low Risk": "green"}

# ---- Action Board guest list ----
ACTION_BOARD_GUESTS = [
    {"guest_id": "G-11244", "clv_tier": "High", "predicted_clv": 612900,
     "recommended_action": "VIP concierge outreach", "days_since_last_stay": 8},
    {"guest_id": "G-10234", "clv_tier": "Platinum", "predicted_clv": 485200,
     "recommended_action": "Upsell suite package", "days_since_last_stay": 12},
    {"guest_id": "G-12881", "clv_tier": "High", "predicted_clv": 421500,
     "recommended_action": "VIP concierge outreach", "days_since_last_stay": 22},
    {"guest_id": "G-10567", "clv_tier": "High", "predicted_clv": 310750,
     "recommended_action": "Send loyalty offer", "days_since_last_stay": 45},
    {"guest_id": "G-11578", "clv_tier": "High", "predicted_clv": 278600,
     "recommended_action": "Send loyalty offer", "days_since_last_stay": 60},
    {"guest_id": "G-12091", "clv_tier": "Medium", "predicted_clv": 235400,
     "recommended_action": "Re-engagement email", "days_since_last_stay": 83},
    {"guest_id": "G-13102", "clv_tier": "Medium", "predicted_clv": 198200,
     "recommended_action": "Re-engagement email", "days_since_last_stay": 71},
    {"guest_id": "G-10891", "clv_tier": "Medium", "predicted_clv": 88400,
     "recommended_action": "Re-engagement email", "days_since_last_stay": 120},
    {"guest_id": "G-11820", "clv_tier": "Medium", "predicted_clv": 65100,
     "recommended_action": "Re-engagement email", "days_since_last_stay": 150},
    {"guest_id": "G-11023", "clv_tier": "Low", "predicted_clv": 24300,
     "recommended_action": "Win-back discount", "days_since_last_stay": 210},
]
TOTAL_ACTION_BOARD_ROWS = 336

# ---- At-risk guests ----
AT_RISK_GUESTS = [
    {"guest_id": "G-10234", "predicted_clv": 485200, "days_since_last_stay": 94,
     "prev_stays": 18, "risk_level": "High Risk", "recommended_action": "Personal call from manager"},
    {"guest_id": "G-11244", "predicted_clv": 412900, "days_since_last_stay": 78,
     "prev_stays": 14, "risk_level": "High Risk", "recommended_action": "Send VIP win-back offer"},
    {"guest_id": "G-10567", "predicted_clv": 310750, "days_since_last_stay": 112,
     "prev_stays": 11, "risk_level": "High Risk", "recommended_action": "Send VIP win-back offer"},
    {"guest_id": "G-11578", "predicted_clv": 278600, "days_since_last_stay": 65,
     "prev_stays": 9, "risk_level": "Medium Risk", "recommended_action": "Email loyalty bonus"},
    {"guest_id": "G-12091", "predicted_clv": 192400, "days_since_last_stay": 83,
     "prev_stays": 7, "risk_level": "Medium Risk", "recommended_action": "Priority retention campaign"},
    {"guest_id": "G-12344", "predicted_clv": 165100, "days_since_last_stay": 71,
     "prev_stays": 6, "risk_level": "Medium Risk", "recommended_action": "Email loyalty bonus"},
    {"guest_id": "G-12820", "predicted_clv": 152700, "days_since_last_stay": 98,
     "prev_stays": 5, "risk_level": "High Risk", "recommended_action": "Send VIP win-back offer"},
    {"guest_id": "G-13023", "predicted_clv": 148300, "days_since_last_stay": 68,
     "prev_stays": 5, "risk_level": "Low Risk", "recommended_action": "Re-engagement offer"},
]
TOTAL_AT_RISK_ROWS = 328

# ---- Full guest profile detail for Guest Lookup screen (keyed by guest_id) ----
GUEST_PROFILES = {
    "G-10234": {
        "guest_id": "G-10234",
        "guest_email": "guest10234@example.com",
        "total_previous_stays": 18,
        "avg_daily_rate": 22400,
        "avg_length_of_stay": 4.2,
        "cancellation_rate": 4,
        "booking_lead_time": 14,
        "booking_channel": "Direct / Website",
        "is_repeat_guest": True,
        "days_since_last_stay": 12,
        "predicted_clv": 485200,
        "clv_tier": "High",
        "tier_badge": "Platinum",
        "recommended_action": "VIP concierge outreach",
        "recommended_action_reason": "High predicted CLV and strong repeat-visit behaviour.",
        "behavioural_insights": {
            "Repeat Visits": {"value": "18 stays", "label": "Strong loyalty"},
            "Spending Behaviour": {"value": "Above avg ADR", "label": "Premium spender"},
            "Cancellation": {"value": "4% rate", "label": "Very low"},
            "Booking Frequency": {"value": "Every 42 days", "label": "High frequency"},
            "Recency": {"value": "12 days ago", "label": "Recently active"},
            "Booking Channel": {"value": "Direct / Web", "label": "High margin"},
        },
        "prediction_drivers": [
            ("Repeat Visits", 92), ("Average Daily Rate", 78), ("Length of Stay", 65),
            ("Booking Lead Time", 50), ("Cancellation Rate", 30),
        ],
        "historical_stays": [
            {"date": "Jun 2025", "nights": 5, "amount": 24500, "room_type": "Executive Suite"},
            {"date": "Dec 2024", "nights": 4, "amount": 21800, "room_type": "Deluxe Room"},
            {"date": "Aug 2024", "nights": 6, "amount": 23200, "room_type": "Executive Suite"},
            {"date": "Mar 2024", "nights": 3, "amount": 19900, "room_type": "Standard Room"},
        ],
        "earlier_stays_count": 14,
        "action_logs": [
            {"action_taken": "VIP concierge outreach", "channel": "Email", "status": "Completed",
             "timestamp": "12 Jun 2025, 09:14", "user": "Marketing Team"},
        ],
    },
}

# ---- Model Performance page ----
MODEL_COMPARISON = {
    "metrics": ["MAE (KSh)", "RMSE (KSh)", "R\u00b2", "Cross-Val R\u00b2 (5-fold)"],
    "random_forest": [12840, 21390, 0.812, 0.798],
    "xgboost": [9620, 16480, 0.871, 0.856],
}

FEATURE_IMPORTANCE = [
    ("Repeat Visits", 92), ("Average Daily Rate", 85), ("Length of Stay", 74),
    ("Previous Stays", 68), ("Spending Behaviour", 61), ("Booking Lead Time", 48),
    ("Booking Channel", 40), ("Cancellation Rate", 32),
]

ACTUAL_VS_PREDICTED = [
    (10000, 9800), (25000, 26500), (40000, 38200), (60000, 62100),
    (85000, 83000), (110000, 115400), (150000, 147800), (180000, 185600),
    (220000, 216300), (270000, 275900), (320000, 315200), (380000, 388400),
    (450000, 442100), (500000, 495000),
]

SEGMENT_TIMELINE = {
    "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "High": [1500, 1580, 1620, 1690, 1750, 1842],
    "Medium": [4200, 4150, 4300, 4280, 4350, 4400],
    "Low": [6500, 6480, 6400, 6350, 6300, 6238],
}
