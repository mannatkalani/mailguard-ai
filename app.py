import streamlit as st

from src.utils import inject_global_css, COLORS
from src.classifier import get_classifier
from src import gmail_auth

st.set_page_config(
    page_title="MailGuard AI — Gmail Spam Screener",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

DEFAULTS = {
    "review_threshold": 60,
    "fetch_count": 40,
    "scan_results": None,
    "selected_message_id": None,
    "gmail_email": None,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

clf = get_classifier()

PAGES = {
    "Overview": "overview",
    "Gmail Scanner": "gmail_scanner",
    "Quick Test": "quick_test",
    "Settings": "settings",
}
ICONS = {"Overview": "🏠", "Gmail Scanner": "📥", "Quick Test": "✍️", "Settings": "⚙️"}

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 0.4rem 0 1.1rem 0;">
            <div style="font-family:'Fraunces',serif; font-size:1.4rem; font-weight:700; color:{COLORS['cream']};">
                🍷 MailGuard AI
            </div>
            <div style="font-size:0.75rem; color:{COLORS['gold']}; letter-spacing:0.05em; text-transform:uppercase;">
                Gmail Spam Screener
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_page = st.session_state.pop("nav_override", "Overview")
    labels = [f"{ICONS[p]}  {p}" for p in PAGES]
    default_index = list(PAGES.keys()).index(default_page) if default_page in PAGES else 0
    choice = st.radio("Navigate", labels, index=default_index, label_visibility="collapsed")
    current_page = choice.split("  ", 1)[1]

    st.markdown("<hr>", unsafe_allow_html=True)
    if gmail_auth.is_connected():
        st.caption("Gmail status")
        st.markdown("🟢 **Connected**")
    elif gmail_auth.is_configured():
        st.caption("Gmail status")
        st.markdown("🟡 **Ready to connect**")
    else:
        st.caption("Gmail status")
        st.markdown("⚪ **Setup needed**")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("MailGuard AI · NLP + ML spam screening. Predictions are probabilistic, not a guarantee.")

module_name = PAGES[current_page]
page_module = __import__(f"app_pages.{module_name}", fromlist=["render"])
page_module.render()
