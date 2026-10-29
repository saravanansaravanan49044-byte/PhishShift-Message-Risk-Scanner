"""Campaign-separated holdout (FR-03), model comparison (FR-02), FPR on legit-urgent & robustness drift (FR-05).

Run: python -m src.train_eval
"""
import json
import random
import re
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .models import MODELS, decide, explain

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "messages_clean.csv"
RES = ROOT / "results"
MODEL_DIR = ROOT / "models"
SEED = 42
HOLDOUT_CAMPAIGNS = ["C5_ceo_soft_ask", "C6_shared_doc_lure", "L4_legit_urgent"]  # mentor may swap (Sec 08)
MODEL_VERSION = "phishshift-v1.0"


def text_of(df):
    return (df["subject_or_title"].fillna("") + " " + df["body_text"] + " domain_" + df["sender_domain_type"]
            + " " + df["sanitized_url_features"].str.replace("|", " url_")).tolist()


def perturb(text: str, rng: random.Random) -> str:
    """Controlled perturbations for AT-03 / CP-5: defang style, punctuation, leetspeak, spacing."""
    ops = [
        lambda t: t.replace("[.]", "(dot)"),
        lambda t: t.replace("hxxps://", "hxxps[:]//"),
        lambda t: re.sub(r"[.!]", "", t),
        lambda t: t.replace("o", "0").replace("a", "@"),
        lambda t: " ".join(t.split()).upper(),
        lambda t: t.replace(" ", "  "),
    ]
    return rng.choice(ops)(text)


def metrics(y, p, thr=0.5):
    yh = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yh, labels=[0, 1]).ravel()
    return {"precision": round(precision_score(y, yh, zero_division=0), 3),
            "recall": round(recall_score(y, yh, zero_division=0), 3),
            "f1": round(f1_score(y, yh, zero_division=0), 3),
            "roc_auc": round(roc_auc_score(y, p), 3) if len(set(y)) > 1 else None,
            "fpr": round(fp / max(1, fp + tn), 3), "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def main():
    df = pd.read_csv(DATA, keep_default_na=False)
    df["label"] = df["label"].astype(int)
    test_mask = df["campaign_group"].isin(HOLDOUT_CAMPAIGNS)
    train_pool, camp_test = df[~test_mask], df[test_mask]
    # also a random in-distribution split, to contrast with campaign split (CP-3)
    tr, rnd_test = train_test_split(train_pool, test_size=0.25, random_state=SEED, stratify=train_pool["label"])
    assert not set(tr["campaign_group"]) & set(camp_test["campaign_group"]), "campaign leakage!"

    Xtr, ytr = text_of(tr), tr["label"].values
    rng = random.Random(SEED)
    Xpert = [perturb(t, rng) for t in text_of(camp_test)]
    rows, fitted, preds = [], {}, {}
    for name, ctor in MODELS.items():
        m = ctor().fit(Xtr, ytr); fitted[name] = m
        p_rnd = m.predict_proba(text_of(rnd_test))[:, 1]
        p_camp = m.predict_proba(text_of(camp_test))[:, 1]
        p_pert = m.predict_proba(Xpert)[:, 1]
        preds[name] = p_camp
        legit_urg = (camp_test["campaign_group"] == "L4_legit_urgent").values
        dec = np.array([decide(x) for x in p_camp])
        confident = dec != "ABSTAIN_REVIEW"
        r = {"model": name,
             **{f"random_{k}": v for k, v in metrics(rnd_test["label"].values, p_rnd).items() if k in ("f1", "roc_auc", "fpr")},
             **{f"campaign_{k}": v for k, v in metrics(camp_test["label"].values, p_camp).items()},
             "fpr_legit_urgent": round(float((p_camp[legit_urg] >= 0.5).mean()), 3),
             "perturbed_f1": metrics(camp_test["label"].values, p_pert)["f1"],
             "mean_abs_prob_drift": round(float(np.abs(p_pert - p_camp).mean()), 3),
             "abstain_rate": round(float((~confident).mean()), 3),
             "accuracy_on_non_abstained": round(float(((p_camp[confident] >= 0.5) == camp_test["label"].values[confident]).mean()), 3) if confident.any() else None}
        rows.append(r)
    table = pd.DataFrame(rows)
    RES.mkdir(exist_ok=True); MODEL_DIR.mkdir(exist_ok=True)
    table.to_csv(RES / "results_table.csv", index=False)

    # choose best by campaign F1 minus legit-urgent FPR
    best = max(rows, key=lambda r: r["campaign_f1"] - r["fpr_legit_urgent"])["model"]
    joblib.dump({"model": fitted[best], "name": best, "version": MODEL_VERSION,
                 "trained": datetime.utcnow().isoformat(), "holdout": HOLDOUT_CAMPAIGNS}, MODEL_DIR / "phishshift.joblib")
    joblib.dump(fitted["tfidf_lr"], MODEL_DIR / "tfidf_lr.joblib")

    # error analysis (CP-4): missed phishing + flagged legit, per subset
    ct = camp_test.assign(p=preds[best])
    missed = ct[(ct.label == 1) & (ct.p < 0.5)].sort_values("p").head(3)
    flagged = ct[(ct.label == 0) & (ct.p >= 0.5)].sort_values("p", ascending=False).head(3)
    errs = []
    for kind, sub in [("missed_phishing", missed), ("flagged_legitimate", flagged)]:
        for _, r in sub.iterrows():
            errs.append({"type": kind, "message_id": r.message_id, "campaign": r.campaign_group,
                         "prob": round(r.p, 3), "text": r.body_text, "explanation": explain(r.body_text, fitted["tfidf_lr"])})
    (RES / "error_examples.json").write_text(json.dumps(errs, indent=2))
    per_campaign = ct.groupby("campaign_group").apply(lambda g: pd.Series({
        "n": len(g), "mean_prob": round(g.p.mean(), 3), "flag_rate": round((g.p >= 0.5).mean(), 3)}), include_groups=False)
    per_campaign.to_csv(RES / "per_campaign_breakdown.csv")

    log = {"timestamp": datetime.utcnow().isoformat(), "seed": SEED, "version": MODEL_VERSION,
           "train_rows": len(tr), "random_test_rows": len(rnd_test), "campaign_test_rows": len(camp_test),
           "train_campaigns": sorted(tr.campaign_group.unique()), "holdout_campaigns": HOLDOUT_CAMPAIGNS,
           "selected_model": best, "abstain_band": [0.35, 0.65]}
    with (RES / "experiment_log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")
    pd.set_option("display.width", 250)
    print(table.to_string(index=False)); print("\nper campaign:\n", per_campaign); print("\nselected:", best)


if __name__ == "__main__":
    main()
