import pandas as pd

DUMMY_GUESTS = pd.DataFrame([
    {"guest_id": "G001", "guest_email": "jane.doe@example.com", "total_previous_stays": 12,
     "avg_daily_rate": 145.50, "avg_length_of_stay": 3.2, "booking_lead_time": 21,
     "cancellation_rate": 0.05, "booking_channel": "Direct", "is_repeat_guest": True,
     "last_stay_date": "2026-06-15", "predicted_clv": 48500, "clv_tier": "High",
     "recommended_action": "Send loyalty offer"},
    {"guest_id": "G002", "guest_email": "amina.k@example.com", "total_previous_stays": 3,
     "avg_daily_rate": 98.00, "avg_length_of_stay": 1.8, "booking_lead_time": 45,
     "cancellation_rate": 0.20, "booking_channel": "Online TA", "is_repeat_guest": False,
     "last_stay_date": "2026-03-02", "predicted_clv": 12300, "clv_tier": "Medium",
     "recommended_action": "Send re-engagement email"},
    {"guest_id": "G003", "guest_email": "brian.o@example.com", "total_previous_stays": 1,
     "avg_daily_rate": 60.00, "avg_length_of_stay": 1.0, "booking_lead_time": 10,
     "cancellation_rate": 0.40, "booking_channel": "Corporate", "is_repeat_guest": False,
     "last_stay_date": "2025-11-20", "predicted_clv": 3100, "clv_tier": "Low",
     "recommended_action": "No action needed"},
])
