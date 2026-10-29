"""One-command reproducible pipeline: data -> clean/dedup -> EDA -> train/eval."""
from src import eda, generate_data, preprocess, train_eval

if __name__ == "__main__":
    generate_data.main()
    preprocess.main()
    eda.main()
    train_eval.main()
    print("\nDone. Now run: pytest -q   and   python -m app.scan \"<message>\"")
