import streamlit as st


def kpi_tile(label, value, icon=""):
    with st.container(border=True):
        st.markdown(f"## {icon}")
        st.markdown(f"### {value}")
        st.caption(label)