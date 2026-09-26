import streamlit as st


def section_title(title, subtitle=None):
    parts = title.split(" ", 1)
    first = parts[0]
    has_icon = len(parts) == 2 and not any(character.isalnum() for character in first)
    icon = first if has_icon else ""
    clean_title = parts[1] if has_icon else title

    st.markdown(
        f"""
        <div class="section-header">
            {f'<div class="section-icon">{icon}</div>' if icon else ''}
            <div>
                <h2>{clean_title}</h2>
                {f"<p>{subtitle}</p>" if subtitle else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
