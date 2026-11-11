"""End-to-end build: clean corpus -> NER -> STIX graph -> exports -> FAISS index -> classifier.

``python -m cybersec_nlp.pipelines.build_knowledge_base [--skip-index]``

Outputs (consumed by Notebooks 2A-4B, the master notebook and the MVP):

* ``data/processed/corpus_clean.parquet``  cleaned corpus with ``doc_id``
* ``data/processed/entities.json``          per-document entities (Jalon 1)
* ``data/processed/knowledge_graph.json``   graph exchange format
* ``data/processed/rag_documents.jsonl``    RAG contract (doc_id, text, source, title)
* ``data/processed/neo4j/{import,queries}.cypher``
* ``artifacts/vector_index/``               FAISS index + chunk table
* ``artifacts/incident_classifier.joblib``  triage classifier
* ``reports/metrics/pipeline_metrics.json`` build statistics and classifier metrics
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from time import perf_counter

from cybersec_nlp import config
from cybersec_nlp.data.loading import clean_dataset, load_raw
from cybersec_nlp.graph.knowledge_graph import (
    build_knowledge_graph,
    export_neo4j_scripts,
    extract_corpus_entities,
    graph_summary,
    save_graph,
)
from cybersec_nlp.nlp.classifier import train_and_evaluate
from cybersec_nlp.nlp.ner import CyberNER


def rag_documents(corpus) -> list[dict[str, str]]:
    return [
        {"doc_id": r.doc_id, "text": r.assistant, "title": r.user,
         "source": f"https://huggingface.co/datasets/{config.DATASET_ID} (train, ligne {r.raw_index})"}
        for r in corpus.itertuples(index=False)
    ]


def write_jsonl(rows: list[dict], path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def read_jsonl(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(build_index: bool = True) -> dict:
    timings: dict[str, float] = {}

    def step(name: str, start: float) -> None:
        timings[name] = round(perf_counter() - start, 2)
        print(f"[ok] {name} ({timings[name]} s)")

    t = perf_counter()
    corpus, steps = clean_dataset(load_raw())
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    corpus.to_parquet(config.CORPUS_CLEAN, index=False)
    step("cleaning", t)

    t = perf_counter()
    ner = CyberNER()
    entities = extract_corpus_entities(corpus, ner)
    config.ENTITIES_JSON.write_text(json.dumps(entities, ensure_ascii=False), encoding="utf-8")
    graph = build_knowledge_graph(corpus, ner)
    save_graph(graph, config.KNOWLEDGE_GRAPH_JSON)
    export_neo4j_scripts(graph, config.NEO4J_DIR)
    documents = rag_documents(corpus)
    write_jsonl(documents, config.RAG_DOCUMENTS)
    step("ner_graph_exports", t)

    if build_index:
        from cybersec_nlp.rag.vector_index import VectorIndex

        t = perf_counter()
        VectorIndex.build(documents).save(config.VECTOR_INDEX_DIR)
        step("vector_index", t)

    t = perf_counter()
    model, report = train_and_evaluate(corpus["user"].tolist(), (corpus["user"] + " " + corpus["assistant"]).tolist())
    model.save(config.CLASSIFIER_PATH)
    step("classifier", t)

    label_counts: dict[str, int] = {}
    for record in entities:
        for entity in record["entities"]:
            label_counts[entity["label"]] = label_counts.get(entity["label"], 0) + 1
    metrics = {
        "dataset": {"id": config.DATASET_ID, "revision": config.DATASET_REVISION,
                    "cleaning": [asdict(s) for s in steps]},
        "ner": {"entity_mentions": label_counts,
                "docs_with_entity": sum(bool(r["entities"]) for r in entities), "docs": len(entities)},
        "graph": graph_summary(graph),
        "classifier": asdict(report),
        "timings_s": timings,
    }
    config.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (config.METRICS_DIR / "pipeline_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-index", action="store_true", help="do not (re)build the FAISS index")
    args = parser.parse_args()
    metrics = run(build_index=not args.skip_index)
    print(json.dumps({k: metrics[k] for k in ("graph", "ner")}, indent=2))
    print(f"classifier macro-F1 = {metrics['classifier']['macro_f1']:.3f}")


if __name__ == "__main__":
    main()
