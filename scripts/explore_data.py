"""Print a compact exploratory summary of the locally saved dataset."""

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict, load_from_disk

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "cybersec_v1"
LABEL_COLUMNS = ("label", "labels", "class", "category", "classification")


def _splits(dataset: Dataset | DatasetDict) -> list[tuple[str, Dataset]]:
    if isinstance(dataset, DatasetDict):
        return list(dataset.items())
    return [("dataset", dataset)]


def _find_label_column(splits: list[tuple[str, Dataset]]) -> str | None:
    columns = {column for _, split in splits for column in split.column_names}
    return next((column for column in LABEL_COLUMNS if column in columns), None)


def _label_key(value: Any) -> str:
    if value is None:
        return "<missing>"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return repr(value)


def explore_data(dataset_path: Path = DATASET_PATH, label_column: str | None = None) -> None:
    """Load and summarize the dataset, including class counts when labels exist."""
    print(f"Loading dataset from: {dataset_path}")
    dataset = load_from_disk(str(dataset_path))
    splits = _splits(dataset)

    total_rows = sum(len(split) for _, split in splits)
    print(f"\nTotal rows: {total_rows}")
    if len(splits) > 1:
        print("Rows per split:")
        for split_name, split in splits:
            print(f"  {split_name}: {len(split)}")

    columns = list(splits[0][1].column_names) if splits else []
    print(f"\nColumns: {columns}")

    selected_label = label_column or _find_label_column(splits)
    if selected_label is None:
        print(
            "\nClass distribution: unavailable; no label/class column was found. "
            "This dataset contains instruction-response fields, not explicit class labels."
        )
    else:
        missing_splits = [
            split_name
            for split_name, split in splits
            if selected_label not in split.column_names
        ]
        if missing_splits:
            raise ValueError(
                f"Label column '{selected_label}' is missing from splits: "
                f"{', '.join(missing_splits)}"
            )
        counts: Counter[str] = Counter()
        for _, split in splits:
            counts.update(_label_key(value) for value in split[selected_label])
        print(f"\nClass distribution for '{selected_label}':")
        for label, count in sorted(counts.items()):
            print(f"  {label}: {count}")

    print("\nFirst 3 rows:")
    rows_remaining = 3
    for split_name, split in splits:
        for row in split.select(range(min(rows_remaining, len(split)))):
            print(f"  [{split_name}] {row}")
            rows_remaining -= 1
            if rows_remaining == 0:
                return
    if rows_remaining == 3:
        print("  Dataset is empty.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label-column",
        help="Override automatic class-column detection for labeled datasets.",
    )
    args = parser.parse_args()
    explore_data(label_column=args.label_column)


if __name__ == "__main__":
    main()
