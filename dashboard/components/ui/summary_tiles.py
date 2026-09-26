import streamlit as st


def summary_tile(title, value, subtitle="", icon="📌", color="#3B82F6"):
    st.markdown(
        f"""
<div class="summary-card" style="--card-accent:{color};">
  <div class="summary-icon">{icon}</div>
  <div class="summary-label">{title}</div>
  <div class="summary-value">{value}</div>
  <div class="summary-subtitle">{subtitle}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
