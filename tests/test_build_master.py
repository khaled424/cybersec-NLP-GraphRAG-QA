"""Tests for the master-notebook builder (scripts/build_master_notebook.py)."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_master_notebook.py"
spec = importlib.util.spec_from_file_location("build_master_notebook", SCRIPT)
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder  # required by dataclasses when loading a module from a file path
spec.loader.exec_module(builder)


def test_demote_headings_skips_code_fences() -> None:
    text = "# Title\ntext\n```\n# comment in code\n```\n## Section"
    assert builder.demote_headings(text) == "## Title\ntext\n```\n# comment in code\n```\n### Section"


@pytest.mark.skipif(not all((builder.NOTEBOOKS / f"{p.notebook}.ipynb").exists() for p in builder.PARTS),
                    reason="team notebooks not available")
def test_master_contains_every_cell_of_every_part() -> None:
    import nbformat

    master = builder.build()
    sources = [c.source for c in master.cells]
    for index, part in enumerate(builder.PARTS):
        notebook = nbformat.read(builder.NOTEBOOKS / f"{part.notebook}.ipynb", as_version=4)
        assert any(s.startswith(f"---\n# Partie {index} — ") for s in sources)
        code = [c.source for c in notebook.cells if c.cell_type == "code"]
        assert all(s in sources for s in code), part.notebook
    assert sum(s.startswith("# Isolation") for s in sources) == len(builder.PARTS) - 1
    assert len({c.id for c in master.cells}) == len(master.cells)
