import pandas as pd
import streamlit as st

from data.dummy_guests import SEGMENT_TIMELINE
from utils import render_sidebar_footer, render_top_role_badge, logout_button

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("Segments")
    st.caption("Guest CLV tier distribution over time")
with col_badge:
    render_top_role_badge()

df = pd.DataFrame(SEGMENT_TIMELINE).set_index("months")

st.subheader("Tier Distribution Over Time")
st.line_chart(df)

if st.session_state.role == "marketing":
    st.button("⬇ Download Chart")

st.write("")
st.subheader("Current Tier Breakdown")
c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.caption("🟢 High Tier")
    st.markdown(f"### {df['High'].iloc[-1]:,}")
with c2, st.container(border=True):
    st.caption("🟠 Medium Tier")
    st.markdown(f"### {df['Medium'].iloc[-1]:,}")
with c3, st.container(border=True):
    st.caption("🔴 Low Tier")
    st.markdown(f"### {df['Low'].iloc[-1]:,}")

render_sidebar_footer()
logout_button()
