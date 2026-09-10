import pandas as pd
import streamlit as st

from data.dummy_guests import ACTUAL_VS_PREDICTED, FEATURE_IMPORTANCE, MODEL_COMPARISON
from utils import render_sidebar_footer, render_model_status_badges, logout_button

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("Model Performance")
    st.caption("Evaluation and interpretability of the Customer Lifetime Value prediction models")
with col_badge:
    render_model_status_badges()

st.subheader("Model Comparison")
st.markdown("Deployed model: ✅ **XGBoost — Best Performing**")

comp_df = pd.DataFrame({
    "METRIC": MODEL_COMPARISON["metrics"],
    "RANDOM FOREST": MODEL_COMPARISON["random_forest"],
    "XGBOOST": MODEL_COMPARISON["xgboost"],
})
st.dataframe(comp_df, width='stretch', hide_index=True)

st.write("")
left, mid, right = st.columns(3)

with left:
    st.subheader("Model Performance Comparison")
    perf_df = pd.DataFrame({
        "Random Forest": [MODEL_COMPARISON["random_forest"][0] / 100,
                           MODEL_COMPARISON["random_forest"][1] / 100,
                           MODEL_COMPARISON["random_forest"][2] * 100],
        "XGBoost": [MODEL_COMPARISON["xgboost"][0] / 100,
                    MODEL_COMPARISON["xgboost"][1] / 100,
                    MODEL_COMPARISON["xgboost"][2] * 100],
    }, index=["MAE (norm)", "RMSE (norm)", "R²"])
    st.bar_chart(perf_df)

with mid:
    st.subheader("📊 Feature Importance")
    st.caption("Guest behavioural variables contributing most strongly to predicted CLV.")
    for label, pct in FEATURE_IMPORTANCE:
        c1, c2 = st.columns([3, 1])
        c1.caption(label)
        c2.markdown(f"**{pct}%**")
        st.progress(pct / 100)
    st.caption("Download as PNG / CSV")

with right:
    st.subheader("📈 Actual vs Predicted CLV")
    st.caption("Test set — dashed line = perfect prediction")
    avp_df = pd.DataFrame(ACTUAL_VS_PREDICTED, columns=["Actual CLV (KSh)", "Predicted CLV (KSh)"])
    st.scatter_chart(avp_df, x="Actual CLV (KSh)", y="Predicted CLV (KSh)")

st.write("")
st.subheader("📖 Model Interpretation")
i1, i2, i3 = st.columns(3)
with i1, st.container(border=True):
    st.markdown("❓ **What does the model predict?**")
    st.caption("The model estimates the total future revenue a guest is likely to generate over "
               "their relationship with the hotel. This allows the Revenue Manager to prioritise "
               "high-value guests for personalised service.")
with i2, st.container(border=True):
    st.markdown("🔁 **Why is Repeat Visits the top feature?**")
    st.caption("Guests who return frequently have proven loyalty and are consistently found to "
               "spend more over time. Repeat visit behaviour is the single strongest signal of "
               "long-term guest value.")
with i3, st.container(border=True):
    st.markdown("🛡️ **How confident are the predictions?**")
    st.caption("The XGBoost model explains 87.1% of variation in guest CLV (R² = 0.871). "
               "Predictions should be used as decision-support tools alongside human judgement, "
               "not as absolute values.")

render_sidebar_footer()
logout_button()
