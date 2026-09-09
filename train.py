"""
Offline training script.

Reproduces the exact model-comparison workflow from the research notebook
(spam.ipynb) on data/spam_dataset.csv, then serializes the winning
production model + vectorizer + metadata to models/ with joblib so the
Streamlit app never has to retrain on startup.

Run once:  python train.py
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from src.preprocessing import clean_text

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "spam_dataset.csv"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)


def main():
    t0 = time.time()
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "label"]).reset_index(drop=True)

    dataset_stats = {
        "total_messages": int(len(df)),
        "ham_count": int((df["label"] == "ham").sum()),
        "spam_count": int((df["label"] == "spam").sum()),
        "source_counts": df["source"].value_counts().to_dict() if "source" in df.columns else {},
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_text": int(df["text"].duplicated().sum()),
        "missing_values": int(df.isnull().sum().sum()),
    }
    print("Dataset stats:", dataset_stats)

    print("Cleaning text (this mirrors the notebook's clean_text pipeline)...")
    df["clean_text"] = df["text"].apply(clean_text)
    df["label_num"] = (df["label"] == "spam").astype(int)

    X = df["clean_text"]
    y = df["label_num"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = {}
    fitted = {}

    # ---- Vectorizers ----
    cv_vec = CountVectorizer()
    X_train_cv = cv_vec.fit_transform(X_train)
    X_test_cv = cv_vec.transform(X_test)

    tfidf_vec = TfidfVectorizer()
    X_train_tfidf = tfidf_vec.fit_transform(X_train)
    X_test_tfidf = tfidf_vec.transform(X_test)

    combos = [
        ("LR + CountVectorizer", LogisticRegression(max_iter=1000), X_train_cv, X_test_cv, cv_vec),
        ("LR + TF-IDF", LogisticRegression(max_iter=1000), X_train_tfidf, X_test_tfidf, tfidf_vec),
        ("NB + CountVectorizer", MultinomialNB(), X_train_cv, X_test_cv, cv_vec),
        ("NB + TF-IDF", MultinomialNB(), X_train_tfidf, X_test_tfidf, tfidf_vec),
    ]

    for name, model, Xtr, Xte, vec in combos:
        print(f"Training {name} ...")
        model.fit(Xtr, y_train)
        preds = model.predict(Xte)
        probs = model.predict_proba(Xte)[:, 1]

        acc = accuracy_score(y_test, preds)
        auc = roc_auc_score(y_test, probs)
        prec = precision_score(y_test, preds)
        rec = recall_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        cm = confusion_matrix(y_test, preds).tolist()
        fpr, tpr, _ = roc_curve(y_test, probs)

        results[name] = {
            "test_accuracy": acc,
            "auc": auc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "confusion_matrix": cm,
            "roc_fpr": fpr.tolist()[::max(1, len(fpr) // 200)],
            "roc_tpr": tpr.tolist()[::max(1, len(tpr) // 200)],
        }
        fitted[name] = (model, vec)
        print(f"  {name}: acc={acc:.4f} auc={auc:.4f} f1={f1:.4f}")

    # ---- Pick production model: best test accuracy (matches notebook: LR + CountVectorizer) ----
    best_name = max(results, key=lambda k: results[k]["test_accuracy"])
    best_model, best_vec = fitted[best_name]
    print(f"\nProduction model selected: {best_name}")

    joblib.dump(best_model, MODELS_DIR / "model.joblib")
    joblib.dump(best_vec, MODELS_DIR / "vectorizer.joblib")

    # Top spam-indicative tokens for the LR+Count model, for the "Top suspicious
    # words" chart and the model-level explainability panel.
    top_spam_terms = []
    if hasattr(best_model, "coef_"):
        vocab = best_vec.get_feature_names_out()
        coefs = best_model.coef_[0]
        order = coefs.argsort()[::-1][:30]
        top_spam_terms = [{"term": vocab[i], "weight": float(coefs[i])} for i in order]

    metadata = {
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "training_seconds": round(time.time() - t0, 1),
        "production_model": best_name,
        "vectorizer_type": "CountVectorizer" if "Count" in best_name else "TF-IDF",
        "model_type": "LogisticRegression" if "LR" in best_name else "MultinomialNB",
        "dataset_stats": dataset_stats,
        "model_comparison": results,
        "top_spam_terms": top_spam_terms,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }

    with open(MODELS_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone in {time.time() - t0:.1f}s. Artifacts written to {MODELS_DIR}/")


if __name__ == "__main__":
    main()
