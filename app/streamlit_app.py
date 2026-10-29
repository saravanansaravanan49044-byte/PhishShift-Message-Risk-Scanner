"""PhishShift: polished Streamlit UI for educational message-risk triage."""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.scan import DISCLAIMER, scan  # noqa: E402

st.set_page_config(
    page_title="PhishShift | Message Risk Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.hero h1 { font-family:'Space Grotesk',sans-serif;font-size:clamp(1.8rem,3.5vw,2.65rem);line-height:1.12;letter-spacing:-1px;color:white;margin:0 0 12px; }
.hero p { color:#d8e7f0;font-size:1rem;line-height:1.65;max-width:700px;margin:0; }
.pill-row { display:flex;flex-wrap:wrap;gap:8px;margin-top:20px; }
.pill { border:1px solid #ffffff36;background:#ffffff12;border-radius:999px;padding:7px 11px;font-size:.78rem;color:#f2fbff; }
.section-title { font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.12rem;color:#182b42;margin:.45rem 0 .25rem; }
.section-hint { color:#718096;font-size:.88rem;margin-bottom:.8rem; }
.panel { background:#ffffffd9;border:1px solid #e2eaf1;border-radius:20px;padding:22px 23px;box-shadow:0 8px 24px #1b34450a; }
.stTextArea textarea { background:#fbfdff!important;border:1px solid #d9e4ec!important;border-radius:13px!important;color:#172033!important;font-size:.96rem!important;line-height:1.6!important; }
.stTextArea textarea:focus { border-color:#0f9d91!important;box-shadow:0 0 0 2px #0f9d9120!important; }
.stButton>button { border-radius:12px;border:1px solid #dce6ed;font-weight:600;min-height:42px;transition:all .15s ease; }
.stButton>button[kind="primary"] { background:linear-gradient(100deg,#0f9d91,#167da0);color:white;border:0;box-shadow:0 7px 16px #0f9d9126; }
.stButton>button[kind="primary"]:hover { background:linear-gradient(100deg,#0b887e,#126b8a);color:white;border:0; }
.result-card { background:white;border:1px solid #e0e8ef;border-radius:20px;padding:23px;box-shadow:0 10px 28px #1b34450b;margin-top:1rem; }
.result-label { font-size:.75rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#7b8797; }
.result-decision { font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;margin:.35rem 0 .2rem; }
.risk-number { font-family:'Space Grotesk',sans-serif;font-size:2.7rem;line-height:1.1;font-weight:700;letter-spacing:-1px; }
.risk-track { width:100%;height:9px;border-radius:99px;background:#e8eef3;overflow:hidden;margin:12px 0 7px; }
.risk-fill { height:100%;border-radius:99px; }
.small-muted { color:#718096;font-size:.82rem; }
.cue { display:inline-block;padding:6px 10px;margin:4px 5px 2px 0;border-radius:9px;background:#fff4df;border:1px solid #f7e4bd;color:#825315;font-size:.82rem;font-weight:600; }
.term-row { display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #edf1f5;font-size:.88rem; }
.term-row:last-child { border-bottom:0; }
.footer-note { margin-top:22px;padding:15px 17px;border-radius:13px;background:#edf5f8;border:1px solid #dceaf0;color:#526577;font-size:.82rem;line-height:1.55; }
.feature-card { background:#ffffffc9;border:1px solid #e1eaf0;border-radius:16px;padding:16px;height:100%; }
.feature-icon { font-size:1.35rem;margin-bottom:8px; }
.feature-title { font-weight:700;color:#23384f;margin-bottom:4px; }
.feature-copy { color:#718096;font-size:.82rem;line-height:1.5; }
hr { border-color:#e4ebf1!important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="brand">
  <div class="brand-icon">🛡️</div>
  <div><div class="brand-name">PhishShift</div><div class="brand-sub">MESSAGE RISK SCANNER · ML-07</div></div>
</div>
<div class="hero">
  <div class="eyebrow">Smart message screening</div>
  <h1>Spot suspicious messages<br>before they become a risk.</h1>
  <p>Paste an email or SMS to review warning signs, model-estimated risk, and the words that influenced the result. Links are not opened or visited.</p>
  <div class="pill-row"><span class="pill">✦ Machine learning</span><span class="pill">⌁ Explainable warning cues</span><span class="pill">🔒 Local message analysis</span></div>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.15, .85], gap="large")
with left:
    st.markdown('<div class="section-title">01 / Enter a message</div><div class="section-hint">Use a message you want to check. Avoid pasting real passwords or private information.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        samples = {
            "Suspicious account alert": "Your account is suspended. Verify your password immediately.",
            "Legitimate meeting note": "Hi team, our project meeting is scheduled for tomorrow at 10 AM. Please bring your progress report.",
            "Prize / reward message": "Congratulations, you won a prize. Confirm your identity immediately to claim your reward.",
        }
        if "message_text" not in st.session_state:
            st.session_state.message_text = ""
        def load_sample(label):
            st.session_state.message_text = samples[label]
        def clear_message():
            st.session_state.message_text = ""
            st.session_state.pop("scan_result", None)
        sample_cols = st.columns(3)
        for sample_col, label in zip(sample_cols, samples):
            with sample_col:
                st.button(label, key=f"sample_{label}", use_container_width=True,
                          on_click=load_sample, args=(label,))
        message = st.text_area(
            "Message text", key="message_text", height=190,
            placeholder="Paste your email or SMS message here…",
            help="Maximum length: 5,000 characters.",
            label_visibility="collapsed",
        )
        c1, c2 = st.columns([1.2, 1])
        with c1:
            scan_clicked = st.button("🛡️  Scan message", type="primary", use_container_width=True)
        with c2:
            st.button("Clear text", use_container_width=True, on_click=clear_message)
        if scan_clicked:
            try:
                st.session_state.scan_result = scan(message)
            except ValueError as exc:
                st.error(str(exc))
            except FileNotFoundError:
                st.error("Model files are missing. Run `python run_all.py` from the project folder first.")
            except Exception as exc:
                st.error(f"Could not scan this message: {exc}")

with right:
    st.markdown('<div class="section-title">02 / How it helps</div><div class="section-hint">A quick review, not a final security verdict.</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Risk estimate</div><div class="feature-copy">See the model’s estimated phishing probability and review category.</div></div><br>
    <div class="feature-card"><div class="feature-icon">🔎</div><div class="feature-title">Warning signals</div><div class="feature-copy">Find language related to urgency, password requests, threats, rewards, or links.</div></div><br>
    <div class="feature-card"><div class="feature-icon">🧠</div><div class="feature-title">Model explanation</div><div class="feature-copy">Review text cues and influential terms that may have affected the prediction.</div></div>
    ''', unsafe_allow_html=True)

result = st.session_state.get("scan_result")
if result:
    decision = result.get("decision", "ABSTAIN_REVIEW")
    risk = max(0, min(1, float(result.get("risk_probability", 0))))
    styles = {
        "SUSPICIOUS": ("#b42318", "#fff0ee", "High caution"),
        "ABSTAIN_REVIEW": ("#a15c07", "#fff6e5", "Review recommended"),
        "LIKELY_SAFE": ("#087f5b", "#e8f8f1", "Lower estimated risk"),
    }
    color, tint, subtitle = styles.get(decision, styles["ABSTAIN_REVIEW"])
    st.markdown('<div class="section-title">03 / Scan result</div><div class="section-hint">Use this result as a guide and verify unexpected requests through a trusted channel.</div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="result-card">
      <div class="result-label">Model assessment</div>
      <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;margin-top:8px">
        <div><div class="result-decision" style="color:{color}">{decision.replace('_',' ')}</div><div class="small-muted">{subtitle}</div></div>
        <div style="background:{tint};color:{color};padding:10px 14px;border-radius:13px;text-align:center"><div class="risk-number">{risk:.0%}</div><div style="font-size:.72rem;font-weight:700;letter-spacing:.7px">ESTIMATED RISK</div></div>
      </div>
      <div class="risk-track"><div class="risk-fill" style="width:{risk*100:.1f}%;background:{color}"></div></div>
      <div class="small-muted">Model: {result.get('model','unknown')} · Version: {result.get('version','unknown')}</div>
    </div>
    ''', unsafe_allow_html=True)

    explanation = result.get("explanation", {})
    cues = explanation.get("rule_cues", {})
    terms = explanation.get("model_terms", [])
    cue_labels = {
        "urgency": "Urgency", "credential_request": "Credential request",
        "money_or_reward": "Money or reward", "link_present": "Link present",
        "url_shortener": "URL shortener", "secrecy_or_pressure": "Secrecy / pressure",
        "threat_of_loss": "Threat of loss",
    }
    cue_col, term_col = st.columns(2, gap="large")
    with cue_col:
        with st.container(border=True):
            st.markdown("**🔎 Warning cues found**")
            if cues:
                for key, words in cues.items():
                    st.markdown(f"**{cue_labels.get(key, key.replace('_',' ').title())}**")
                    st.markdown("".join(f'<span class="cue">{word}</span>' for word in words), unsafe_allow_html=True)
            else:
                st.info("No predefined warning cues were detected. This does not guarantee the message is safe.")
    with term_col:
        with st.container(border=True):
            st.markdown("**🧠 Influential text terms**")
            if terms:
                for item in terms:
                    term = str(item.get("term", ""))
                    weight = float(item.get("weight", 0))
                    direction = "toward phishing" if weight > 0 else "away from phishing"
                    st.markdown(f'<div class="term-row"><span><b>{term}</b><br><span class="small-muted">{direction}</span></span><span style="font-weight:700;color:{"#b42318" if weight > 0 else "#087f5b"}">{weight:+.3f}</span></div>', unsafe_allow_html=True)
            else:
                st.write("No model-term explanation is available for this result.")

st.markdown(f'<div class="footer-note"><b>Safety note:</b> {DISCLAIMER} The risk percentage is a model estimate, not a calibrated guarantee. If a message asks for credentials, money, or urgent action, verify it independently using a trusted contact or official website.</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#91a0ae;font-size:.76rem;margin-top:20px">PhishShift · Educational machine-learning project</div>', unsafe_allow_html=True)
