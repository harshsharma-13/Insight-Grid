from html import escape

import streamlit as st


def page_header(eyebrow, title, description, context=None):
    context = context or []
    context_html = "".join(
        f'<span class="workspace-context-item">{escape(str(item))}</span>'
        for item in context
        if item
    )

    st.markdown(
        f"""
        <header class="workspace-header">
            <div class="workspace-eyebrow">{escape(str(eyebrow))}</div>
            <div class="workspace-header-row">
                <div>
                    <h1>{escape(str(title))}</h1>
                    <p>{escape(str(description))}</p>
                </div>
                <div class="workspace-context">{context_html}</div>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def executive_brief(text, label="Executive brief", tone="blue"):
    st.markdown(
        f"""
        <div class="executive-brief executive-brief-{escape(str(tone))}">
            <div class="executive-brief-label"><span></span>{escape(str(label))}</div>
            <div class="executive-brief-copy">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
