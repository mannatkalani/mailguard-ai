import streamlit as st

from src.utils import page_header, status_badge_html, COLORS
from src.classifier import get_classifier


def render():
    page_header("Quick Test", "Try a Single Message",
                "A small secondary tool for testing the classifier on one message. The primary workflow is Gmail Scanner.")

    clf = get_classifier()
    st.caption(f"Model: **{clf.model_name}** · {clf.metadata['model_comparison'][clf.model_name]['test_accuracy']*100:.2f}% test accuracy")

    examples = [
        "Congratulations! You've WON a $1000 gift card. Click here to claim NOW!!!",
        "Hey, are we still meeting for lunch tomorrow at noon?",
        "URGENT: Your account will be suspended. Verify your password immediately.",
    ]
    cols = st.columns(3)
    for c, ex in zip(cols, examples):
        if c.button(ex[:26] + "...", use_container_width=True):
            st.session_state.quick_test_text = ex

    text = st.text_area("Message text", value=st.session_state.get("quick_test_text", ""), height=140,
                        placeholder="Paste or type a message to classify...")

    if st.button("Classify Message", type="primary"):
        if not text.strip():
            st.warning("Enter a message first.")
        else:
            result = clf.predict_one(text)
            threshold = st.session_state.get("review_threshold", 60)
            status = "REVIEW" if result["confidence"] < threshold else result["prediction"]

            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(
                    f"""
                    <div class="mg-card" style="text-align:center;">
                        {status_badge_html(status)}
                        <div style="margin-top:0.6rem; font-size:1.6rem; font-weight:700; color:{COLORS['deep_burgundy']};">{result['confidence']:.1f}%</div>
                        <div style="color:{COLORS['text_muted']}; font-size:0.8rem;">confidence</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                contribs = clf.top_features_for_text(result["clean_text"], top_n=8)
                if contribs:
                    st.caption("Top contributing tokens:")
                    for token, w in contribs:
                        st.write(f"`{token}` — {'🔴 spam' if w > 0 else '🟢 ham'} ({w:+.2f})")
                else:
                    st.caption("Feature importance unavailable for this model.")
