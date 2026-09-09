"""
Shared visual identity (wine/burgundy palette) and small UI helper
components reused across pages: KPI cards, status badges, section headers.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLORS = {
    "primary_wine": "#6E1F3A",
    "deep_burgundy": "#4A1428",
    "merlot": "#7B2948",
    "dark_plum": "#321522",
    "cream": "#F7F1EC",
    "beige": "#E9DDD5",
    "gold": "#C7A46A",
    "spam": "#7B2948",
    "spam_bg": "#F3E1E6",
    "ham": "#4F6F52",
    "ham_bg": "#E7EFE6",
    "review": "#B8863A",
    "review_bg": "#F6ECD9",
    "text_dark": "#321522",
    "text_muted": "#8A6B76",
}

PLOTLY_SEQUENCE = ["#6E1F3A", "#C7A46A", "#7B2948", "#4F6F52", "#B8863A", "#4A1428", "#A8697F", "#D9C7A3"]
PLOTLY_DIVERGING = ["#4F6F52", "#C7A46A", "#7B2948"]


def inject_global_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: linear-gradient(180deg, {COLORS['cream']} 0%, {COLORS['beige']} 100%);
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['dark_plum']} 0%, {COLORS['deep_burgundy']} 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: {COLORS['cream']} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: rgba(247,241,236,0.15);
        }}

        h1, h2, h3 {{
            font-family: 'Fraunces', serif !important;
            color: {COLORS['deep_burgundy']} !important;
        }}

        .mg-hero {{
            background: linear-gradient(120deg, {COLORS['deep_burgundy']} 0%, {COLORS['primary_wine']} 55%, {COLORS['merlot']} 100%);
            border-radius: 20px;
            padding: 2.6rem 2.8rem;
            color: {COLORS['cream']};
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 30px rgba(74,20,40,0.25);
        }}
        .mg-hero h1 {{
            color: {COLORS['cream']} !important;
            font-size: 2.4rem;
            margin-bottom: 0.3rem;
        }}
        .mg-hero p {{
            color: {COLORS['beige']};
            font-size: 1.05rem;
            max-width: 640px;
        }}
        .mg-eyebrow {{
            display: inline-block;
            background: rgba(247,241,236,0.12);
            border: 1px solid rgba(247,241,236,0.25);
            color: {COLORS['gold']};
            padding: 0.2rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }}

        .mg-card {{
            background: #FFFFFF;
            border: 1px solid {COLORS['beige']};
            border-radius: 16px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 2px 10px rgba(74,20,40,0.06);
        }}

        .mg-kpi-label {{
            color: {COLORS['text_muted']};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }}
        .mg-kpi-value {{
            color: {COLORS['deep_burgundy']};
            font-size: 1.9rem;
            font-weight: 700;
            font-family: 'Fraunces', serif;
        }}
        .mg-kpi-sub {{
            color: {COLORS['text_muted']};
            font-size: 0.78rem;
        }}

        .mg-badge {{
            display: inline-block;
            padding: 0.28rem 0.8rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
        }}
        .mg-badge-spam {{ background: {COLORS['spam_bg']}; color: {COLORS['spam']}; border: 1px solid {COLORS['spam']}55;}}
        .mg-badge-ham {{ background: {COLORS['ham_bg']}; color: {COLORS['ham']}; border: 1px solid {COLORS['ham']}55;}}
        .mg-badge-review {{ background: {COLORS['review_bg']}; color: {COLORS['review']}; border: 1px solid {COLORS['review']}55;}}

        .mg-pipeline-step {{
            background: #FFFFFF;
            border: 1px solid {COLORS['beige']};
            border-radius: 12px;
            padding: 0.7rem 0.5rem;
            text-align: center;
            font-size: 0.82rem;
            font-weight: 600;
            color: {COLORS['deep_burgundy']};
        }}

        div.stButton > button {{
            background: {COLORS['primary_wine']};
            color: {COLORS['cream']};
            border: none;
            border-radius: 10px;
            padding: 0.55rem 1.3rem;
            font-weight: 600;
        }}
        div.stButton > button:hover {{
            background: {COLORS['deep_burgundy']};
            color: {COLORS['gold']};
        }}
        div.stButton > button[kind="secondary"] {{
            background: transparent;
            color: {COLORS['primary_wine']};
            border: 1.5px solid {COLORS['primary_wine']};
        }}

        div[data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid {COLORS['beige']};
            border-radius: 14px;
            padding: 0.8rem 1rem;
        }}

        .mg-privacy-note {{
            background: {COLORS['beige']};
            border-left: 4px solid {COLORS['gold']};
            border-radius: 8px;
            padding: 0.7rem 1rem;
            font-size: 0.85rem;
            color: {COLORS['text_dark']};
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge_html(status: str) -> str:
    status = (status or "").upper()
    cls = {"SPAM": "mg-badge-spam", "HAM": "mg-badge-ham", "REVIEW": "mg-badge-review"}.get(status, "mg-badge-ham")
    icon = {"SPAM": "⛔", "HAM": "✅", "REVIEW": "⚠️"}.get(status, "")
    return f'<span class="mg-badge {cls}">{icon} {status}</span>'


def kpi_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="mg-card">
            <div class="mg-kpi-label">{label}</div>
            <div class="mg-kpi-value">{value}</div>
            <div class="mg-kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="margin-bottom:1.3rem;">
            <div class="mg-eyebrow" style="background:{COLORS['beige']}; color:{COLORS['primary_wine']}; border:1px solid {COLORS['primary_wine']}33;">{eyebrow}</div>
            <h2 style="margin:0.2rem 0 0.1rem 0;">{title}</h2>
            <p style="color:{COLORS['text_muted']}; margin:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
