"""Project-wide paths and constants (single source of truth for notebooks, pipeline and MVP).

``CYBERSEC_ROOT`` overrides the repository root, which is useful when the package is
installed non-editable or run inside a container.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.getenv("CYBERSEC_ROOT", Path(__file__).resolve().parents[2]))

DATASET_ID = "AlicanKiraz0/Cybersecurity-Dataset-v1"
DATASET_REVISION = "410b35d53b8b1d49b9b781760a32147b2946698c"
DATASET_FILE = "cybersecurity-dataset-train-data.parquet"
DATASET_SHA256 = "6b1092bce6d219a50cd5ff3487a068cb368e2fd08a0f469c7c7314935d6473aa"

DATA_RAW = ROOT / "data" / "raw" / "cybersec_v1"
RAW_PARQUET = DATA_RAW / DATASET_FILE
DATA_PROCESSED = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"
METRICS_DIR = REPORTS / "metrics"

# Files exchanged between notebooks, pipeline and MVP (Jalon 1 contract).
CORPUS_CLEAN = DATA_PROCESSED / "corpus_clean.parquet"
ENTITIES_JSON = DATA_PROCESSED / "entities.json"
KNOWLEDGE_GRAPH_JSON = DATA_PROCESSED / "knowledge_graph.json"
RAG_DOCUMENTS = DATA_PROCESSED / "rag_documents.jsonl"
TOPICS_PARQUET = DATA_PROCESSED / "df_clean_eda.parquet"
NEO4J_DIR = DATA_PROCESSED / "neo4j"
VECTOR_INDEX_DIR = ARTIFACTS / "vector_index"
CLASSIFIER_PATH = ARTIFACTS / "incident_classifier.joblib"

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SEED = 42
