"""Assemble ``notebooks/00_Master_Notebook.ipynb``, the final deliverable, from the team notebooks.

Every team notebook stays the **single source of truth**: this script copies all of its
cells, in TDSP order, under one "Partie" heading per notebook (its own headings are demoted
by one level so the master has a single coherent outline). Between two parts an isolation
cell resets the kernel namespace and releases GPU memory, so the master runs top to bottom
in one kernel exactly as the notebooks run separately (no name collisions, no memory
build-up across the GPU-heavy parts).

    python scripts/build_master_notebook.py      # rebuild after any notebook change
    mise run master                              # rebuild + execute (GPU, ~1 h 30)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
MASTER = NOTEBOOKS / "00_Master_Notebook.ipynb"


@dataclass(frozen=True)
class Part:
    notebook: str
    title: str
    owner: str
    tdsp: str


PARTS: tuple[Part, ...] = (
    Part("001-EDA", "Profilage initial du jeu de données", "Équipe", "2 — Data Understanding"),
    Part("Notebook1_Preprocessing_NER_Graph", "Preprocessing NLP, NER cyber & base Neo4j", "Walid",
         "2 — Data Acquisition & Understanding"),
    Part("Notebook2_PartA_GNN_PyG", "GNN & PyTorch Geometric (GCN / GAT)", "Membre 2", "3 — Modeling"),
    Part("Notebook2_PartB_GTN_Leiden", "Graph Transformers (HGT) & clustering Hierarchical Leiden", "Membre 3",
         "3 — Modeling (Threat Mapping)"),
    Part("Notebook3_LLM_FineTuning_Evaluation", "LLMs, prompt engineering, LoRA & évaluation", "Membre 4",
         "3 — Model Tuning"),
    Part("Notebook4_PartA_HybridRAG_Pipeline", "Chunking, base vectorielle & pipeline HybridRAG", "Membre 5",
         "4 — Operationalization"),
    Part("Notebook4_PartB_AgenticRAG_Security_SIEM", "Agentic RAG (ReAct), sécurité OWASP & export SIEM", "Membre 6",
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

**Livrable final du projet** · méthodologie **TDSP** · MVP : **Vigie**, l'assistant du Centre d'Opérations de Sécurité.

Ce notebook réunit **l'intégralité du travail de l'équipe** : chaque partie reprend toutes les cellules (explications,
code, résultats et interprétations) du notebook de son responsable, dans l'ordre du cycle TDSP, puis la synthèse
consolide les résultats et les confronte aux critères d'acceptation.

| Partie | Contenu | Responsable | Étape TDSP | Notebook source |
| --- | --- | --- | --- | --- |
{rows}

**Lecture.** Chaque partie commence par une cellule d'isolation qui remet le noyau à zéro et libère la mémoire GPU :
elle s'exécute donc exactement comme son notebook d'origine. Les parties 1 → 7 dépendent des livrables de la partie 1
(corpus nettoyé, entités, graphe STIX) écrits dans `data/processed/`.

**Exécution.** `mise run master` reconstruit ce notebook à partir des notebooks de l'équipe puis l'exécute de haut en
bas (GPU CUDA recommandé, ~1 h 30). Le code partagé et testé est dans `src/cybersec_nlp/`.""")]


def part_cells(index: int, part: Part) -> list:
    source = nbformat.read(NOTEBOOKS / f"{part.notebook}.ipynb", as_version=4)
    cells = [nbformat.v4.new_markdown_cell(
        f"---\n# Partie {index} — {part.title}\n\n**Responsable :** {part.owner} · **Étape TDSP :** {part.tdsp} · "
        f"**Notebook source :** `notebooks/{part.notebook}.ipynb`")]
    if index > 0:
        cells.append(nbformat.v4.new_code_cell(ISOLATION))
    for cell in source.cells:
        if cell.cell_type == "markdown":
            cells.append(nbformat.v4.new_markdown_cell(demote_headings(cell.source)))
        elif cell.cell_type == "code":
            cells.append(nbformat.v4.new_code_cell(cell.source))
    return cells


def build() -> nbformat.NotebookNode:
    master = nbformat.v4.new_notebook()
    master.cells = (intro_cells() + [nbformat.v4.new_code_cell(SESSION_SETUP)]
                    + [cell for i, part in enumerate(PARTS) for cell in part_cells(i, part)])
    master.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}}
    nbformat.validate(master)
    return master


def main() -> None:
    master = build()
    nbformat.write(master, MASTER)
    code = sum(c.cell_type == "code" for c in master.cells)
    print(f"{MASTER.relative_to(ROOT)} : {len(PARTS)} parties, {len(master.cells)} cellules ({code} de code)")


if __name__ == "__main__":
    main()
