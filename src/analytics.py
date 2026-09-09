import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    if total == 0:
        return {"total": 0, "spam": 0, "ham": 0, "review": 0, "spam_rate": 0.0, "avg_confidence": 0.0}
    spam = int((df["status"] == "SPAM").sum())
    ham = int((df["status"] == "HAM").sum())
    review = int((df["status"] == "REVIEW").sum())
    avg_conf = float(df["confidence"].mean())
    return {
        "total": total, "spam": spam, "ham": ham, "review": review,
        "spam_rate": round(100 * spam / total, 1),
        "avg_confidence": round(avg_conf, 1),
    }


def top_spam_domains(df: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    d = df[df["status"] == "SPAM"].copy()
    if d.empty:
        return pd.DataFrame(columns=["domain", "count"])
    d["domain"] = d["sender"].astype(str).str.extract(r"@([\w\.-]+)").fillna("unknown")
    out = d["domain"].value_counts().head(top_n).rename_axis("domain").reset_index(name="count")
    return out
