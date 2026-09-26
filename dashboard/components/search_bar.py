import streamlit as st


def launchpad_search():
    st.markdown("### Ask anything about the smartphone market")

    query = st.text_input(
        "",
        placeholder="Example: Which phones have the best battery and least heating complaints?",
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button("Best battery phones", width="stretch")

    with col2:
        st.button("Compare Poco vs Redmi", width="stretch")

    with col3:
        st.button("Phones with camera complaints", width="stretch")

    return query
