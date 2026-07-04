import streamlit as st


def navbar():
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"] {
                display: none;
            }

            .block-container {
                padding-top: 1rem;
            }

            div[data-testid="stHorizontalBlock"] {
                align-items: center;
            }

            .nav-wrapper {
                position: sticky;
                top: 0;
                z-index: 999;
                background: rgba(11, 15, 23, 0.95);
                backdrop-filter: blur(14px);
                border-bottom: 1px solid #263244;
                padding: 0.6rem 0;
                margin-bottom: 2rem;
            }

            div[data-testid="stPopover"] button,
            div[data-testid="stPageLink"] a {
                border-radius: 999px !important;
                font-weight: 700 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        st.page_link("app.py", label="Home", icon="🏠")

    with c2:
        with st.popover("Explore", use_container_width=True):
            st.page_link("pages/📱_Phone_Explorer.py", label="Phone Explorer", icon="📱")
            st.page_link("pages/🔎_Review_Explorer.py", label="Review Explorer", icon="🔎")
            st.page_link("pages/🎯_Phone_Finder.py", label="Phone Finder", icon="🎯")

    with c3:
        with st.popover("Analyze", use_container_width=True):
            st.page_link("pages/⚖️_Compare_Phones.py", label="Compare Phones", icon="⚖️")
            st.page_link("pages/🏆_Competitive_Intelligence.py", label="Competitive Intelligence", icon="🏆")

    with c4:
        with st.popover("Act", use_container_width=True):
            st.page_link("pages/🛠️_Product_Action_Center.py", label="Product Action Center", icon="🛠")

    st.markdown("</div>", unsafe_allow_html=True)