import streamlit as st


def hero(title, subtitle, badge=None):
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title, value, icon=""):
    with st.container(border=True):
        st.caption(f"{icon} {title}")
        st.markdown(f"**{value}**")


def insight_card(title, text, icon=""):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.write(text)


def list_card(title, items, icon="•"):
    with st.container(border=True):
        st.markdown(f"### {title}")
        for item in items:
            if item:
                st.markdown(f"{icon} {item}")


def verdict_chip(verdict):
    verdict = str(verdict)
    if "Highly" in verdict or "Positive" in verdict:
        color = "🟢"
    elif "Mixed" in verdict:
        color = "🟡"
    elif "Not" in verdict:
        color = "🔴"
    else:
        color = "⚪"
    return f"{color} {verdict}"