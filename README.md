# 🍷 MailGuard AI — Gmail Spam Screener

A lean, wine-themed Streamlit app that connects directly to your Gmail account
and automatically screens your inbox for spam using a trained NLP/ML pipeline.

Connecting Gmail is a **one-click sign-in** — Google's own screen handles the
login, no password is ever typed into this app, and reconnecting on future
runs is instant (no repeated logins).

## Features

- **One-click Gmail connection** (Google's official OAuth sign-in, read-only access)
- **Automatic batch scanning** — pick how many recent emails to scan, click once
- **Spam / Ham / Review** classification with a configurable confidence threshold
- **Two focused charts** — Spam vs Ham split, and top spam sender domains (kept deliberately minimal)
- **Message investigation** — click any row to see the message and the top words that drove the decision
- **CSV export** of scan results
- **Demo Mode & file upload** as fallback ways to try it without connecting Gmail
- **Quick Test** — secondary single-message tester

## Tech Stack

Python · Streamlit · scikit-learn · NLTK · Pandas · Plotly · Google API Client

## Model

Production model: **LR + CountVectorizer** (97.08% test accuracy, AUC 0.994) — see `models/metadata.json` for full metrics.
Trained on 35,631 labeled messages (Enron corporate email + SMS spam corpora),
using the same NLP cleaning pipeline as the original research notebook
(lowercase → URL/email/digit tokens → stopword removal → Porter stemming).

## Local Setup

```bash
cd gmail-spam-screener
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords')"
streamlit run app.py
```

The trained model artifacts are already included in `models/`, so no training
step is required. (`train.py` is included if you want to retrain from scratch.)

Open the app and you'll land on the Overview page — click through to **Gmail
Scanner**, or just try **Demo Mode** immediately with zero setup.

## Gmail Setup (one-time, ~2 minutes)

This is the only setup Google requires of any app that talks to Gmail. Do it
once, and every connection after that is a single click.

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** and create a project (or use an existing one).
2. Search for **Gmail API** in the top search bar and click **Enable**.
3. Go to **APIs & Services → OAuth consent screen**. Choose **External**, fill in an app name and your email address, and add yourself under **Test users**.
4. Go to **APIs & Services → Credentials → + Create Credentials → OAuth client ID**.
5. Application type: **Desktop app**. Give it any name (e.g. "MailGuard AI"). Click **Create**.
6. Click **Download JSON** on the credential that was just created.
7. Rename the downloaded file to exactly **`credentials.json`** and place it in this project's root folder — the same folder as `app.py`.
8. Run the app and go to **Gmail Scanner**. Click **Connect Gmail** — your browser opens Google's sign-in page automatically. Choose your account, click **Allow**, and the tab closes itself.

That's it. A `token.json` file is created automatically to remember your
sign-in — every future run reconnects instantly with no browser popup, until
you click **Disconnect** or delete `token.json`.

**Note:** while your app is in "Testing" mode in Google Cloud (the default),
only the test users you added in step 3 can sign in. That's expected for a
personal/demo project — you don't need to publish the app.

## Security & Privacy

- The app never asks for or stores your Gmail password.
- Only the read-only `gmail.readonly` scope is requested — nothing can be sent, deleted, or modified in your mailbox.
- `credentials.json` and `token.json` are local files, listed in `.gitignore`, and never uploaded anywhere.
- Message bodies are processed in-memory for classification only.

## Project Structure

```text
gmail-spam-screener/
├── app.py
├── train.py
├── requirements.txt
├── credentials.json        ← you add this (see Gmail Setup above), gitignored
├── token.json               ← created automatically after first sign-in, gitignored
│
├── models/                  # pre-trained artifacts
│   ├── model.joblib
│   ├── vectorizer.joblib
│   └── metadata.json
│
├── src/
│   ├── preprocessing.py     # notebook-matching text cleaning
│   ├── classifier.py        # loads model, runs predictions
│   ├── gmail_auth.py        # the one-click Gmail OAuth flow
│   ├── fallback_ingestion.py # demo data + file upload
│   ├── analytics.py         # small KPI/chart helpers
│   └── utils.py             # wine theme + shared UI components
│
├── app_pages/
│   ├── overview.py
│   ├── gmail_scanner.py     # primary workflow
│   ├── quick_test.py
│   └── settings.py
│
└── data/
    └── spam_dataset.csv     # training data (used by train.py and Demo Mode)
```

ML predictions are probabilistic — MailGuard AI does not claim guaranteed or
100% spam detection.
