import streamlit as st


def hero():

    st.markdown(
        """
        <style>

        .hero{
            padding:32px;
            border-radius:18px;
            background:linear-gradient(135deg,#111827,#1E293B);
            border:1px solid #334155;
            margin-bottom:25px;
        }

        .hero h1{
            font-size:44px;
            margin-bottom:8px;
            font-weight:800;
        }

        .hero p{
            color:#CBD5E1;
            font-size:18px;
            margin-bottom:22px;
        }

        .hero-chip{
            display:inline-block;
            padding:8px 14px;
            border-radius:999px;
            background:#0F172A;
            border:1px solid #334155;
            margin-right:10px;
            margin-bottom:10px;
            font-size:14px;
            color:#E2E8F0;
        }

        </style>

        <div class="hero">

        <h1>AI Consumer & Market Intelligence Platform</h1>

        <p>
        Transform smartphone reviews into actionable business intelligence for
        Product, Marketing, Sales and Research teams.
        </p>

        <span class="hero-chip">📱 Phone Intelligence</span>
        <span class="hero-chip">💬 Voice of Customer</span>
        <span class="hero-chip">📊 Market Analytics</span>
        <span class="hero-chip">🤖 AI Decision Support</span>

        </div>

        """,
        unsafe_allow_html=True,
    )