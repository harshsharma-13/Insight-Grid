from components.ui.page_header import executive_brief
from components.ui.section import section_title


def render(summary):

    section_title(
        "🧠 AI Executive Summary",
        "An AI-generated overview of the current smartphone market."
    )

    executive_brief(summary.replace("**", ""), label="Market readout")
