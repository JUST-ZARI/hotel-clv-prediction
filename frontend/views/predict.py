"""Predict a booking: run the saved XGBoost model live on a new or returning booking.

Scenario tool — nothing is saved. Impossible inputs are rejected before the
model runs; the same inputs always give the same prediction.
"""

from datetime import date

import pandas as pd
import streamlit as st

import charts
import components as ui
import predictor as P
from auth import require_auth
from data import repository as repo
from style import alert, icon

require_auth({"revenue_manager"})
s = st.session_state

ui.page_header("Predict a Booking", "")

FIELDS = list(P.Booking().__dict__)


def _put(b: P.Booking) -> None:
    """Fill the form widgets from a Booking."""
    for k, v in b.__dict__.items():
        s[f"pb_{k}"] = v


def _read() -> P.Booking:
    return P.Booking(**{k: s.get(f"pb_{k}", getattr(P.Booking(), k)) for k in FIELDS})


if "pb_adr_ksh" not in s:
    _put(P.Booking())


def _load_guest() -> None:
    gid = repo.normalize_guest_id(s.get("pb_guest", ""))
    g = repo.get_guest(gid) if gid else None
    b = P.booking_of(gid, int(g["days_since_last_stay"]) if g is not None else 0) if gid else None
    if b is None:
        s["_pb_msg"] = ("warning", f"No booking found for guest “{gid}”.")
        return
    _put(b)
    s["_pb_msg"] = ("success", f"Loaded {gid}'s booking. Change anything and press Predict.")
    s["_pb_run"] = True


def _returning_stay() -> None:
    """The same guest comes back: one more completed stay, so they are now a repeat guest."""
    s["pb_previous_stays"] = int(s.get("pb_previous_stays", 0)) + 1
    s["pb_repeat_guest"] = True
    s["pb_days_since_last_stay"] = 0
    s["_pb_msg"] = ("info", "Added one returning stay: previous stays +1, repeat guest = yes, last stay = today.")
    s["_pb_run"] = True


def _blank() -> None:
    _put(P.Booking())
    s["_pb_msg"] = ("info", "Form reset to a typical booking.")


# ---------------------------------------------------------------------------
# Start from…
# ---------------------------------------------------------------------------
with ui.card("pb_start"):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.text_input("Start from an existing guest (optional)", key="pb_guest", placeholder="Guest ID, e.g. G-000123",
                      width=320)
        st.button("Load guest", on_click=_load_guest, icon=":material/person_search:")
        st.button("Add a returning stay", on_click=_returning_stay, icon=":material/replay:",
                  help="Simulates the same guest coming back once more.")
        st.space("stretch")
        st.button("New blank booking", on_click=_blank, type="tertiary", icon=":material/restart_alt:")
    msg = s.pop("_pb_msg", None)
    if msg:
        alert(*msg)

# ---------------------------------------------------------------------------
# Booking details (numbers are not limited on purpose: impossible values are rejected with a reason)
# ---------------------------------------------------------------------------
with ui.card("pb_form"):
    ui.card_title("Booking details")
    c = st.columns(3, gap="medium")
    with c[0]:
        st.html('<div class="pb-group">Stay</div>')
        st.selectbox("Hotel", P.options("hotel_type"), key="pb_hotel_type")
        st.date_input("Arrival date", key="pb_arrival", min_value=date(2010, 1, 1), max_value=date(2035, 12, 31))
        st.number_input("Weekend nights", key="pb_weekend_nights", step=1)
        st.number_input("Week nights", key="pb_week_nights", step=1)
        st.selectbox("Room type", P.options("room_type_reserved"), key="pb_room_type")
        st.selectbox("Meal plan", P.options("meal_plan"), key="pb_meal_plan",
                     help="BB bed & breakfast · HB half board · FB full board · SC self catering")
    with c[1]:
        st.html('<div class="pb-group">Guests and price</div>')
        st.number_input("Adults", key="pb_adults", step=1)
        st.number_input("Children", key="pb_children", step=1)
        st.number_input("Babies", key="pb_babies", step=1)
        st.number_input("Average daily rate (KSh per night)", key="pb_adr_ksh", step=500.0, format="%.0f")
        st.number_input("Booking lead time (days before arrival)", key="pb_lead_time", step=1)
        st.number_input("Special requests", key="pb_special_requests", step=1)
        st.number_input("Parking spaces", key="pb_parking_spaces", step=1)
    with c[2]:
        st.html('<div class="pb-group">Channel and history</div>')
        st.selectbox("Booking channel", P.options("booking_channel"), key="pb_booking_channel")
        st.selectbox("Market segment", P.options("market_segment"), key="pb_market_segment")
        st.selectbox("Guest type", P.options("customer_type"), key="pb_customer_type")
        st.selectbox("Deposit", P.options("deposit_type"), key="pb_deposit_type")
        st.checkbox("Booked through an agent", key="pb_booked_through_agent")
        st.checkbox("Company booking", key="pb_company_booking")
        st.number_input("Booking changes", key="pb_booking_changes", step=1)
        st.checkbox("Repeat guest", key="pb_repeat_guest")
        st.number_input("Previous stays (not cancelled)", key="pb_previous_stays", step=1)
        st.number_input("Previous cancellations", key="pb_previous_cancellations", step=1)
        st.number_input("Days since last stay", key="pb_days_since_last_stay", step=1,
                        help="Used for the recommended action, not for the CLV value.")
    with st.container(key="pb_actions", horizontal=True, horizontal_alignment="right"):
        run = st.button("Predict CLV", type="primary", icon=":material/insights:", key="pb_run")

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
if run or s.pop("_pb_run", False):
    b = _read()
    errors, warnings = P.validate(b)
    if errors:
        s["_pb_result"] = {"errors": errors}
    else:
        m = repo.model_meta()
        r = P.predict(b, m.high_min_clv, m.low_max_clv, m.platinum_min_clv, repo.at_risk_days())
        r["warnings"] = warnings
        all_clv = repo.guests()["predicted_clv"]
        r["top_pct"] = max(1, round(100 * (all_clv > r["clv"]).mean()))
        s["_pb_result"] = r
        hist = s.setdefault("_pb_history", [])
        hist.insert(0, {"Fingerprint": r["fingerprint"], "Nights": b.weekend_nights + b.week_nights,
                        "Rate (KSh)": int(b.adr_ksh), "Prev. stays": b.previous_stays,
                        "Repeat": "Yes" if b.repeat_guest else "No", "Predicted CLV (KSh)": int(round(r["clv"])),
                        "Tier": r["badge"], "Action": r["action"]})
        del hist[12:]

