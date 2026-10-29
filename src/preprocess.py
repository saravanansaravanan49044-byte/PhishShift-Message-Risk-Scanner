"""Sanitize (CP-1), clean schema (T2) and near-duplicate removal (FR-01, CP-2).

Raw file is never modified; outputs go to data/processed and results/.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "messages_raw.csv"
PROC = ROOT / "data" / "processed" / "messages_clean.csv"
RES = ROOT / "results"

LIVE_URL = re.compile(r"\bhttps?://", re.I)


def defang(text: str) -> str:
    """Make any live URL inert: http->hxxp, '.' in host -> [.]"""
    def _fix(m):
        return m.group(0).replace("http", "hxxp")
    text = LIVE_URL.sub(_fix, text)
    text = re.sub(r"(?<=[a-z0-9])\.(?=(com|net|org|info|io|ly|co|gd|support)\b)", "[.]", text, flags=re.I)
    return text


def normalize_for_dedup(text: str) -> str:
    t = text.lower()
    t = re.sub(r"hxxps?://\S+|\S+\[\.\]\S+", " URL ", t)
    t = re.sub(r"\$[\d,]+", " AMT ", t)
    t = re.sub(r"[^a-z ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def shingles(t: str, k: int = 3) -> set:
    w = t.split()
    return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b))


def dedup(df: pd.DataFrame, thr: float = 0.85) -> tuple[pd.DataFrame, list]:
    """Greedy near-duplicate removal. Names are also masked so templates collapse."""
    names = r"\b(alex|priya|sam|meera|jordan|ravi|taylor|anu|chris|kavya)\b"
    keys = df["body_text"].map(lambda s: re.sub(names, "NAME", normalize_for_dedup(s)))
    sh = [shingles(k) for k in keys]
    kept, removed = [], []
    for i in range(len(df)):
        dup_of = next((j for j in kept if jaccard(sh[i], sh[j]) >= thr), None)
        if dup_of is None:
            kept.append(i)
        else:
            removed.append({"removed": df.iloc[i]["message_id"], "duplicate_of": df.iloc[dup_of]["message_id"],
                            "similarity": round(jaccard(sh[i], sh[dup_of]), 3)})
    return df.iloc[kept].reset_index(drop=True), removed


def main():
    raw = pd.read_csv(RAW, dtype=str, keep_default_na=False)
    log = {"raw_rows": len(raw)}
    df = raw.copy()
    df["channel"] = df["channel"].str.strip().str.lower()
    log["empty_sender_domain_type"] = int((df["sender_domain_type"] == "").sum())
    df.loc[df["sender_domain_type"] == "", "sender_domain_type"] = "unknown"
    before = df["body_text"].copy()
    df["body_text"] = df["body_text"].map(defang)
    log["urls_defanged_now"] = int((before != df["body_text"]).sum())
    log["live_urls_remaining"] = int(df["body_text"].str.contains(LIVE_URL).sum())
    df["label"] = df["label"].astype(int)
    df, removed = dedup(df)
    log["after_dedup_rows"] = len(df)
    log["near_duplicates_removed"] = len(removed)
    log["rows_per_campaign"] = df["campaign_group"].value_counts().to_dict()
    PROC.parent.mkdir(parents=True, exist_ok=True); RES.mkdir(exist_ok=True)
    df.to_csv(PROC, index=False)
    pd.DataFrame(removed).to_csv(RES / "dedup_proof.csv", index=False)
    (RES / "sanitization_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    assert log["live_urls_remaining"] == 0, "CP-1 failed: live URL present"


if __name__ == "__main__":
    main()
