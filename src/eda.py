"""EDA (T3): missingness, distributions, leakage checks + 3 labelled charts."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "messages_raw.csv"
CLEAN = ROOT / "data" / "processed" / "messages_clean.csv"
FIG = ROOT / "results" / "figures"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW, keep_default_na=False)
    df = pd.read_csv(CLEAN, keep_default_na=False)
    lines = ["# EDA summary", "", f"Raw rows: {len(raw)}  |  after cleaning+dedup: {len(df)}", "",
             "## Empty-string counts per column (raw)", (raw == "").sum().to_string(), "",
             "## Label balance (clean)", df.label.value_counts().to_string(), "",
             "## Channel x label", pd.crosstab(df.channel, df.label).to_string(), "",
             "## Sender domain type x label (LEAKAGE RISK: near-perfectly separates classes)",
             pd.crosstab(df.sender_domain_type, df.label).to_string(), "",
             "## Body length stats", df.body_text.str.len().describe().round(1).to_string(), "",
             "Leakage notes: sender_domain_type and url features are strongly label-correlated in synthetic data; "
             "campaign_group must never be a feature; dates are uniformly random so time ordering is not informative."]
    (ROOT / "results" / "eda_summary.md").write_text("\n".join(lines))

    df.label.map({0: "legitimate", 1: "phishing"}).value_counts().plot.bar(color=["#4a7", "#c44"])
    plt.title("Fig 1. Class balance after dedup"); plt.ylabel("messages"); plt.tight_layout()
    plt.savefig(FIG / "fig1_class_balance.png"); plt.close()

    df.campaign_group.value_counts().sort_index().plot.barh()
    plt.title("Fig 2. Messages per campaign group"); plt.xlabel("messages"); plt.tight_layout()
    plt.savefig(FIG / "fig2_campaigns.png"); plt.close()

    for lab, name in [(0, "legitimate"), (1, "phishing")]:
        df[df.label == lab].body_text.str.len().plot.hist(alpha=.6, bins=20, label=name)
    plt.title("Fig 3. Body length distribution"); plt.xlabel("characters"); plt.legend(); plt.tight_layout()
    plt.savefig(FIG / "fig3_length.png"); plt.close()
    print("EDA written to results/")


if __name__ == "__main__":
    main()
