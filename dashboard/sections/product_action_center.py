import streamlit as st

from components.ui.kpi_tile import kpi_tile
from components.ui.page_header import executive_brief, page_header


def _priority_style(priority):
    if priority == "Critical":
        return "🔴 Critical"
    if priority == "Important":
        return "🟠 Important"
    return "🟡 Monitor"


def render(get_action_dataset, get_action_summary):
    actions_df = get_action_dataset()

    page_header(
        "Prioritization workspace",
        "Product Action Center",
        "Translate recurring customer pain points into owned, evidence-backed product interventions.",
        context=[
            f"{len(actions_df)} opportunities",
            "Voice-of-customer evidence",
            "Impact-oriented",
        ],
    )

    if actions_df.empty:
        st.info("No product actions available yet.")
        return

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_tile("Open opportunities", len(actions_df), "◫")
    with k2:
        kpi_tile("Critical priorities", int((actions_df["priority"] == "Critical").sum()), "!")
    with k3:
        kpi_tile("Customer mentions", f"{int(actions_df['mentions'].sum()):,}", "◎")
    with k4:
        kpi_tile("Owners involved", actions_df["owner"].nunique(), "↗")

    executive_brief(
        get_action_summary(actions_df).replace("**", ""),
        label="Portfolio priority readout",
    )

    with st.container(key="filter_toolbar"):
        st.markdown('<div class="filter-label">Action filters</div>', unsafe_allow_html=True)
        f1, f2 = st.columns(2)
        with f1:
            selected_priority = st.selectbox(
                "Priority",
                ["All"] + actions_df["priority"].dropna().unique().tolist(),
                key="action_priority_filter",
            )
        with f2:
            selected_owner = st.selectbox(
                "Owner",
                ["All"] + sorted(actions_df["owner"].dropna().unique().tolist()),
                key="action_owner_filter",
            )

    filtered_actions = actions_df.copy()
    if selected_priority != "All":
        filtered_actions = filtered_actions[filtered_actions["priority"] == selected_priority]
    if selected_owner != "All":
        filtered_actions = filtered_actions[filtered_actions["owner"] == selected_owner]

    st.markdown('<div class="analysis-panel-title">Prioritized opportunity queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-panel-caption">Ordered customer problems with owners, supporting evidence and expected business impact.</div>', unsafe_allow_html=True)

    if filtered_actions.empty:
        st.info("No actions match the selected filters.")
        return

    for index, (_, row) in enumerate(filtered_actions.head(10).iterrows(), start=1):

        with st.container(key=f"action_card_{index}", border=True):

            left, right = st.columns([4, 1])

            with left:

                st.caption(f"OPPORTUNITY {index:02d}")
                st.markdown(f"### {row['issue']}")

                st.caption(
                    f"{row['phones']} phones affected • {row['brands']} brands affected"
                )

                st.markdown(f"**Accountable team:** {row['owner']}")

                st.markdown("**Affected Brands**")
                st.write(row["affected_brands"])

                st.markdown("**Example Phones**")
                st.write(row["example_phones"])

                st.markdown("**Recommended Action**")
                st.write(row["recommended_action"])

                st.markdown("**Customer evidence**")

                if row["evidence"]:
                    for evidence in row["evidence"]:

                        title = (
                            f"{evidence['brand']} • "
                            f"{evidence['phone_name']} • "
                            f"{evidence['platform']}"
                        )

                        with st.expander(title):
                            st.write(evidence["review"])
                else:
                    st.caption("No supporting review excerpts found.")

                st.markdown("**Expected Business Impact**")
                st.write(row["business_impact"])

            with right:

                st.metric("Mentions", row["mentions"])
                st.markdown(f"### {_priority_style(row['priority'])}")

    st.divider()
