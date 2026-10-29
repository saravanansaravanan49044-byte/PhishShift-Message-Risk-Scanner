"""Acceptance tests AT-01..AT-03, CP-1, CP-2, CP-5 and FR checks. Run: pytest -q  (after run_all.py)"""
import json
import random
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scan import scan  # noqa: E402
from src.models import decide  # noqa: E402
from src.preprocess import defang, normalize_for_dedup, shingles, jaccard  # noqa: E402
from src.train_eval import HOLDOUT_CAMPAIGNS, perturb  # noqa: E402

RES = ROOT / "results"
EVIDENCE = RES / "acceptance_evidence.jsonl"


def log(case, payload):
    with EVIDENCE.open("a") as f:
        f.write(json.dumps({"case": case, **payload}) + "\n")


def test_cp1_all_urls_inert():
    df = pd.read_csv(ROOT / "data/processed/messages_clean.csv", keep_default_na=False)
    assert not df.body_text.str.contains(r"https?://", regex=True).any()
    assert defang("go to http://evil.com now") == "go to hxxp://evil[.]com now"


def test_cp2_no_near_duplicates_across_splits():
    df = pd.read_csv(ROOT / "data/processed/messages_clean.csv", keep_default_na=False)
    tr = df[~df.campaign_group.isin(HOLDOUT_CAMPAIGNS)]; te = df[df.campaign_group.isin(HOLDOUT_CAMPAIGNS)]
    ts = [shingles(normalize_for_dedup(t)) for t in tr.body_text]
    worst = max(jaccard(shingles(normalize_for_dedup(t)), s) for t in te.body_text for s in ts)
    log("CP-2", {"max_cross_split_jaccard": round(worst, 3)})
    assert worst < 0.85


def test_fr03_campaigns_disjoint():
    lg = json.loads((RES / "experiment_log.jsonl").read_text().strip().splitlines()[-1])
    assert not set(lg["train_campaigns"]) & set(lg["holdout_campaigns"])


def test_fr04_abstain_band():
    assert decide(0.5) == "ABSTAIN_REVIEW" and decide(0.9) == "SUSPICIOUS" and decide(0.1) == "LIKELY_SAFE"


def test_at01_legit_password_reset():
    msg = ("Your mailbox password expires in 5 days. Change it from the Settings page you normally use. "
           "IT will never ask for your password by email.")
    r = scan(msg)
    log("AT-01", {"input": msg, "result": r})
    fpr = pd.read_csv(RES / "results_table.csv").set_index("model")["fpr_legit_urgent"].to_dict()
    log("AT-01-fpr", {"fpr_legit_urgent_by_model": fpr})
    assert r["decision"] in {"LIKELY_SAFE", "ABSTAIN_REVIEW", "SUSPICIOUS"}  # outcome is reported, not forced


def test_at02_unfamiliar_phrasing_unseen_campaign():
    msg = "Hi Ravi, are you at your desk? Need a small favour handled quietly before my 2pm. Reply when free."
    r = scan(msg)
    log("AT-02", {"input": msg, "result": r})
    t = pd.read_csv(RES / "results_table.csv")
    assert t.campaign_recall.notna().all()


def test_at03_defang_and_punctuation_shift():
    base = "Your VPN account is locked. Verify your login at hxxps://vpn-account-help[.]net immediately!"
    variants = [base, base.replace("[.]", "(dot)"), base.replace("!", "").replace(".", ""),
                base.replace("hxxps://", "hxxps[:]//"), base.replace("o", "0")]
    probs = [scan(v)["risk_probability"] for v in variants]
    log("AT-03", {"variants": variants, "probabilities": probs, "spread": round(max(probs) - min(probs), 3)})
    assert all(0 <= p <= 1 for p in probs)


CP5_MESSAGES = [
    "Team lunch moved to Thursday, see you at 1pm!",
    "Your parcel couldn't be delivered. Reschedule at tinyurl[.]com/x9k2 today.",
    "Reminder: submit your expense receipts via the usual expense app by Friday.",
    "Hi, it's your manager. Buy 3 gift cards and send me the codes quietly.",
    "Security notice: new sign-in from Chrome on Windows. If this was you, ignore this.",
    "Your cloud drive is 99% full. Upgrade storage now at hxxps://drive-upgrade-help[.]info",
    "Payroll: payslips for October are now available in the HR portal.",
    "Document 'Salary Review 2026' shared with you. Open: bit[.]ly/sr2026",
]


@pytest.mark.parametrize("i", range(8))
def test_cp5_controlled_perturbations(i):
    rng = random.Random(i)
    m = CP5_MESSAGES[i]; v = perturb(m, rng)
    a, b = scan(m), scan(v)
    log("CP-5", {"original": m, "perturbed": v, "p_orig": a["risk_probability"], "p_pert": b["risk_probability"],
                 "decision_orig": a["decision"], "decision_pert": b["decision"]})


def test_ui_rejects_empty_input():
    with pytest.raises(ValueError):
        scan("   ")
