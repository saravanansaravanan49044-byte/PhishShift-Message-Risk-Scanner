"""PhishShift CLI risk-review prototype (T6).

  python -m app.scan "Your mailbox will be suspended, verify at bit[.]ly/abc"
  python -m app.scan --file message.txt --json

Never opens, resolves or fetches links (NFR-01). Decision support only (NFR-03).
"""
import argparse
import json
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.models import decide, explain  # noqa: E402
from src.preprocess import defang  # noqa: E402

DISCLAIMER = ("DECISION SUPPORT ONLY - this is an educational triage tool, not a guarantee of safety. "
              "Do not click links; report doubtful messages to your security team.")
MAX_LEN = 5000


def scan(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Message text is empty.")
    if len(text) > MAX_LEN:
        raise ValueError(f"Message is longer than {MAX_LEN} characters.")
    bundle = joblib.load(ROOT / "models" / "phishshift.joblib")
    lr = joblib.load(ROOT / "models" / "tfidf_lr.joblib")
    safe = defang(text)
    p = float(bundle["model"].predict_proba([safe])[0, 1])
    return {"model": bundle["name"], "version": bundle["version"], "risk_probability": round(p, 3),
            "decision": decide(p), "explanation": explain(safe, lr), "disclaimer": DISCLAIMER}


def main():
    ap = argparse.ArgumentParser(description="PhishShift message risk scanner")
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        text = Path(a.file).read_text(encoding="utf-8") if a.file else a.text
        r = scan(text or "")
    except FileNotFoundError:
        print("Error: file not found. Run `python run_all.py` first if models/ is missing."); sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}"); sys.exit(2)
    if a.json:
        print(json.dumps(r, indent=2)); return
    print(f"\nDecision: {r['decision']}   (risk {r['risk_probability']:.0%}, {r['model']} {r['version']})")
    for cue, words in r["explanation"]["rule_cues"].items():
        print(f"  - {cue}: {', '.join(words)}")
    for t in r["explanation"].get("model_terms", []):
        print(f"    term '{t['term']}' weight {t['weight']:+}")
    print("\n" + r["disclaimer"])


if __name__ == "__main__":
    main()
