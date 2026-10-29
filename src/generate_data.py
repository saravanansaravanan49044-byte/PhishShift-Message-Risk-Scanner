"""Generate a locally-authored, fully synthetic corpus (no real people, credentials or live URLs).

Every URL is defanged (hxxp://, [.] ) and only *features* of it are kept, satisfying NFR-01/NFR-02.
Run: python -m src.generate_data
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 7
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "messages_raw.csv"

NAMES = ["Alex", "Priya", "Sam", "Meera", "Jordan", "Ravi", "Taylor", "Anu", "Chris", "Kavya"]
TEAMS = ["Finance", "HR", "IT Support", "Payroll", "Facilities", "Security Office"]
SERVICES = ["mailbox", "VPN", "payroll portal", "cloud drive", "HR portal", "expense app"]
AMOUNTS = ["$120", "$450", "$1,250", "$89", "$3,400"]
SHORT = ["bit[.]ly/{c}", "tinyurl[.]com/{c}", "t[.]co/{c}", "is[.]gd/{c}"]
BAD_DOM = ["secure-{s}-verify[.]com", "{s}-account-help[.]net", "login-{s}[.]support", "{s}update[.]info"]
GOOD_DOM = ["intranet[.]example-corp[.]com", "hr[.]example-corp[.]com", "it[.]example-corp[.]com"]

# Phishing campaigns. C1-C4 = "classic" keyword-heavy (training); C5-C6 = novel tactics (held out).
PHISH = {
    "C1_account_suspend": [
        "URGENT: Your {svc} account will be suspended. Verify your password now at {url} to avoid losing access.",
        "Dear user, your {svc} has been locked due to suspicious activity. Click here immediately: {url}",
        "Final warning! {svc} password expires today. Confirm your login credentials at {url}",
    ],
    "C2_invoice_fraud": [
        "Invoice overdue: payment of {amt} required within 24 hours. Download invoice and pay at {url}",
        "Your payment of {amt} failed. Update billing details urgently via {url} or service will stop.",
        "ACTION REQUIRED: outstanding balance {amt}. Click the secure link {url} to settle now.",
    ],
    "C3_prize": [
        "Congratulations {name}! You have won a {amt} gift card. Claim your prize now at {url}",
        "You are selected for a free reward worth {amt}. Click {url} and enter your details to claim.",
    ],
    "C4_payroll_divert": [
        "Payroll alert: confirm your bank account details at {url} or your salary will be delayed.",
        "Your salary of {amt} is on hold. Verify identity and bank info immediately: {url}",
    ],
    # --- novel / unfamiliar phrasing (AT-02) ---
    "C5_ceo_soft_ask": [
        "Hi {name}, are you at your desk? I need a small favour handled quietly before my next meeting. Reply when free. - sent from my phone",
        "{name}, quick one - can you pick up a few store cards for a client thank-you? I'll reimburse. Keep it between us for now.",
        "Hey {name}, in back-to-back calls. Could you look at the doc I shared {url} and tell me your thoughts by lunch?",
    ],
    "C6_shared_doc_lure": [
        "{name} shared a file with you: 'Q3 bonus allocations'. Open in browser {url}",
        "A document is waiting for your signature from {team}. Review it here {url} - expires end of day.",
        "New voicemail (0:42) from {team}. Listen online: {url}",
    ],
}
# Legitimate messages. L1-L3 training; L4 = legitimate URGENT / password / payroll (held out, FR-05, AT-01).
LEGIT = {
    "L1_meetings": [
        "Hi {name}, moving our sync to 3pm tomorrow. Agenda is on the team wiki. Thanks!",
        "Reminder: {team} all-hands is on Friday in room 4B. Snacks provided.",
        "Can you share the slides from today's review? No rush, end of week is fine.",
    ],
    "L2_it_notice": [
        "IT Support: scheduled maintenance for {svc} on Saturday 2-4am. No action needed.",
        "The new printer on floor 3 is now available. Drivers install automatically.",
    ],
    "L3_hr_info": [
        "{team} newsletter: welcome our new joiners and see the updated holiday calendar on the intranet.",
        "Thanks for completing the training module, {name}. Your certificate is in the HR portal.",
    ],
    "L4_legit_urgent": [
        "Your {svc} password expires in 5 days. Change it from the Settings page you normally use. IT will never ask for your password by email.",
        "Payroll reminder: timesheets are due today by 5pm so salaries are processed on time. Submit via the usual HR portal.",
        "URGENT: fire drill at 11am today. Please follow wardens to the assembly point.",
        "Security notice: we detected a login from a new device. If this was you, no action is needed. Otherwise contact the helpdesk on extension 4400.",
    ],
}
CHANNELS = ["email", "sms"]


def fill(tpl: str, rng: random.Random, phish: bool) -> tuple[str, str, str]:
    code = "".join(rng.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(6))
    svc = rng.choice(SERVICES)
    if phish:
        url = rng.choice(SHORT).format(c=code) if rng.random() < 0.5 else "hxxps://" + rng.choice(BAD_DOM).format(s=svc.split()[0].lower())
        dtype = rng.choice(["lookalike", "free_mail", "unknown_external"])
    else:
        url = "hxxps://" + rng.choice(GOOD_DOM)
        dtype = "internal"
    text = tpl.format(name=rng.choice(NAMES), team=rng.choice(TEAMS), svc=svc, amt=rng.choice(AMOUNTS), url=url)
    # light noise so near-duplicates exist (FR-01)
    if rng.random() < 0.3:
        text = text.replace(".", " .") if rng.random() < 0.5 else text + " "
    feats = url_features(url) if "{url}" in tpl else "none"
    return text, dtype, feats


def url_features(url: str) -> str:
    u = url.lower()
    f = []
    if any(s in u for s in ["bit[.]ly", "tinyurl", "t[.]co", "is[.]gd"]):
        f.append("shortener")
    if u.startswith("hxxps") or u.startswith("hxxp"):
        f.append("defanged")
    if "example-corp" in u:
        f.append("internal_domain")
    elif "-" in u:
        f.append("hyphen_domain")
    return "|".join(f) or "none"


def main():
    rng = random.Random(SEED)
    rows, mid = [], 0
    start = date(2026, 1, 5)
    for label, groups, n in [(1, PHISH, 42), (0, LEGIT, 45)]:
        for camp, tpls in groups.items():
            for _ in range(n):
                tpl = rng.choice(tpls)
                body, dtype, feats = fill(tpl, rng, bool(label))
                ch = rng.choice(CHANNELS)
                subj = (body.split(".")[0][:50]) if ch == "email" else ""
                mid += 1
                rows.append({
                    "message_id": f"M{mid:04d}", "channel": ch, "subject_or_title": subj,
                    "body_text": body, "sanitized_url_features": feats, "sender_domain_type": dtype,
                    "label": label, "campaign_group": camp,
                    "collected_date": (start + timedelta(days=rng.randint(0, 200))).isoformat(),
                    "source": "locally_authored_synthetic_v1", "license": "CC0 (team-authored)",
                })
    # inject a few schema issues to demonstrate cleaning (T2)
    rows[3]["channel"] = "EMAIL "
    rows[10]["sender_domain_type"] = ""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
