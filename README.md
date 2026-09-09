
Text is cleaned using the same pipeline as the original research
notebook: lowercase → URLs/emails/digits replaced with tokens →
non-alphabetic characters stripped → English stopwords removed →
Porter stemming.

## Model Performance

Trained and evaluated on 35,631 labeled messages (Enron corporate email +
SMS spam corpora), 80/20 train/test split:

| Model                 | Test Accuracy | AUC   |
|------------------------|--------------:|------:|
| **LR + CountVectorizer** (production) | **97.08%** | **0.994** |
| LR + TF-IDF             | 96.76% | 0.995 |
| NB + CountVectorizer     | 93.71% | 0.991 |
| NB + TF-IDF              | 96.07% | 0.995 |

ML predictions are probabilistic — MailGuard AI does not claim guaranteed
or 100% spam detection.

## Tech Stack

Python · Streamlit · scikit-learn · NLTK · Pandas · Plotly · Google API Client

## Local Setup

```bash
git clone https://github.com/<your-username>/mailguard-ai.git
cd mailguard-ai

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords')"

streamlit run app.py
```

Trained model artifacts are already included in `models/` — no training
step required. (`train.py` is included if you want to retrain from scratch.)

## Gmail Setup (one-time, ~2 minutes)

This is the only setup Google requires of any app that talks to Gmail —
do it once, and every connection after is a single click.

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** → create or select a project
2. Search **Gmail API** → click **Enable**
3. Go to **APIs & Services → OAuth consent screen** (may appear as **"Google Auth Platform"**) → choose **External** → add yourself as a **test user**
4. Go to **Credentials → Create Credentials → OAuth client ID** → application type **Desktop app**
5. Click **Download JSON**, rename it to `credentials.json`, place it in the project root (next to `app.py`)
6. Run the app → go to **Gmail Scanner** → click **Connect Gmail** → your browser opens Google's sign-in automatically → choose your account → **Allow**

A `token.json` is created automatically to remember your sign-in — every
future run reconnects instantly with no browser popup, until you click
**Disconnect** or delete `token.json`.

> **Note:** while the app is in "Testing" mode in Google Cloud (the
> default), only accounts added as test users can sign in. That's expected
> for a personal project — no need to publish it.

## Project Structure

```text
mailguard-ai/
├── app.py                    # entry point — nav, session state, routing
├── train.py                  # reproduces the model training from the research notebook
├── requirements.txt
├── credentials.json          # you add this (gitignored, never committed)
├── token.json                # created automatically after first sign-in (gitignored)
│
├── models/                   # pre-trained artifacts
│   ├── model.joblib
│   ├── vectorizer.joblib
│   └── metadata.json
│
├── src/
│   ├── preprocessing.py      # notebook-matching NLP cleaning pipeline
│   ├── classifier.py         # loads model, runs predictions
│   ├── gmail_auth.py         # one-click Gmail OAuth flow + rate-limit handling
│   ├── fallback_ingestion.py # demo data + CSV/JSON upload
│   ├── analytics.py          # KPI + chart helpers
│   └── utils.py              # wine theme + shared UI components
│
├── app_pages/
│   ├── overview.py
│   ├── gmail_scanner.py      # primary workflow
│   ├── quick_test.py
│   └── settings.py
│
└── data/
    └── spam_dataset.csv      # training data (used by train.py and Demo Mode)
```

## Security & Privacy

- Never asks for or stores your Gmail password
- Requests only the read-only `gmail.readonly` scope — nothing can be sent, deleted, or modified in your mailbox
- `credentials.json` and `token.json` are local-only files, `.gitignore`'d, never uploaded anywhere
- Message bodies are processed in-memory for classification only, never logged

## Future Improvements

- Transformer-based classifier (e.g. DistilBERT) as an additional option
- Continual / feedback-based retraining from human review decisions
- Phishing-specific detection and malicious URL analysis
- Sender reputation scoring
- Attachment risk analysis

---

<p align="center">Built as a demonstration of an end-to-end NLP/ML product — from a research notebook to a deployed, explainable classifier.</p>