res = s.get("_pb_result")
if res and "errors" in res:
    with ui.card("pb_rejected"):
        ui.card_title("Booking rejected", "The model was not run, because these details are impossible:",
                      fa="ban")
        for e in res["errors"]:
            alert("error", e)
elif res:
    left, right = st.columns([1, 1.3], gap="small")
    tone = {"High": "brand", "Medium": "sage", "Low": "sky"}[res["tier"]]
    with left:
        st.html(f"""
        <div class="gl-clv gl-clv-{tone}">
            <div class="gl-k">Predicted Customer Lifetime Value</div>
            <div class="gl-clv-v">{ui.ksh(res["clv"])}</div>
            <div class="gl-clv-tier">{ui.esc(res["badge"])} value tier</div>
            <div class="gl-clv-c">Higher than {100 - res["top_pct"]}% of current guests · XGBoost</div>
        </div>""")
        with ui.card("pb_action"):
            st.html(f"""
            <div class="gl-rec-k">{icon("bolt")} Recommended Action</div>
            <div class="gl-rec-v">{ui.esc(res["action"])}</div>
            <div class="gl-rec-r">Reason: {ui.esc(res["reason"])}</div>""")
            ui.note(f"Input fingerprint {res['fingerprint']}: the same inputs always give exactly the same prediction.")
        for w in res.get("warnings", []):
            alert("warning", w)
    with right, ui.card("pb_drivers"):
        ui.card_title("Prediction Drivers", "Share of the model's reasoning — ▲ raised, ▼ lowered the CLV")
        d = res["drivers"]
        charts.show(charts.hbar_track([x for x, _, _ in d], [v for _, v, _ in d],
                                      [charts.SERIES[i % len(charts.SERIES)] for i in range(len(d))],
                                      [f"{'▲' if way == 'up' else '▼'} {v:.0f}%" for _, v, way in d],
                                      max_value=100, height=30 * len(d) + 6),
                    key="chart_pb_drivers", filename="prediction_drivers")

hist = s.get("_pb_history")
if hist:
    with ui.card("pb_history"):
        with st.container(horizontal=True, vertical_alignment="center"):
            ui.card_title("Recent predictions", "Compare the bookings you have priced in this session")
            st.space("stretch")
            if st.button("Clear", type="tertiary", key="pb_clear"):
                s.pop("_pb_history", None)
                st.rerun()
        st.dataframe(pd.DataFrame(hist), hide_index=True, width="stretch")

ui.css("""
.st-key-pb_actions { padding-top: 16px; border-top: 1px solid var(--line); }
.stApp .st-key-pb_actions button { min-width: 180px; min-height: 42px; padding: 0 22px; }
.pb-group { font-size: 0.9rem; font-weight: 600; color: var(--ink-900); margin-bottom: 4px;
            padding-bottom: 8px; border-bottom: 1px solid var(--line); }
.gl-k { font-size: 0.8rem; font-weight: 500; color: var(--ink-500); }
.gl-clv { border-radius: var(--r-lg); padding: 20px 22px; border: 1px solid; animation: ds-rise .5s var(--ease) both; margin-bottom: 12px; }
.gl-clv-brand { background: radial-gradient(500px 220px at 100% 0%, rgba(168,224,190,.22), rgba(168,224,190,0) 60%),
                linear-gradient(140deg, var(--brand-600), var(--brand-700)); border-color: var(--brand-700);
                box-shadow: 0 18px 36px -22px rgba(0,63,43,.8); }
.gl-clv-brand .gl-k, .gl-clv-brand .gl-clv-c { color: rgba(255,255,255,.7); }
.gl-clv-brand .gl-clv-v { color: #FFFFFF; }
.gl-clv-brand .gl-clv-tier { color: var(--mint-300); }
.gl-clv-sage { background: var(--sage-50); border-color: var(--sage-200); }
.gl-clv-sage .gl-clv-v, .gl-clv-sage .gl-clv-tier { color: var(--sage-700); }
.gl-clv-sky  { background: var(--sky-50);  border-color: var(--sky-200); }
.gl-clv-sky  .gl-clv-v, .gl-clv-sky  .gl-clv-tier { color: var(--sky-700); }
.gl-clv-v { margin-top: 8px; font-size: 2.1rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; font-variant-numeric: tabular-nums; }
.gl-clv-tier { margin-top: 4px; font-size: 0.9rem; font-weight: 500; }
.gl-clv-c { margin-top: 2px; font-size: 0.8rem; color: var(--ink-600); }
.gl-rec-k { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; font-weight: 500;
            color: var(--ink-500); }
.gl-rec-k i { color: var(--brand-600); }
.gl-rec-v { margin-top: 10px; font-size: 1.05rem; font-weight: 600; color: var(--ink-900); }
.gl-rec-r { margin-top: 4px; font-size: 0.85rem; line-height: 1.5; color: var(--ink-600); }
""")
