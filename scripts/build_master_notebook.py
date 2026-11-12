"""Assemble ``notebooks/00_Master_Notebook.ipynb``, the final deliverable, from the team notebooks.

Every team notebook stays the **single source of truth**: this script copies all of its
cells, in TDSP order, under one "Partie" heading per notebook (its own headings are demoted
by one level so the master has a single coherent outline). Between two parts an isolation
cell resets the kernel namespace and releases GPU memory, so the master runs top to bottom
in one kernel exactly as the notebooks run separately (no name collisions, no memory
build-up across the GPU-heavy parts).

The master is read by the teaching staff, so its explanations are condensed:
``scripts/master_summaries.md`` holds a short version of the team notebooks' markdown cells,
each keyed by a fingerprint of the source cell it replaces. A summary applies only while its
source cell is unchanged; when a teammate edits a cell, the full text is used again and the
build reports the summary as stale. Code cells are always copied verbatim.

    python scripts/build_master_notebook.py                  # rebuild after any notebook change
    python scripts/build_master_notebook.py --markdown-only  # update the text of the executed master
    mise run master                                          # rebuild + execute (GPU, ~1 h 30)
"""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
MASTER = NOTEBOOKS / "00_Master_Notebook.ipynb"
SUMMARIES = Path(__file__).with_name("master_summaries.md")


@dataclass(frozen=True)
class Part:
    notebook: str
    title: str
    owner: str
    tdsp: str


PARTS: tuple[Part, ...] = (
    Part("001-EDA", "Profilage initial du jeu de données", "Équipe", "2 — Data Understanding"),
    Part("Notebook1_Preprocessing_NER_Graph", "Preprocessing NLP, NER cyber & base Neo4j", "Walid Fehry",
         "2 — Data Acquisition & Understanding"),
    Part("Notebook2_PartA_GNN_PyG", "GNN & PyTorch Geometric (GCN / GAT)", "Emna Trabelsi", "3 — Modeling"),
    Part("Notebook2_PartB_GTN_Leiden", "Graph Transformers (HGT) & clustering Hierarchical Leiden", "Hejer Mnejja",
         "3 — Modeling (Threat Mapping)"),
    Part("Notebook3_LLM_FineTuning_Evaluation", "LLMs, prompt engineering, LoRA & évaluation", "Khaled Gannoun",
         "3 — Model Tuning"),
    Part("Notebook4_PartA_HybridRAG_Pipeline", "Chunking, base vectorielle & pipeline HybridRAG", "Ines Trabelsi",
         "4 — Operationalization"),
    Part("Notebook4_PartB_AgenticRAG_Security_SIEM", "Agentic RAG (ReAct), sécurité OWASP & export SIEM", "Adrian Salvador Ekomo Mesi Obono",
         "5 — Security Audit"),
    Part("Synthese_TDSP", "Synthèse TDSP, démonstration de Vigie & acceptation", "Équipe",
         "4–5 — Deployment & Acceptance"),
)

SESSION_SETUP = """# Configuration de session, avant tout usage du GPU : entraînements reproductibles (cf. cybersec_nlp.reproducibility)
import os

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")"""

ISOLATION = """# Isolation : la partie suivante repart d'un état vierge, exactement comme son notebook d'origine
%reset -f
import gc

import torch

torch.use_deterministic_algorithms(False)
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()"""

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^#{1,5}\s")


def demote_headings(markdown: str, levels: int = 1) -> str:
    """Add ``levels`` '#' to every Markdown heading outside fenced code blocks."""
    lines, in_code = [], False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            in_code = not in_code
        elif not in_code and _HEADING.match(line):
            line = "#" * levels + line
        lines.append(line)
    return "\n".join(lines)


def intro_cells() -> list:
    rows = "\n".join(f"| {i} | {p.title} | {p.owner} | {p.tdsp} | `{p.notebook}.ipynb` |" for i, p in enumerate(PARTS))
    return [nbformat.v4.new_markdown_cell(f"""# 🛡️ Notebook maître — Cybersécurité & TAL : Graph-RAG pour le SOC

**Livrable final** · méthodologie **TDSP** · MVP **Vigie**, l'assistant du Centre d'Opérations de Sécurité (SOC).

Ce notebook réunit **tout le travail de l'équipe** : chaque partie reprend l'intégralité d'un notebook (code, résultats,
interprétations) dans l'ordre du cycle TDSP ; la partie 7 consolide les résultats et vérifie les critères d'acceptation.

| Partie | Contenu | Responsable | Étape TDSP | Notebook source |
| --- | --- | --- | --- | --- |
{rows}

- **Lecture** : chaque section annonce son objectif, le code suit, puis un encadré **Interprétation** donne les chiffres
  clés et leur sens.
- **Isolation** : chaque partie commence par une cellule qui remet le noyau à zéro et libère le GPU ; elle s'exécute
  donc exactement comme son notebook d'origine.
- **Dépendances** : les parties 1 → 7 lisent les livrables de la partie 1 (corpus, entités, graphe STIX) dans
  `data/processed/`.
- **Exécution** : `mise run master` reconstruit puis exécute ce notebook (GPU CUDA recommandé) ; le code partagé et
  testé est dans `src/cybersec_nlp/`.""")]


