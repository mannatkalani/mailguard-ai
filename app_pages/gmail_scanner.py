import time

import pandas as pd
import plotly.express as px
import streamlit as st

from src.utils import page_header, status_badge_html, COLORS
from src.classifier import get_classifier
from src.analytics import compute_kpis, top_spam_domains
from src import gmail_auth
from src.fallback_ingestion import load_demo_emails, load_from_csv, load_from_json

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=COLORS["text_dark"]),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
)


def _render_setup_instructions():
    st.warning("Gmail isn't set up for this project yet — a one-time step is needed before you can connect.")
    with st.expander("📋 Show the 2-minute setup steps", expanded=True):
        st.markdown(
            """
            1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** and create a project (or pick an existing one).
            2. Search for **Gmail API** and click **Enable**.
            3. Go to **APIs & Services → OAuth consent screen**. Choose **External**, fill in an app name and your email, and add yourself as a **test user**.
            4. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
               Choose **Desktop app** as the application type.
            5. Click **Download JSON** on the credential you just created.
            6. Rename the downloaded file to **`credentials.json`** and place it in this project's root folder (next to `app.py`).
            7. Refresh this page — you'll see a **Connect Gmail** button appear.

            After this one-time setup, connecting takes a single click — no redirect URLs, no
            copy-pasting keys, nothing else to configure.
            """
        )


def _render_connection_panel():
    if not gmail_auth.is_configured():
        _render_setup_instructions()
        st.caption("In the meantime, you can still explore the product below with Demo Mode.")
        return False

    connected = gmail_auth.is_connected()

    if connected:
        try:
            creds = gmail_auth.get_credentials()
            email = st.session_state.get("gmail_email")
            if not email:
                email = gmail_auth.get_connected_email(creds)
                st.session_state.gmail_email = email
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f'<span class="mg-badge mg-badge-ham">🟢 CONNECTED</span> '
                    f'<span style="color:{COLORS["text_muted"]}">as <b>{email}</b> — read-only access</span>',
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("Disconnect", use_container_width=True, type="secondary"):
                    gmail_auth.disconnect()
                    st.session_state.gmail_email = None
                    st.rerun()
            return True
        except Exception as e:
            st.error(f"Gmail connection needs to be refreshed: {e}")
            gmail_auth.disconnect()
            return False
    else:
        st.markdown(
            f'<span class="mg-badge mg-badge-review">⚪ NOT CONNECTED</span>',
            unsafe_allow_html=True,
        )
        st.caption("Click below — your browser will open Google's sign-in page. Choose your account, click Allow, and you're done.")
        if st.button("🔐  Connect Gmail", type="primary"):
            with st.spinner("Waiting for you to finish signing in with Google in your browser..."):
                try:
                    creds = gmail_auth.get_credentials()
                    st.session_state.gmail_email = gmail_auth.get_connected_email(creds)
                    st.success(f"Connected as {st.session_state.gmail_email}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't complete Google sign-in: {e}")
        return False


def _run_classification(df: pd.DataFrame) -> pd.DataFrame:
    clf = get_classifier()
    preds = clf.predict_batch(df["body"])
    out = pd.concat([df.reset_index(drop=True), preds.reset_index(drop=True)], axis=1)
    out = clf.apply_review_threshold(out, st.session_state.get("review_threshold", 60))
    return out


def _do_scan(raw_df, box):
    steps = ["Cleaning message text", "Vectorizing", "Scoring with ML model", "Building results"]
    bar = box.progress(0, text=steps[0])
    for i, step in enumerate(steps):
        bar.progress(int((i + 1) / len(steps) * 100), text=step)
        time.sleep(0.1)
    results = _run_classification(raw_df)
    st.session_state.scan_results = results
    st.session_state.selected_message_id = None
    bar.empty()
    box.success(f"Scanned {len(results)} messages.")


def _render_fetch_controls(gmail_connected: bool):
    c1, c2 = st.columns([2, 1])
    with c1:
        n = st.slider("Number of emails to scan", 10, 150, st.session_state.get("fetch_count", 40), step=10)
        st.session_state.fetch_count = n
    with c2:
        st.write("")
        st.write("")
        fetch_clicked = st.button("📥  Fetch & Scan Emails", type="primary", use_container_width=True,
                                   disabled=not gmail_connected)
    if fetch_clicked and gmail_connected:
        box = st.container()
        with st.spinner("Fetching messages from Gmail..."):
            creds = gmail_auth.get_credentials()
            raw = gmail_auth.fetch_messages(creds, max_results=n)
        if raw.empty:
            box.warning("No messages found.")
        else:
            _do_scan(raw, box)

    with st.expander("Don't want to connect Gmail right now? Try Demo Mode instead"):
        d1, d2 = st.columns([2, 1])
        with d1:
            dn = st.slider("Demo messages to sample", 10, 100, 40, step=10, key="demo_n")
        with d2:
            st.write("")
            st.write("")
            if st.button("▶️  Run Demo Scan", use_container_width=True):
                demo_df = load_demo_emails(n=dn)
                box = st.container()
                _do_scan(demo_df, box)

        up = st.file_uploader("...or upload a CSV/JSON of emails", type=["csv", "json"])
        if up is not None:
            try:
                df = load_from_json(up) if up.name.endswith(".json") else load_from_csv(up)
                box = st.container()
                _do_scan(df, box)
            except Exception as e:
                st.error(f"Couldn't parse that file: {e}")


