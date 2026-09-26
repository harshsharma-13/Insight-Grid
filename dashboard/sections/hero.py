import streamlit as st


def render(kpis, brand_count):
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-grid"></div>
            <div class="hero-content">
                <div class="eyebrow"><span class="eyebrow-dot"></span> AI consumer command center</div>
                <h1>See the market.<br><span class="gradient-text">Hear the customer.</span></h1>
                <p>
                    Turn thousands of smartphone reviews, specifications and price signals into
                    confident product, marketing and buying decisions.
                </p>
                <div class="hero-stats">
                    <span class="hero-stat"><strong>{kpis['total_phones']}</strong> devices tracked</span>
                    <span class="hero-stat"><strong>{kpis['total_reviews']:,}</strong> reviews analyzed</span>
                    <span class="hero-stat"><strong>{brand_count}</strong> brands benchmarked</span>
                    <span class="hero-stat"><strong>{kpis['avg_positive']}%</strong> positive signal</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
