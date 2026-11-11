"""Download the pinned raw dataset file into ``data/raw/cybersec_v1`` and verify its checksum."""

from cybersec_nlp import config
from cybersec_nlp.data.loading import load_raw


def main() -> None:
    frame = load_raw()
    print(f"{config.DATASET_ID}@{config.DATASET_REVISION[:8]}: {frame.shape} -> {config.RAW_PARQUET}")


if __name__ == "__main__":
    main()
