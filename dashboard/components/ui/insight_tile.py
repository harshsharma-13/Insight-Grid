import streamlit as st


def insight_tile(title, summary, meta=None, icon=""):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")

        if meta:
            st.caption(meta)

        st.write(summary)


def list_insight_tile(title, items, icon="•"):
    with st.container(border=True):
        st.markdown(f"### {title}")

        if not items:
            st.caption("No data available")

        for item in items:
            if item:
                st.markdown(f"{icon} {item}")