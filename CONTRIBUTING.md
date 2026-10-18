# Contributing

Thank you for contributing to **cybersec-NLP-GraphRAG-QA**. This project
combines NLP, cybersecurity, graph methods, and Graph-RAG; contributions
should be reproducible, reviewable, and safe to run on Windows.

## Development setup

Run commands from the repository root in PowerShell:

```powershell
python -m pip install -e ".[dev]"
```

Use `.\run.ps1` for the standard project commands:

```powershell
.\run.ps1 data
.\run.ps1 explore
.\run.ps1 test
.\run.ps1 lint
```

The dataset and trained model artifacts are local resources. Keep them out of
source control; the repository ignores `data/` and `models/`.

## Golden rules

1. **Keep `main` green.** The test suite must pass with `.\run.ps1 test` before
   changes are merged.
2. **Do not commit data or model artifacts.** Never add files from `data/` or
   `models/`; share reproducible download or generation instructions instead.
3. **Make metrics reproducible.** Document the dataset and split, preprocessing,
   model and configuration, random seeds, and evaluation command needed to
   reproduce every reported metric. Do not present unverified results as
   measured results.
4. **Use a focused branch.** Create branches with one of these prefixes:
   `feat/`, `fix/`, or `docs/` (for example, `feat/graph-retriever`).
5. **Use conventional commit messages.** Start commits with `feat:`, `fix:`,
   or `docs:` as appropriate (for example, `fix: handle empty EDA dataset`).
6. **Definition of Done.** Before pushing, both `.\run.ps1 lint` and
   `.\run.ps1 test` must pass.

## Pull request checklist

- [ ] The change has a focused branch and a conventional commit message.
- [ ] `.\run.ps1 lint` passes.
- [ ] `.\run.ps1 test` passes.
- [ ] New or changed NLP/graph behavior includes relevant tests.
- [ ] Any reported metric includes enough detail to reproduce it.
- [ ] No local datasets, credentials, or trained model files are included.
- [ ] Documentation and configuration are updated when behavior or commands
      change.
