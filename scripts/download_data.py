"""Download the cybersecurity dataset from Hugging Face."""

from pathlib import Path

from datasets import load_dataset

DATASET_ID = "AlicanKiraz0/Cybersecurity-Dataset-v1"
SAVE_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "cybersec_v1"


def main() -> None:
    """Download and save the dataset in Hugging Face's on-disk format."""
    print(f"Starting download of '{DATASET_ID}' from Hugging Face...")
    dataset = load_dataset(DATASET_ID)
    print("Download complete. Saving dataset to disk...")
    dataset.save_to_disk(str(SAVE_PATH))
    print(f"Dataset saved successfully to: {SAVE_PATH}")


if __name__ == "__main__":
    main()
