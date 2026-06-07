# HealthHubQA - Supporting Materials

**Author:** Ayomide Ogun-Ajala  
**Student ID:** 21309903

This archive contains the source code and supporting files for **HealthHubQA**, a biomedical question answering system built for a Final Year Project. The system uses a Retrieval-Augmented Generation (RAG) workflow on PubMedQA-style data and compares model behavior with and without retrieval.

## Project Summary

HealthHubQA evaluates biomedical QA under multiple configurations:

- Retrieval module using sentence embeddings (`all-MiniLM-L6-v2` + cosine similarity)
- RAG pipeline integrating retrieved contexts with generative models
- Evaluation pipeline producing accuracy, macro-F1, confusion matrices, and prediction distributions
- Optional multi-model runs (local model, GPT API model, and local Ollama model)

  https://www.image2url.com/r2/default/images/1780866728541-e5649f1e-0f7e-4c65-a055-47bcfab2e0d0.png

## Main Components

- `run_baselines.py`  
  Main baseline experiment runner for no-RAG vs RAG conditions.

- `run_gpt_only.py`  
  GPT-only experimental run (requires `OPENAI_API_KEY`).

- `run_llama_only.py` / `run_phi3_quick.py`  
  Local Ollama-based runs for Phi-3/Llama-style experiments.

- `code_expermiments/code_expermiments/`  
  Supporting scripts for retrieval, generation, full pipeline execution, and evaluation.

- `hallucination_annotation/create_hallucination_template.py`  
  Utility script for hallucination annotation workflows.

## Environment Requirements

- Python 3.10+ recommended
- Internet access for first model download from Hugging Face
- Optional: OpenAI API key for GPT runs
- Optional: Ollama installed and running for local Phi-3/Llama runs

## Installation

1. (Recommended) Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## How To Run

### 1) Main Baseline Experiment (recommended)

```bash
python run_baselines.py
```

This generates CSV outputs in `results_v3/`.

### 2) GPT-Only Experiment (optional)

Set your API key first:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

Then run:

```bash
python run_gpt_only.py
```

Outputs are saved to `results_gpt/`.

### 3) Local Phi-3/Llama Experiment via Ollama (optional)

Make sure Ollama is running and the model is pulled, then run:

```bash
python run_llama_only.py
```

or quick test:

```bash
python run_phi3_quick.py
```

Outputs are saved to `results_llama/` or `results_llama_test/`.

## Example Data Included

- `data_samples/pubmedqa_500.csv`
- `data_samples/pubmedqa_first_6_rows.csv`

## Result Files Included

Typical output files include:

- `all_experiments.csv`
- `metrics_summary.csv`
- `confusion_matrices.csv`
- `prediction_distributions.csv`

(Stored under the respective `results*` directories.)

## Notes For Reproducibility

- Scripts use fixed sample sizes defined at the top of each file.
- First run may take longer due to model downloads.
- If GPT key is missing, GPT scripts will fail or skip GPT-dependent logic.
- For final reproduction, run from project root:
  `c:\Users\ayomi\Downloads\FYP-HealthHubQA`
