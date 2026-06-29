import streamlit as st


def kpi_card(label, value, helper=None):
    with st.container(border=True):
        st.caption(label)
        st.markdown(f"### {value}")
        if helper:
            st.caption(helper)