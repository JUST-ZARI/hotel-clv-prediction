import pandas as pd
import streamlit as st

from data.dummy_guests import GUEST_PROFILES
from utils import render_sidebar_footer, render_top_role_badge, render_model_status_badges, logout_button

is_revenue_manager = st.session_state.role == "revenue_manager"

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("Guest Lookup")
    st.caption("Search for an individual guest and review their predicted lifetime value")
with col_badge:
    render_top_role_badge()
    render_model_status_badges()

search_col, btn_col = st.columns([4, 1])
guest_id_input = search_col.text_input("Guest ID", placeholder="Enter Guest ID — e.g. G-10234",
                                        label_visibility="collapsed")
search_clicked = btn_col.button("Search", type="primary", width='stretch')

guest_id = guest_id_input.strip().upper() if guest_id_input else "G-10234"
guest = GUEST_PROFILES.get(guest_id, GUEST_PROFILES["G-10234"])
if search_clicked and guest_id not in GUEST_PROFILES:
    st.warning(f"No dummy data for '{guest_id}' yet — showing G-10234 instead.")

left, right = st.columns([2.3, 1])

with left:
    with st.container(border=True):
        h1, h2 = st.columns([4, 1])
        h1.caption("GUEST PROFILE")
        h2.markdown(f"<div style='text-align:right;'><span style='background:#eef2ff;"
                    f"color:#3b4ee0;padding:2px 10px;border-radius:6px;font-size:0.85em;'>"
                    f"{guest['tier_badge']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"### {guest['guest_id']}")

        r1c1, r1c2 = st.columns(2)
        r1c1.caption("Total Previous Stays")
        r1c1.markdown(f"**{guest['total_previous_stays']}**")
        r1c2.caption("Average Daily Rate")
        r1c2.markdown(f"**KSh {guest['avg_daily_rate']:,}**")

        r2c1, r2c2 = st.columns(2)
        r2c1.caption("Avg. Length of Stay")
        r2c1.markdown(f"**{guest['avg_length_of_stay']} nights**")
        r2c2.caption("Cancellation Rate")
        r2c2.markdown(f"**{guest['cancellation_rate']}%**")

        r3c1, r3c2 = st.columns(2)
        r3c1.caption("Booking Lead Time")
        r3c1.markdown(f"**{guest['booking_lead_time']} days**")
        r3c2.caption("Booking Channel")
        r3c2.markdown(f"**{guest['booking_channel']}**")

        r4c1, r4c2 = st.columns(2)
        r4c1.caption("Repeat Guest")
        r4c1.markdown(f"**{'Yes' if guest['is_repeat_guest'] else 'No'}**")
        r4c2.caption("Days Since Last Stay")
        r4c2.markdown(f"**{guest['days_since_last_stay']} days**")

    st.write("")
    st.subheader("Behavioural Insights")
    insight_items = list(guest["behavioural_insights"].items())
    for row_start in range(0, len(insight_items), 3):
        cols = st.columns(3)
        for col, (label, data) in zip(cols, insight_items[row_start:row_start + 3]):
            with col, st.container(border=True):
                st.caption(label)
                st.markdown(f"**:green[{data['value']}]**")
                st.caption(data["label"])

    st.write("")
    st.subheader("Historical Stay Timeline")
    stay_cols = st.columns(len(guest["historical_stays"]) + 1)
    for col, stay in zip(stay_cols, guest["historical_stays"]):
        with col:
            st.markdown("🛏️")
            st.markdown(f"**{stay['date']}**")
            st.caption(f"{stay['nights']} nights")
            st.caption(f"KSh {stay['amount']:,}")
            st.caption(f":blue[{stay['room_type']}]")
    with stay_cols[-1]:
        st.markdown(f"**+{guest['earlier_stays_count']}**")
        st.caption("earlier")

    if not is_revenue_manager:
        st.write("")
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.subheader("📨 Execute Recommended Action")
            h2.markdown("<div style='text-align:right;'><span style='background:#eef2ff;"
                        "color:#3b4ee0;padding:2px 10px;border-radius:6px;font-size:0.85em;'>"
                        "Marketing Team</span></div>", unsafe_allow_html=True)

            st.caption("DELIVERY CHANNEL")
            channel = st.radio("Delivery channel", ["✉️ Email", "📄 Download PDF"],
                                horizontal=True, label_visibility="collapsed")

            st.caption("MESSAGE PREVIEW")
            st.text_area(
                "Message preview",
                value=(
                    f"Dear Valued Guest ({guest['guest_id']}),\n\n"
                    f"As one of our {guest['tier_badge']} guests, we would love to offer you a "
                    "personalised VIP concierge experience on your next visit. Please find your "
                    "exclusive offer enclosed.\n\n— Grand Regency Hotel, Revenue & Guest Relations"
                ),
                height=140,
                label_visibility="collapsed",
            )

            if st.button("📨 Send Email" if "Email" in channel else "📄 Generate PDF",
                          type="primary", width='stretch'):
                st.success(f"Action logged: '{guest['recommended_action']}' marked Completed "
                           f"via {'Email' if 'Email' in channel else 'PDF download'}.")

        st.write("")
        st.subheader("Action Logs")
        st.dataframe(pd.DataFrame(guest["action_logs"]), width='stretch', hide_index=True)

with right:
    with st.container(border=True):
        st.caption("PREDICTED CUSTOMER LIFETIME VALUE")
        st.markdown(f"## :green[KSh {guest['predicted_clv']:,}]")
        st.markdown(f"**:green[{guest['clv_tier']}]**")
        st.caption("Top 5% of all hotel guests")

    st.write("")
    with st.container(border=True):
        st.markdown("⚡ **RECOMMENDED ACTION**")
        st.markdown(f"#### {guest['recommended_action']}")
        st.caption(f"Reason: {guest['recommended_action_reason']}")
        if is_revenue_manager:
            st.button("Log Action", type="primary", width='stretch')

    st.write("")
    with st.container(border=True):
        st.markdown("**Prediction Drivers**")
        st.caption("Top features influencing this guest's CLV prediction")
        for label, pct in guest["prediction_drivers"]:
            c1, c2 = st.columns([3, 1])
            c1.caption(label)
            c2.markdown(f"**{pct}%**")
            st.progress(pct / 100)
        st.caption("Download as PNG / CSV")

render_sidebar_footer()
logout_button()