def _filter_results(df, status_filter, query):
    out = df.copy()
    if status_filter != "All":
        out = out[out["status"] == status_filter.upper()]
    if query:
        q = query.lower()
        mask = (
            out["sender"].astype(str).str.lower().str.contains(q)
            | out["subject"].astype(str).str.lower().str.contains(q)
            | out["body"].astype(str).str.lower().str.contains(q)
        )
        out = out[mask]
    return out


def _render_results(results: pd.DataFrame):
    kpis = compute_kpis(results)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Emails Scanned", kpis["total"])
    k2.metric("Spam Detected", kpis["spam"])
    k3.metric("Ham Detected", kpis["ham"])
    k4.metric("Spam Rate", f"{kpis['spam_rate']}%")

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("##### Spam vs Ham")
        counts = results["status"].value_counts().reset_index()
        counts.columns = ["status", "count"]
        color_map = {"SPAM": COLORS["spam"], "HAM": COLORS["ham"], "REVIEW": COLORS["review"]}
        fig = px.pie(counts, names="status", values="count", hole=0.6, color="status",
                     color_discrete_map=color_map)
        fig.update_layout(**PLOTLY_LAYOUT, height=280)
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("##### Top Spam Sender Domains")
        dom = top_spam_domains(results)
        if not dom.empty:
            fig = px.bar(dom, x="count", y="domain", orientation="h", color_discrete_sequence=[COLORS["merlot"]])
            fig.update_layout(**PLOTLY_LAYOUT, height=280, xaxis_title="", yaxis_title="")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No spam detected in this batch — nothing to chart.")

    st.write("")
    st.markdown("#### Scan Results")
    c1, c2 = st.columns([1, 2])
    with c1:
        status_filter = st.selectbox("Filter", ["All", "Spam", "Ham", "Review"])
    with c2:
        query = st.text_input("Search sender, subject, or message text")

    filtered = _filter_results(results, status_filter, query)
    st.caption(f"Showing {len(filtered)} of {len(results)} messages")

    display_df = filtered[["sender", "subject", "date", "status", "confidence"]].copy()
    display_df["date"] = pd.to_datetime(display_df["date"], errors="coerce").dt.strftime("%b %d, %H:%M")
    display_df["confidence"] = display_df["confidence"].round(1).astype(str) + "%"
    display_df = display_df.rename(columns={
        "sender": "Sender", "subject": "Subject", "date": "Date", "status": "Prediction", "confidence": "Confidence",
    })

    event = st.dataframe(display_df, use_container_width=True, hide_index=True,
                          on_select="rerun", selection_mode="single-row", height=340)

    csv_bytes = filtered[["sender", "subject", "date", "prediction", "confidence", "status"]].rename(
        columns={"status": "risk_status"}
    ).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  Export Results (CSV)", csv_bytes, file_name="mailguard_gmail_scan.csv", mime="text/csv")

    if event.selection and event.selection.get("rows"):
        idx = event.selection["rows"][0]
        st.session_state.selected_message_id = filtered.iloc[idx]["message_id"]

    _render_investigation(results)


def _render_investigation(df: pd.DataFrame):
    mid = st.session_state.get("selected_message_id")
    if mid is None:
        return
    rows = df[df["message_id"] == mid]
    if rows.empty:
        return
    row = rows.iloc[0]

    st.divider()
    st.markdown("#### 🔍 Message Details")
    left, right = st.columns([2, 1])
    with left:
        st.markdown(
            f"""
            <div class="mg-card">
                <div style="color:{COLORS['text_muted']}; font-size:0.85rem;">Subject</div>
                <div style="font-size:1.1rem; font-weight:700; color:{COLORS['deep_burgundy']}; margin-bottom:0.5rem;">{row['subject']}</div>
                <div style="font-size:0.9rem;"><b>From:</b> {row['sender']}</div>
                <div style="font-size:0.9rem;"><b>Date:</b> {pd.to_datetime(row['date'], errors='coerce')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Message body"):
            st.text(str(row["body"])[:2000])
    with right:
        st.markdown(
            f"""
            <div class="mg-card" style="text-align:center;">
                {status_badge_html(row['status'])}
                <div style="margin-top:0.5rem; font-size:1.6rem; font-weight:700; color:{COLORS['deep_burgundy']};">{row['confidence']:.1f}%</div>
                <div style="color:{COLORS['text_muted']}; font-size:0.8rem;">confidence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    clf = get_classifier()
    contribs = clf.top_features_for_text(row["clean_text"], top_n=6)
    if contribs:
        st.caption("Top words that influenced this decision:")
        st.write(" ".join(f"`{t}` {'🔴' if w > 0 else '🟢'}" for t, w in contribs))


def render():
    page_header("Gmail Scanner", "Fetch & Scan Your Inbox",
                "Connect your Gmail account, choose how many recent messages to scan, and MailGuard AI classifies the whole batch automatically.")

    with st.container():
        st.markdown('<div class="mg-card">', unsafe_allow_html=True)
        gmail_connected = _render_connection_panel()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown('<div class="mg-card">', unsafe_allow_html=True)
        _render_fetch_controls(gmail_connected)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    results = st.session_state.get("scan_results")
    if results is None or len(results) == 0:
        st.info("No scan yet — connect Gmail (or use Demo Mode above) and run a scan to see results here.")
        return

    _render_results(results)
