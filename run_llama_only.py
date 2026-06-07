"""
Llama 3 Baseline Experiment (via Ollama)
=========================================
Runs 2 conditions over PubMedQA dataset (N=100):
  1) Phi-3 Mini + No-RAG
  2) Phi-3 Mini + RAG

Requires Ollama running locally:
  1. Install: https://ollama.com/download/windows
  2. Pull model: ollama pull phi3:mini
  3. Run this script: python run_llama_only.py

Output:
  - results_llama/llama_experiments.csv     (200 rows)
  - results_llama/llama_metrics_summary.csv (2 rows)
"""

import os
import uuid
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# ============================================================================
# CONFIGURATION
# ============================================================================
N_SAMPLES    = 20
TOP_K        = 3
MAX_TOKENS   = 150
OLLAMA_URL   = "http://localhost:11434"
MODEL_NAME   = "phi3:mini"       # ~2.3GB RAM — fits on most machines; change to "llama3" if you have 6GB+ free
OUTPUT_DIR   = Path("results_llama_test")
OUTPUT_DIR.mkdir(exist_ok=True)

print("\n" + "="*80)
print("PHI-3 MINI BASELINE EXPERIMENT  (via Ollama)")
print("="*80)
print(f"Model   : {MODEL_NAME}")
print(f"Samples : {N_SAMPLES}")
print(f"Top-K   : {TOP_K}")
print(f"Output  : {OUTPUT_DIR}\n")

# ============================================================================
# CHECK OLLAMA IS REACHABLE
# ============================================================================
def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"✓ Ollama is running")
        print(f"  Available models: {models}")
        if not any(MODEL_NAME in m for m in models):
            print(f"\n⚠  Model '{MODEL_NAME}' not found locally.")
            print(f"   Run this in a terminal first:  ollama pull phi3:mini")
            print(f"   Then re-run this script.\n")
            raise SystemExit(1)
        return True
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to Ollama at http://localhost:11434")
        print("Make sure Ollama is installed and running:")
        print("  1. Download: https://ollama.com/download/windows")
        print("  2. Install and launch Ollama")
        print("  3. In a terminal run:  ollama pull llama3")
        print("  4. Then re-run this script\n")
        raise SystemExit(1)

check_ollama()

# ============================================================================
# STEP 1: LOAD DATASET
# ============================================================================
print("\nSTEP 1: Loading PubMedQA dataset...")
df_full  = pd.read_csv("data_samples/pubmedqa_500.csv")
eval_df  = df_full.head(N_SAMPLES).copy().reset_index(drop=True)
eval_df["sample_id"] = range(len(eval_df))
print(f"✓ Loaded {len(eval_df)} samples")
print(f"  Label distribution:\n{eval_df['final_decision'].value_counts()}\n")

# ============================================================================
# STEP 2: BUILD RETRIEVER
# ============================================================================
print("STEP 2: Building retriever (MiniLM + cosine similarity)...")
retriever          = SentenceTransformer("all-MiniLM-L6-v2")
all_contexts       = df_full["context"].fillna("").tolist()
context_embeddings = retriever.encode(all_contexts, show_progress_bar=False)
print(f"✓ Embedded {len(all_contexts)} contexts  (dim={context_embeddings.shape[1]})\n")

def retrieve(question: str, top_k: int = TOP_K) -> dict:
    q_emb  = retriever.encode([question])
    scores = cosine_similarity(q_emb, context_embeddings)[0]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return {
        "contexts": [all_contexts[i] for i in top_idx],
        "scores":   [float(scores[i]) for i in top_idx],
    }

# ============================================================================
# STEP 3: LLAMA 3 GENERATION  (Ollama REST API)
# ============================================================================
def generate_llama(question: str, context: dict | None = None, use_context: bool = True) -> tuple[str, int]:
    """
    Call Llama 3 via Ollama and return (answer_text, word_count).
    On error returns an error string and -1.
    """
    if use_context and context and context.get("contexts"):
        # Truncate each context to 100 chars to keep prompt short enough for CPU inference
        truncated = [c[:100] for c in context["contexts"]]
        combined = " | ".join(truncated)
        prompt = (
            "Based on the following medical context, answer the question with "
            "yes, no, or maybe, followed by brief reasoning.\n\n"
            f"Context: {combined}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
    else:
        prompt = (
            "Answer the following medical question with yes, no, or maybe, "
            "followed by brief reasoning.\n\n"
            f"Question: {question}\n\nAnswer:"
        )

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model":  MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": MAX_TOKENS,
                    "temperature": 0.7,
                }
            },
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json()["response"].strip()
        return answer, len(answer.split())

    except Exception as exc:
        short_err = str(exc)[:120]
        print(f"    [LLAMA ERROR] {short_err}")
        return f"[Llama Error: {short_err}]", -1


