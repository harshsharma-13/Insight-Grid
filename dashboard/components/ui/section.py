import streamlit as st


def section_title(title, subtitle=None):
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{title}</h2>
            {f"<p>{subtitle}</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )