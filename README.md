# ML-07 PhishShift Message Risk Scanner

Educational triage tool that scores **simulated** emails/SMS for phishing risk, explains the cues, and abstains when unsure.
**Decision support only – not a guarantee of safety.** No link is ever opened, resolved or fetched.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py          # generate data -> sanitize -> dedup -> EDA -> train & evaluate
pytest -q                  # acceptance tests; evidence -> results/acceptance_evidence.jsonl
python -m app.scan "Your VPN is locked, verify at bit[.]ly/abc"      # CLI
streamlit run app/streamlit_app.py                                    # optional web UI
```

## Layout
| Path | Purpose |
|---|---|
| `src/generate_data.py` | Locally authored synthetic corpus (432 raw rows, 10 campaign groups) |
| `src/preprocess.py` | Schema cleaning, URL defanging (CP-1), near-duplicate removal (FR-01, CP-2) |
| `src/eda.py` | Missingness, distributions, leakage notes, 3 figures |
| `src/models.py` | Rules baseline, TF-IDF+LogReg, word+char TF-IDF calibrated SVM (FR-02); abstain + explanations (FR-04) |
| `src/train_eval.py` | Campaign-separated holdout (FR-03), FPR on legit-urgent, perturbation drift (FR-05) |
| `app/` | CLI + Streamlit prototype (T6) |
| `tests/` | AT-01..03, CP-1, CP-2, CP-5, FR-03/04 tests |
| `data/` | `raw/` (unchanged), `processed/`, `source_manifest.csv` |
| `results/` | results table, dedup proof, sanitization log, error examples, figures, experiment log |
| `docs/` | traceability, threat model, provenance, report template, AI disclosure |

## Mentor variation (Section 08)
Edit `HOLDOUT_CAMPAIGNS` in `src/train_eval.py`, or add the mentor's campaign rows to `data/raw/messages_raw.csv`
with a new `campaign_group`, then re-run `python -m src.preprocess && python -m src.train_eval && pytest -q`.

## Key results (seed 42, campaign holdout C5, C6, L4)
See `results/results_table.csv`. Random split gives F1 = 1.0 for every model (misleading); the campaign holdout
drops this to 0.62 (rules) / 0.82 (TF-IDF LR) / 0.94 (char SVM), with legit-urgent FPR 0.63 / 0.13 / 0.38.
TF-IDF LR is the deployed model because it has the best F1-minus-FPR trade-off.