# ============================================================================
# STEP 4: LABEL EXTRACTION
# ============================================================================
def extract_label(text: str) -> str:
    t = text.lower()
    if "yes"   in t: return "yes"
    if "no"    in t: return "no"
    if "maybe" in t or "perhaps" in t or "uncertain" in t: return "maybe"
    first = t.split()[0] if t.split() else ""
    return first if first in ("yes", "no", "maybe") else "maybe"


# ============================================================================
# STEP 5: RUN EXPERIMENTS
# ============================================================================
CONDITIONS = [
    {"label": "PHI3 + NO_RAG", "model": "phi3_mini", "retrieval_setup": "no_rag", "use_rag": False},
    {"label": "PHI3 + RAG",    "model": "phi3_mini", "retrieval_setup": "rag",    "use_rag": True},
]

run_ts       = datetime.now().isoformat(timespec="seconds")
out_exp      = OUTPUT_DIR / "llama_experiments.csv"
COLUMNS      = ["run_id","timestamp","model","retrieval_setup","sample_id",
                 "question","true_label","prediction_label","correct",
                 "generated_answer","token_length","top1_similarity",
                 "mean_similarity","retrieved_contexts"]

# Write header once
pd.DataFrame(columns=COLUMNS).to_csv(out_exp, index=False)

for cond in CONDITIONS:
    print("="*80)
    print(f"Condition: {cond['label']}")
    print("="*80)

    for idx, row in eval_df.iterrows():
        question   = row["question"]
        true_label = str(row["final_decision"]).lower()

        retrieved = retrieve(question) if cond["use_rag"] else None

        answer, tok_len = generate_llama(
            question,
            context     = retrieved,
            use_context = cond["use_rag"],
        )

        pred_label = extract_label(answer)

        result_row = {
            "run_id":            str(uuid.uuid4()),
            "timestamp":         run_ts,
            "model":             cond["model"],
            "retrieval_setup":   cond["retrieval_setup"],
            "sample_id":         int(row["sample_id"]),
            "question":          question,
            "true_label":        true_label,
            "prediction_label":  pred_label,
            "correct":           pred_label == true_label,
            "generated_answer":  answer,
            "token_length":      tok_len,
            "top1_similarity":   round(retrieved["scores"][0], 4) if retrieved else None,
            "mean_similarity":   round(float(np.mean(retrieved["scores"])), 4) if retrieved else None,
            "retrieved_contexts": str(retrieved) if retrieved else None,
        }

        # Append row immediately — safe against interruption
        pd.DataFrame([result_row]).to_csv(out_exp, mode="a", header=False, index=False)

        if (idx + 1) % 5 == 0:
            print(f"  Processed {idx + 1}/{N_SAMPLES} samples")

    print(f"✓ Completed {cond['label']}\n")

# ============================================================================
# STEP 6: RESULTS ALREADY SAVED ROW-BY-ROW — just reload for metrics
# ============================================================================
results_df = pd.read_csv(out_exp)
print(f"✓ Saved: {out_exp}  ({len(results_df)} rows)\n")

# ============================================================================
# STEP 7: METRICS
# ============================================================================
print("STEP 7: Computing metrics...\n")
metrics = []

for cond in CONDITIONS:
    model = cond["model"]
    setup = cond["retrieval_setup"]
    sub   = results_df[(results_df["model"] == model) & (results_df["retrieval_setup"] == setup)]

    if sub.empty:
        continue

    y_true = sub["true_label"].values
    y_pred = sub["prediction_label"].values

    acc  = accuracy_score(y_true, y_pred)
    f1   = f1_score(y_true, y_pred,  average="macro", zero_division=0)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec  = recall_score(y_true, y_pred,  average="macro", zero_division=0)

    metrics.append({
        "model":           model,
        "retrieval_setup": setup,
        "num_samples":     len(sub),
        "accuracy":        round(acc,  4),
        "macro_f1":        round(f1,   4),
        "precision_macro": round(prec, 4),
        "recall_macro":    round(rec,  4),
    })

    print(f"{model.upper()} + {setup.upper()}:")
    print(f"  Samples  : {len(sub)}")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  Macro F1 : {f1:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall   : {rec:.4f}\n")

metrics_df = pd.DataFrame(metrics)
out_met    = OUTPUT_DIR / "llama_metrics_summary.csv"
metrics_df.to_csv(out_met, index=False)
print(f"✓ Saved: {out_met}\n")

# ============================================================================
# DONE
# ============================================================================
print("="*80)
print("EXPERIMENT COMPLETE")
print("="*80)
print(f"\nOutput files:")
print(f"  1. {out_exp}")
print(f"  2. {out_met}")
print()
print(metrics_df.to_string(index=False))
