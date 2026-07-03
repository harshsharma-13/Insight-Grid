import streamlit as st


def summary_tile(title, value, subtitle="", icon="📌", color="#3B82F6"):
    st.markdown(
        f"""
<div style="background:#111827; border:1px solid #2D3748; border-left:6px solid {color}; border-radius:14px; padding:18px; min-height:165px; box-sizing:border-box;">
  <div style="font-size:30px;">{icon}</div>
  <p style="color:#9CA3AF; font-size:13px; margin:10px 0 0 0; font-weight:500;">{title}</p>
  <p style="color:white; font-size:28px; font-weight:700; margin:6px 0 0 0; line-height:1.1;">{value}</p>
  <p style="color:#D1D5DB; font-size:14px; margin:14px 0 0 0; line-height:1.45;">{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )