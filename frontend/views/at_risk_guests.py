import pandas as pd
import streamlit as st

from data.dummy_guests import AT_RISK_GUESTS, TOTAL_AT_RISK_ROWS
from utils import render_sidebar_footer, render_top_role_badge, render_model_status_badges, logout_button

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("At-Risk High-Value Guests")
    st.caption("High-value guests who have not returned within the selected inactivity period")
with col_badge:
    render_top_role_badge()
    render_model_status_badges()

count = len(AT_RISK_GUESTS)
alert_col, btn_col = st.columns([4, 1])
with alert_col:
    st.error(f"⚠️ {TOTAL_AT_RISK_ROWS} At-Risk High-Value Guests\n\n"
             "These guests represent high predicted CLV and have not returned in 60+ days. "
             "Immediate action is recommended.")
with btn_col:
    st.button("Export All", type="primary", width='stretch')

f1, f2, f3, f4 = st.columns(4)
f1.selectbox("Min CLV", ["KSh 150,000"], label_visibility="collapsed")
f2.selectbox("Days Inactive", ["60+ days"], label_visibility="collapsed")
f3.selectbox("CLV Tier", ["High / Platinum"], label_visibility="collapsed")
f4.selectbox("Booking Channel", ["All Channels"], label_visibility="collapsed")

st.write("")
st.subheader("Days Inactive per At-Risk Guest")
st.caption("Sorted by predicted CLV descending — colour coded by risk level")

chart_df = pd.DataFrame(AT_RISK_GUESTS)[["guest_id", "days_since_last_stay"]].set_index("guest_id")
st.bar_chart(chart_df, horizontal=True)

st.write("")
st.subheader("At-Risk Guest List")
df = pd.DataFrame(AT_RISK_GUESTS).rename(columns={
    "guest_id": "GUEST ID", "predicted_clv": "PREDICTED CLV (KSH)",
    "days_since_last_stay": "DAYS SINCE LAST STAY", "prev_stays": "PREV. STAYS",
    "risk_level": "RISK LEVEL", "recommended_action": "RECOMMENDED ACTION",
})
st.dataframe(df, width='stretch', hide_index=True)
st.caption(f"Showing 1–{count} of {TOTAL_AT_RISK_ROWS}")

render_sidebar_footer()
logout_button()
