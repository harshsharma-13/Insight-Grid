import streamlit as st

from components.ui.section import section_title


def _priority_style(priority):
    if priority == "Critical":
        return "🔴 Critical"
    if priority == "Important":
        return "🟠 Important"
    return "🟡 Monitor"


def render(get_action_dataset, get_action_summary):
    section_title(
        "🛠 Product Action Center",
        "Convert recurring customer pain points into clear product actions.",
    )

    actions_df = get_action_dataset()

    if actions_df.empty:
        st.info("No product actions available yet.")
        return

    st.info(get_action_summary(actions_df))

    st.markdown("### Recommended Product Actions")

    for _, row in actions_df.head(8).iterrows():

        with st.container(border=True):

            left, right = st.columns([4, 1])

            with left:

                st.markdown(f"### {row['issue']}")

                st.caption(
                    f"{row['phones']} phones affected • {row['brands']} brands affected"
                )

                st.markdown(f"**Owner:** {row['owner']}")

                st.markdown("**Affected Brands**")
                st.write(row["affected_brands"])

                st.markdown("**Example Phones**")
                st.write(row["example_phones"])

                st.markdown("**Recommended Action**")
                st.write(row["recommended_action"])

                st.markdown("**Why this action is recommended**")

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