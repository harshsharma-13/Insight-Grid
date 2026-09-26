import streamlit as st


def ai_search_box():
    with st.container(key="ai_command_bar"):
        st.markdown(
            '<div class="search-kicker"><span class="search-spark">✦</span> ASK MARKET INTELLIGENCE</div>',
            unsafe_allow_html=True,
        )

        query = st.text_input(
            "Universal AI Search",
            placeholder="Ask about a phone, feature, segment or customer concern…",
            label_visibility="collapsed",
            key="universal_ai_search",
        )

        prompts = [
            "Best phone for gaming",
            "Compare camera performance",
            "Top customer pain points",
        ]

        prompt_cols = st.columns(3)
        for col, prompt in zip(prompt_cols, prompts):
            with col:
                if st.button(prompt, key=f"prompt_{prompt}", width="stretch"):
                    query = prompt

    return query
