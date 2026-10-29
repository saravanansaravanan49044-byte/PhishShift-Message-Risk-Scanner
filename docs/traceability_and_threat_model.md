# Use case (T1)
- **Decision user:** helpdesk / security-awareness trainer triaging simulated messages.
- **Input:** channel, subject, body text (defanged), sanitized URL features, sender domain type.
- **Output:** risk probability, decision `SUSPICIOUS | ABSTAIN_REVIEW | LIKELY_SAFE`, textual cues.
- **Exclusions:** live mailboxes, real credentials, attachments, link resolution, production blocking.

# Requirement traceability
| Req | Implementation | Test / Evidence |
|---|---|---|
| FR-01 | `preprocess.dedup` (3-gram Jaccard ≥ 0.85, names/URLs/amounts masked) | `results/dedup_proof.csv`, `test_cp2_*` |
| FR-02 | `models.MODELS` (rules, tfidf_lr, char_svm) | `results/results_table.csv` |
| FR-03 | `train_eval.HOLDOUT_CAMPAIGNS` | `test_fr03_campaigns_disjoint`, experiment log |
| FR-04 | `models.decide` (0.35–0.65 abstain), `models.explain` | `test_fr04_abstain_band`, `error_examples.json` |
| FR-05 | `fpr_legit_urgent`, `mean_abs_prob_drift`, `perturbed_f1` | results table, `test_at03_*`, `test_cp5_*` |
| NFR-01 | `defang`, no network code anywhere | `test_cp1_all_urls_inert` |
| NFR-02 | synthetic-only corpus, fictional names | `data/source_manifest.csv` |
| NFR-03 | `DISCLAIMER` in CLI and UI | screenshots |
| AT-01/02/03, CP-5 | `tests/test_acceptance.py` | `results/acceptance_evidence.jsonl` |

# Threat model
| Threat | Mitigation | Residual risk |
|---|---|---|
| Accidental click/fetch of malicious URL | All URLs defanged; no HTTP client imported | User copies link manually |
| Real PII in corpus | Synthetic authoring only; review on import | Mentor-supplied data must be checked |
| Adversarial rewording (new tactics) | Campaign holdout, char n-grams, abstain band | Soft-ask/CEO fraud still often abstains |
| Obfuscation (leetspeak, defang variants) | Char n-grams; perturbation tests | Probability drift measured, not eliminated |
| Over-trust in "LIKELY_SAFE" | Disclaimer; abstain band | Human judgement still required |
| Label leakage via sender_domain_type | Documented in EDA; ablate in report | Synthetic data over-separates |
