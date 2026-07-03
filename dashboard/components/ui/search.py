import streamlit as st


def ai_search_box():
    st.markdown('<div class="search-wrap">', unsafe_allow_html=True)

    query = st.text_input(
        "Universal AI Search",
        placeholder="🔍 Ask anything about smartphones...",
        label_visibility="collapsed",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    return query