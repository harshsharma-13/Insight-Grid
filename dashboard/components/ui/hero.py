import streamlit as st


def home_hero():
    st.markdown(
        """
        <div class="hero-card">
            <h1>AI Consumer Intelligence Platform</h1>
            <p>
                Understand what consumers really think about smartphones using
                reviews, specifications, platform signals and local AI insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )