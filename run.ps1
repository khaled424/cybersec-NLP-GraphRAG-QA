param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("install", "data", "pipeline", "notebooks", "api", "ui", "test", "lint")]
    [string]$Command
)

$ErrorActionPreference = "Stop"
$Notebooks = @(
    "Notebook1_Preprocessing_NER_Graph", "Notebook2_PartA_GNN_PyG", "Notebook2_PartB_GTN_Leiden",
    "Notebook3_LLM_FineTuning_Evaluation", "Notebook4_PartA_HybridRAG_Pipeline",
    "Notebook4_PartB_AgenticRAG_Security_SIEM", "00_Master_Notebook"
)

switch ($Command) {
    "install" {
        & python -m pip install -r requirements.txt
        & python -m pip install -e . --no-deps
        & python -m spacy download en_core_web_sm
    }
    "data" { & python -m cybersec_nlp.data.download }
    "pipeline" { & python -m cybersec_nlp.pipelines.build_knowledge_base }
    "notebooks" {
        foreach ($nb in $Notebooks) {
            & python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=7200 "notebooks/$nb.ipynb"
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
    }
    "api" { & python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 }
    "ui" { & python -m streamlit run frontend/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false }
    "test" { & python -m pytest }
    "lint" { & python -m ruff check . --exclude notebooks }
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
