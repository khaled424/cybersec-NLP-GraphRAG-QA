"""Print a compact summary of the raw and cleaned corpus (``python -m cybersec_nlp.data.explore``)."""

from cybersec_nlp.data.loading import clean_dataset, load_raw


def main() -> None:
    raw = load_raw()
    print(f"Raw rows: {len(raw)} | columns: {raw.columns.tolist()}")
    print("Missing values:", raw.isna().sum().to_dict())
    corpus, steps = clean_dataset(raw)
    for step in steps:
        print(f"  {step.name:<45} {step.rows}")
    print("No class column: categories are produced by weak labelling (Notebook 2A).")
    print("\nFirst question:", corpus.loc[0, "user"][:200])


if __name__ == "__main__":
    main()
