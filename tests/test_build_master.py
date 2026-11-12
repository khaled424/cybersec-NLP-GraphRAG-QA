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


def test_load_summaries_parses_blocks(tmp_path: Path) -> None:
    path = tmp_path / "summaries.md"
    path.write_text("# Header ignored\n\n<!-- résumé 0123456789ab · NB1 -->\n# Short\ntext\n\n"
                    "<!-- résumé ba9876543210 · NB2 -->\nother\n", encoding="utf-8")
    assert builder.load_summaries(path) == {"0123456789ab": "# Short\ntext", "ba9876543210": "other"}
    assert builder.load_summaries(tmp_path / "missing.md") == {}


def test_summary_replaces_only_its_exact_source_cell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import nbformat

    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_markdown_cell("# Long title\nlong explanation"),
                      nbformat.v4.new_markdown_cell("# Kept\nunchanged"),
                      nbformat.v4.new_code_cell("x = 1")]
    nbformat.write(notebook, tmp_path / "NB.ipynb")
    monkeypatch.setattr(builder, "NOTEBOOKS", tmp_path)
    part = builder.Part("NB", "Titre", "Responsable", "3 — Modeling")
    summaries = {builder.fingerprint(notebook.cells[0].source): "# Title\nshort", "deadbeef0000": "stale"}

    cells = builder.part_cells(1, part, summaries)
    sources = [c.source for c in cells]
    assert "## Title\nshort" in sources and "## Kept\nunchanged" in sources and "x = 1" in sources
    monkeypatch.setattr(builder, "PARTS", (part,))
    assert builder.stale_summaries(summaries) == {"deadbeef0000"}


def test_refresh_markdown_keeps_code_and_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import nbformat

    source = nbformat.v4.new_notebook()
    source.cells = [nbformat.v4.new_markdown_cell("# Long\ntext"), nbformat.v4.new_code_cell("print(1)")]
    nbformat.write(source, tmp_path / "NB.ipynb")
    monkeypatch.setattr(builder, "NOTEBOOKS", tmp_path)
    monkeypatch.setattr(builder, "PARTS", (builder.Part("NB", "Titre", "Responsable", "3"),))
    monkeypatch.setattr(builder, "SUMMARIES", tmp_path / "none.md")

    executed = builder.build()
    for cell in executed.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [nbformat.v4.new_output("stream", text="1\n")], 7
    master = tmp_path / "master.ipynb"
    nbformat.write(executed, master)

    summary = f"<!-- résumé {builder.fingerprint(source.cells[0].source)} · NB -->\n# Short\n"
    (tmp_path / "summaries.md").write_text(summary, encoding="utf-8")
    monkeypatch.setattr(builder, "SUMMARIES", tmp_path / "summaries.md")
    assert builder.refresh_markdown(master) == 1

    refreshed = nbformat.read(master, as_version=4)
    assert "## Short" in [c.source for c in refreshed.cells]
    code = next(c for c in refreshed.cells if c.source == "print(1)")
    assert code.execution_count == 7 and code.outputs[0].text == "1\n"