def fingerprint(markdown: str) -> str:
    """Short identifier of a source markdown cell: a summary only applies to that exact text."""
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()[:12]


_SUMMARY_MARK = re.compile(r"^<!-- résumé (?P<key>[0-9a-f]{12}) · \S+ -->$", re.MULTILINE)


def load_summaries(path: Path | None = None) -> dict[str, str]:
    """``{fingerprint: condensed markdown}`` read from ``master_summaries.md`` (empty if the file is absent)."""
    path = SUMMARIES if path is None else path
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    marks = list(_SUMMARY_MARK.finditer(text))
    ends = [mark.start() for mark in marks[1:]] + [len(text)]
    return {mark["key"]: text[mark.end():end].strip() for mark, end in zip(marks, ends, strict=True)}


def source_cells(part: Part) -> list:
    return nbformat.read(NOTEBOOKS / f"{part.notebook}.ipynb", as_version=4).cells


def part_cells(index: int, part: Part, summaries: dict[str, str]) -> list:
    cells = [nbformat.v4.new_markdown_cell(
        f"---\n# Partie {index} — {part.title}\n\n**Responsable :** {part.owner} · **Étape TDSP :** {part.tdsp} · "
        f"**Notebook source :** `notebooks/{part.notebook}.ipynb`")]
    if index > 0:
        cells.append(nbformat.v4.new_code_cell(ISOLATION))
    for cell in source_cells(part):
        if cell.cell_type == "markdown":
            text = summaries.get(fingerprint(cell.source), cell.source)
            cells.append(nbformat.v4.new_markdown_cell(demote_headings(text)))
        elif cell.cell_type == "code":
            cells.append(nbformat.v4.new_code_cell(cell.source))
    return cells


def build(summaries: dict[str, str] | None = None) -> nbformat.NotebookNode:
    summaries = load_summaries() if summaries is None else summaries
    master = nbformat.v4.new_notebook()
    master.cells = (intro_cells() + [nbformat.v4.new_code_cell(SESSION_SETUP)]
                    + [cell for i, part in enumerate(PARTS) for cell in part_cells(i, part, summaries)])
    master.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}}
    nbformat.validate(master)
    return master


def stale_summaries(summaries: dict[str, str]) -> set[str]:
    """Summaries whose source cell no longer exists (edited or removed by its author)."""
    current = {fingerprint(cell.source) for part in PARTS for cell in source_cells(part) if cell.cell_type == "markdown"}
    return set(summaries) - current


def refresh_markdown(path: Path = MASTER) -> int:
    """Rewrite only the markdown of the executed master; code cells and their outputs are left untouched.

    Refuses when the code differs from the team notebooks: a full rebuild and execution is then required.
    """
    current, fresh = nbformat.read(path, as_version=4), build()
    same_code = [c.cell_type for c in current.cells] == [c.cell_type for c in fresh.cells] and all(
        old.source == new.source for old, new in zip(current.cells, fresh.cells, strict=True) if old.cell_type == "code")
    if not same_code:
        raise SystemExit("Le code des notebooks a changé : reconstruire et exécuter le maître (mise run master).")
    changed = 0
    for old, new in zip(current.cells, fresh.cells, strict=True):
        if old.cell_type == "markdown" and old.source != new.source:
            old.source, changed = new.source, changed + 1
    nbformat.write(current, path)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--markdown-only", action="store_true",
                        help="met à jour le texte du maître exécuté sans toucher au code ni aux sorties")
    args = parser.parse_args()
    summaries = load_summaries()
    if args.markdown_only:
        print(f"{MASTER.relative_to(ROOT)} : {refresh_markdown()} cellules de texte mises à jour (code et sorties inchangés)")
    else:
        master = build(summaries)
        nbformat.write(master, MASTER)
        code = sum(c.cell_type == "code" for c in master.cells)
        print(f"{MASTER.relative_to(ROOT)} : {len(PARTS)} parties, {len(master.cells)} cellules ({code} de code)")
    if stale := stale_summaries(summaries):
        print(f"⚠ {len(stale)} résumé(s) obsolète(s) dans {SUMMARIES.name} (cellule source modifiée) : "
              f"le texte complet est utilisé à la place → {', '.join(sorted(stale))}")


if __name__ == "__main__":
    main()
