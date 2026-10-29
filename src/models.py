"""Three models (FR-02), abstain logic and safe cue explanations (FR-04)."""
import re

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

CUES = {
    "urgency": r"\b(urgent|immediately|now|today|final warning|within 24 hours|expires?|asap|end of day)\b",
    "credential_request": r"\b(password|login|credentials|verify|confirm|identity)\b",
    "money_or_reward": r"\b(payment|invoice|bank|salary|gift card|store cards|prize|reward|won|reimburse)\b",
    "link_present": r"(hxxps?://|\[\.\])",
    "url_shortener": r"(bit\[\.\]ly|tinyurl|t\[\.\]co|is\[\.\]gd)",
    "secrecy_or_pressure": r"\b(quietly|between us|favour|favor|at your desk|back-to-back)\b",
    "threat_of_loss": r"\b(suspended|locked|on hold|delayed|stop|losing)\b",
}
CUE_WEIGHTS = {"urgency": 1, "credential_request": 1.5, "money_or_reward": 1, "link_present": 1,
               "url_shortener": 1.5, "secrecy_or_pressure": 1.5, "threat_of_loss": 1}


def find_cues(text: str) -> dict:
    t = text.lower()
    return {k: sorted(set(m.group(0) for m in re.finditer(p, t))) for k, p in CUES.items() if re.search(p, t)}


class RuleBaseline(BaseEstimator, ClassifierMixin):
    """Keyword-rule scorer mapped to a pseudo-probability."""
    classes_ = np.array([0, 1])

    def fit(self, X, y=None):
        return self

    def predict_proba(self, X):
        s = np.array([sum(CUE_WEIGHTS[c] for c in find_cues(x)) for x in X], dtype=float)
        p = 1 / (1 + np.exp(-(s - 2.5)))
        return np.c_[1 - p, p]

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def tfidf_lr():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
    ])


def char_svm():
    """Third model: word+char n-grams + calibrated linear SVM (more robust to spelling/punctuation shifts)."""
    feats = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    return Pipeline([("feats", feats),
                     ("clf", CalibratedClassifierCV(LinearSVC(C=0.5, class_weight="balanced"), cv=3))])


MODELS = {"rules": RuleBaseline, "tfidf_lr": tfidf_lr, "char_svm": char_svm}


def decide(p: float, low: float = 0.35, high: float = 0.65) -> str:
    """FR-04 reject/abstain band."""
    if p >= high:
        return "SUSPICIOUS"
    if p <= low:
        return "LIKELY_SAFE"
    return "ABSTAIN_REVIEW"


def explain(text: str, model=None, top_k: int = 5) -> dict:
    """Safe explanation: lists textual cues only. Never resolves or fetches URLs (NFR-01)."""
    out = {"rule_cues": find_cues(text)}
    try:
        lr = model.named_steps["clf"]; vec = model.named_steps["tfidf"]
        x = vec.transform([text]); idx = x.nonzero()[1]
        contrib = sorted(((vec.get_feature_names_out()[i], float(x[0, i] * lr.coef_[0][i])) for i in idx),
                         key=lambda t: -abs(t[1]))[:top_k]
        out["model_terms"] = [{"term": t, "weight": round(w, 3)} for t, w in contrib]
    except Exception:
        pass
    return out
