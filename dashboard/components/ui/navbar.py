import streamlit as st


def _nav_item(column, active, slug, page, label, icon):
    container_key = "active_navigation_tab" if active == slug else f"navigation_tab_{slug}"

    with column:
        with st.container(key=container_key):
            st.page_link(page, label=label, icon=icon, width="stretch")


def navbar(active="overview"):
    with st.container(key="top_navigation"):
        brand, context = st.columns([3, 2])

        with brand:
            st.markdown(
                """
                <div class="brand-lockup">
                    <div class="brand-mark">CI</div>
                    <div>
                        <div class="brand-name">Consumer Intelligence</div>
                        <div class="brand-status">Live market signal</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with context:
            st.markdown(
                """
                <div class="nav-context">
                    <span class="nav-context-label">MARKET</span>
                    <span>Smartphones · India</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.container(key="navigation_tabs"):
            overview, phones, reviews, finder, compare, intelligence, actions = st.columns(7)

            _nav_item(overview, active, "overview", "app.py", "Overview", "🏠")
            _nav_item(phones, active, "phones", "pages/📱_Phone_Explorer.py", "Phones", "📱")
            _nav_item(reviews, active, "reviews", "pages/🔎_Review_Explorer.py", "Reviews", "🔎")
            _nav_item(finder, active, "finder", "pages/🎯_Phone_Finder.py", "Finder", "🎯")
            _nav_item(compare, active, "compare", "pages/⚖️_Compare_Phones.py", "Compare", "⚖️")
            _nav_item(
                intelligence,
                active,
                "intelligence",
                "pages/🏆_Competitive_Intelligence.py",
                "Intelligence",
                "📊",
            )
            _nav_item(
                actions,
                active,
                "actions",
                "pages/🛠️_Product_Action_Center.py",
                "Actions",
                "🚀",
            )
