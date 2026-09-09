import streamlit as st

from src.utils import page_header, COLORS
from src.classifier import get_classifier
from src import gmail_auth


def render():
    page_header("Settings", "Configuration",
                "Controls for classification sensitivity and your Gmail connection.")

    st.markdown("#### Classification")
    st.session_state.review_threshold = st.slider(
        "Review confidence threshold (%)", min_value=50, max_value=95,
        value=st.session_state.get("review_threshold", 60), step=1,
        help="Predictions below this confidence are marked UNCERTAIN / REVIEW instead of SPAM or HAM.",
    )

    clf = get_classifier()
    prod = clf.metadata["model_comparison"][clf.model_name]
    st.markdown(
        f"""
        <div class="mg-card">
            <div class="mg-kpi-label">Production Model</div>
            <div class="mg-kpi-value" style="font-size:1.3rem;">{clf.model_name}</div>
            <div class="mg-kpi-sub">{prod['test_accuracy']*100:.2f}% test accuracy · AUC {prod['auc']:.3f} · trained on {clf.metadata['n_train']:,} messages</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("#### Gmail Connection")
    if not gmail_auth.is_configured():
        st.info("Gmail OAuth isn't set up yet. Open the **Gmail Scanner** page for the 2-minute setup steps.")
    elif gmail_auth.is_connected():
        email = st.session_state.get("gmail_email", "your account")
        st.success(f"🟢 Connected as {email}")
        if st.button("Disconnect Gmail"):
            gmail_auth.disconnect()
            st.session_state.gmail_email = None
            st.rerun()
    else:
        st.warning("🟡 Credentials found, but not yet connected. Go to Gmail Scanner and click **Connect Gmail**.")

    st.write("")
    st.markdown(
        f"""
        <div class="mg-privacy-note">
        🔒 <b>Privacy & security:</b> MailGuard AI never asks for or stores your Gmail password.
        Access uses Google's OAuth 2.0 flow with the minimal <code>gmail.readonly</code> scope —
        nothing can be sent, deleted, or modified in your mailbox. The cached sign-in token is stored
        only in <code>token.json</code> on this machine and is deleted immediately when you disconnect.
        </div>
        """,
        unsafe_allow_html=True,
    )
