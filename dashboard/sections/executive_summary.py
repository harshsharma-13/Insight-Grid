import streamlit as st

from components.ui.section import section_title


def render(summary):

    section_title(
        "🧠 AI Executive Summary",
        "An AI-generated overview of the current smartphone market."
    )

    with st.container(border=True):
        st.markdown(summary)

    st.divider()