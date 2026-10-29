# ML-07 PhishShift Message Risk Scanner — Final Report
Team/Student IDs: ________  Mentor: ________  Date: ________

## 1. Abstract (150–200 words)
Phishing detectors trained on obvious keyword-heavy lures often fail on new tactics and over-flag legitimate
urgent notices. We built PhishShift, an educational triage tool for simulated emails and SMS. A 432-message,
locally authored corpus across ten campaign groups was sanitized (all URLs defanged) and near-duplicate templates
were removed before splitting (432 → 93 unique). We compared a keyword-rule baseline, a TF-IDF logistic regression
and a word+character TF-IDF calibrated linear SVM. A random split gave every model F1 = 1.0, but a campaign-separated
holdout containing unseen CEO-soft-ask and shared-document lures plus legitimate urgent notices exposed real
differences: F1 0.62 / 0.82 / 0.94 with false-positive rates on legitimate urgent messages of 0.63 / 0.13 / 0.38.
An abstain band (0.35–0.65) routes uncertain messages to human review, and every decision lists the textual cues
that drove it. Perturbation tests (defang variants, punctuation, leetspeak) produced small probability drift.
The tool is decision support only and is not a guarantee of safety. *(edit with your own numbers)*

## 2. Problem & objectives — see docs/traceability_and_threat_model.md (use case, FR/NFR)
## 3. Literature & sources (min 3)
1. Fette, Sadeh, Tomasic (2007). *Learning to detect phishing emails.* WWW.
2. Chandrasekaran, Narayanan, Upadhyaya (2006). *Phishing email detection based on structural properties.*
3. Geifman & El-Yaniv (2017). *Selective classification for deep neural networks* (abstain/reject option).
4. Lee et al. (2022). *Deduplicating training data makes language models better.* ACL.
Dataset licence: team-authored synthetic, CC0 — see data/source_manifest.csv.
## 4. Data & EDA — paste results/eda_summary.md, sanitization_log.json, figures/fig1-3
## 5. Design & methods — pipeline: generate → defang/clean → dedup → campaign split → 3 models → abstain/explain → CLI/UI
## 6. Results — results_table.csv, per_campaign_breakdown.csv, 3 examples from error_examples.json, pytest log
## 7. Safety & limitations — synthetic data over-separates; sender_domain_type leakage; small unique set; soft-ask fraud
## 8. Conclusion & appendix — future: larger licensed corpus, sender-metadata ablation, threshold tuning per channel
