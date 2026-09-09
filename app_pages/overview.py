import streamlit as st

from src.utils import COLORS, page_header
from src.classifier import get_classifier
from src import gmail_auth


def render():
    clf = get_classifier()
    meta = clf.metadata
    prod = meta["model_comparison"][meta["production_model"]]

    st.markdown(
        f"""
        <div class="mg-hero">
            <div class="mg-eyebrow">AI-Powered Gmail Spam Screening</div>
            <h1>MailGuard AI</h1>
            <p>Connect your Gmail account and automatically scan your inbox for spam —
            powered by a machine learning model trained and evaluated on 35,000+ labeled messages.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("📥  Connect Gmail & Scan", use_container_width=True):
            st.session_state.nav_override = "Gmail Scanner"
            st.rerun()
    with c2:
        st.link_button("📄  Read Setup Instructions", "#", disabled=True,
                        help="See the README, or open Gmail Scanner — setup steps are shown there if not yet connected.")

    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Model Accuracy", f"{prod['test_accuracy']*100:.2f}%")
    m2.metric("Model AUC", f"{prod['auc']:.3f}")
    m3.metric("Training Messages", f"{meta['dataset_stats']['total_messages']:,}")

    st.write("")
    page_header("Connecting your Gmail", "It's a one-click sign-in",
                "No password ever needed — Google's own sign-in screen handles authentication.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="mg-card">
                <div style="font-size:1.6rem;">1️⃣</div>
                <h3 style="margin:0.3rem 0;">Click Connect</h3>
                <p style="color:{COLORS['text_muted']};">Go to Gmail Scanner and click <b>Connect Gmail</b>.</p>
            </div>
            """, unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"""
            <div class="mg-card">
                <div style="font-size:1.6rem;">2️⃣</div>
                <h3 style="margin:0.3rem 0;">Sign in with Google</h3>
                <p style="color:{COLORS['text_muted']};">Your browser opens Google's official sign-in page. Choose your account and click Allow.</p>
            </div>
            """, unsafe_allow_html=True)
    with c3:
        st.markdown(
            f"""
            <div class="mg-card">
                <div style="font-size:1.6rem;">3️⃣</div>
                <h3 style="margin:0.3rem 0;">You're connected</h3>
                <p style="color:{COLORS['text_muted']};">The tab closes automatically and your inbox is ready to scan — reconnects instantly next time.</p>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    status = "🟢 Connected" if gmail_auth.is_connected() else ("🟡 Ready to connect" if gmail_auth.is_configured() else "⚪ Setup needed")
    st.markdown(
        f"""
        <div class="mg-privacy-note">
        🔒 <b>Privacy:</b> MailGuard AI never asks for or stores your Gmail password. It uses Google's
        official OAuth sign-in with read-only access, and can't send, delete, or modify anything in your
        mailbox. Current status: <b>{status}</b> — see the Gmail Scanner page for details.
        </div>
        """,
        unsafe_allow_html=True,
    )
