import streamlit as st


def render_home_hero():
    st.markdown(
        """
        <div class="hero-card">
            <h1>AI Consumer Intelligence Platform</h1>
            <p>
                Search, compare and analyze smartphones using product specifications,
                review sentiment, platform performance and local AI-generated insights.
            </p>
            <span class="badge">Smartphone Market Intelligence</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Ask anything",
        placeholder="Example: Which phones have the best battery and least heating complaints?",
        label_visibility="collapsed",
    )

    return query