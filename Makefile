.PHONY: install data pipeline notebooks api ui mvp test lint

PYTHON ?= python
NOTEBOOKS = Notebook1_Preprocessing_NER_Graph Notebook2_PartA_GNN_PyG Notebook2_PartB_GTN_Leiden \
            Notebook3_LLM_FineTuning_Evaluation Notebook4_PartA_HybridRAG_Pipeline \
            Notebook4_PartB_AgenticRAG_Security_SIEM 00_Master_Notebook

install:            ## dependencies + package (editable) + spaCy model
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e . --no-deps
	$(PYTHON) -m spacy download en_core_web_sm

data:               ## download the pinned raw dataset (checksum verified)
	$(PYTHON) -m cybersec_nlp.data.download

pipeline:           ## clean -> NER -> STIX graph -> Neo4j scripts -> FAISS index -> classifier
	$(PYTHON) -m cybersec_nlp.pipelines.build_knowledge_base

notebooks:          ## execute every notebook in dependency order (GPU recommended, ~1 h 30)
	for nb in $(NOTEBOOKS); do \
		$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace \
			--ExecutePreprocessor.timeout=7200 notebooks/$$nb.ipynb || exit 1; \
	done

api:                ## FastAPI backend on http://localhost:8000 (docs: /docs)
	$(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

ui:                 ## Streamlit interface on http://localhost:8501
	$(PYTHON) -m streamlit run frontend/app.py --server.port 8501

mvp:                ## API + interface together (Ctrl+C stops both)
	$(PYTHON) -m uvicorn backend.main:app --port 8000 & \
	$(PYTHON) -m streamlit run frontend/app.py --server.port 8501; kill %1

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check . --exclude notebooks
