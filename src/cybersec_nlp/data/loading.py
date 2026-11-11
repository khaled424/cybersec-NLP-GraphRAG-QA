"""Load and clean the Cybersecurity-Dataset-v1 corpus (one implementation for every notebook).

Cleaning steps (Notebook 1, section 4):

1. drop the ``system`` column and rows without ``user`` / ``assistant``;
2. de-duplicate on ``user`` keeping the longest answer;
3. normalise text (HTML entities, literal ``\\n``, ``<think>`` blocks, whitespace);
4. remove too-short questions/answers and truncated answers.

Each kept row receives a stable ``doc_id`` derived from its row index in the pinned raw file.
"""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cybersec_nlp import config

USER_MIN_WORDS = 3
ASSISTANT_MIN_WORDS = 10
VALID_ENDINGS = (".", "!", "?", ":", ";", ")", '"', "'", "`", "*")
_THINK_CLOSED = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.DOTALL | re.IGNORECASE)
_THINK_OPEN = re.compile(r"<think\b[^>]*>.*$", re.DOTALL | re.IGNORECASE)
_THINK_ORPHAN = re.compile(r"</think\s*>", re.IGNORECASE)
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class CleaningStep:
    name: str
    rows: int


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_raw(path: Path = config.RAW_PARQUET, verify: bool = True) -> pd.DataFrame:
    """Read the pinned raw parquet, downloading it from Hugging Face if it is missing."""
    if not path.exists():
        from huggingface_hub import hf_hub_download

        path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = hf_hub_download(
            repo_id=config.DATASET_ID,
            filename=config.DATASET_FILE,
            revision=config.DATASET_REVISION,
            repo_type="dataset",
            local_dir=path.parent,
        )
        path = Path(downloaded)
    if verify and path.resolve() == config.RAW_PARQUET.resolve():
        actual = sha256_of(path)
        if actual != config.DATASET_SHA256:
            raise ValueError(f"Raw dataset checksum mismatch: {actual} != {config.DATASET_SHA256}")
    return pd.read_parquet(path)


def normalize_text(text: object) -> str:
    """Decode HTML entities and literal newlines, drop ``<think>`` blocks, collapse spaces."""
    if not isinstance(text, str):
        return ""
    text = html.unescape(text).replace('\\"', '"').replace("\\n", "\n")
    text = _THINK_CLOSED.sub(" ", text)
    text = _THINK_OPEN.sub(" ", text)
    text = _THINK_ORPHAN.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def is_truncated(text: str) -> bool:
    """True when the text is empty or does not end with a closing punctuation mark."""
    text = str(text).strip()
    return not text or not text.endswith(VALID_ENDINGS)


def clean_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[CleaningStep]]:
    """Return the cleaned corpus (columns ``doc_id, raw_index, user, assistant``) and step counts."""
    steps = [CleaningStep("Dataset brut", len(raw))]
    df = raw.drop(columns=["system"], errors="ignore").copy()
    df["raw_index"] = range(len(df))
    df = df.dropna(subset=["user", "assistant"])
    steps.append(CleaningStep("Après suppression des NaN (user / assistant)", len(df)))

    df = (
        df.assign(_len=df["assistant"].astype(str).str.len())
        .sort_values(["user", "_len"], ascending=[True, False])
        .drop_duplicates(subset="user", keep="first")
        .drop(columns="_len")
    )
    steps.append(CleaningStep("Après suppression des doublons 'user'", len(df)))

    for column in ("user", "assistant"):
        df[column] = df[column].map(normalize_text)
    invalid = (
        (df["user"].str.split().str.len() < USER_MIN_WORDS)
        | (df["assistant"].str.split().str.len() < ASSISTANT_MIN_WORDS)
        | df["assistant"].map(is_truncated)
    )
    df = df[~invalid].sort_values("raw_index").reset_index(drop=True)
    steps.append(CleaningStep("Après filtrage courts / tronqués", len(df)))

    df.insert(0, "doc_id", df["raw_index"].map(lambda i: f"HF-{i:05d}"))
    return df[["doc_id", "raw_index", "user", "assistant"]], steps


def load_clean_corpus(use_cache: bool = True) -> pd.DataFrame:
    """Cleaned corpus, read from ``data/processed`` when available."""
    if use_cache and config.CORPUS_CLEAN.exists():
        return pd.read_parquet(config.CORPUS_CLEAN)
    corpus, _ = clean_dataset(load_raw())
    return corpus
