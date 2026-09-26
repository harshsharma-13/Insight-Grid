import streamlit as st


def chart_card(title, fig):
    fig.update_layout(
        paper_bgcolor="#111820",
        plot_bgcolor="#111820",
        font=dict(family="Segoe UI", size=13, color="#F3F4F6"),
        margin=dict(l=12, r=12, t=20, b=12),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    fig.update_xaxes(showgrid=False, zeroline=False, color="#94A3B8")
    fig.update_yaxes(showgrid=True, gridcolor="#263244", zeroline=False, color="#94A3B8")

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False, "responsive": True},
        )
