# ADR 0001: Initial project architecture

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

The project combines machine-learning workflows, Graph-RAG components, an
inference API, and a user interface. These concerns should remain independently
organized while sharing a single repository and Python environment.

## Decision

Use a monorepo-style layout with `ml/` for ML and retrieval components,
`backend/` for the API, `frontend/` for the user interface, and `infra/` for
deployment assets. Keep configuration, tests, and technical documentation in
dedicated top-level directories.

## Consequences

- Components can be developed and tested in one repository.
- Data and trained model artifacts remain local and are excluded from Git.
- TODO: Record future decisions when concrete technology choices are made.
