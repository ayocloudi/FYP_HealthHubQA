"""
GPT-Only Baseline Experiment
============================
Runs 2 conditions over PubMedQA dataset (N=100):
  1) GPT-4 + No-RAG
  2) GPT-4 + RAG

Output:
  - results_gpt/gpt_experiments.csv      (detailed results, 200 rows)
  - results_gpt/gpt_metrics_summary.csv  (2 rows: one per condition)
"""

import os
import uuid
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
N_SAMPLES   = 100
TOP_K       = 3
MAX_TOKENS  = 150
OUTPUT_DIR  = Path("results_gpt")
OUTPUT_DIR.mkdir(exist_ok=True)

print("\n" + "="*80)
print("GPT-ONLY BASELINE EXPERIMENT")
print("="*80)
print(f"Samples : {N_SAMPLES}")
print(f"Top-K   : {TOP_K}")
print(f"Output  : {OUTPUT_DIR}\n")

# ============================================================================
# OPENAI CLIENT  (latest v1+ syntax)
# ============================================================================
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialised")
except ImportError:
    raise SystemExit(
        "\n[ERROR] openai package not found.\n"
        "Run:  pip install openai\n"
        "Then re-run this script."
    )

# ============================================================================
# STEP 1: LOAD DATASET
# ============================================================================
print("\nSTEP 1: Loading PubMedQA dataset...")
df_full = pd.read_csv("data_samples/pubmedqa_500.csv")
eval_df  = df_full.head(N_SAMPLES).copy().reset_index(drop=True)
eval_df["sample_id"] = range(len(eval_df))
print(f"✓ Loaded {len(eval_df)} samples")
print(f"  Label distribution:\n{eval_df['final_decision'].value_counts()}\n")

# ============================================================================
# STEP 2: BUILD RETRIEVER
# ============================================================================
print("STEP 2: Building retriever (MiniLM + cosine similarity)...")
retriever = SentenceTransformer("all-MiniLM-L6-v2")
all_contexts       = df_full["context"].fillna("").tolist()
context_embeddings = retriever.encode(all_contexts, show_progress_bar=False)
print(f"✓ Embedded {len(all_contexts)} contexts  (dim={context_embeddings.shape[1]})\n")

def retrieve(question: str, top_k: int = TOP_K) -> dict:
    q_emb = retriever.encode([question])
    scores = cosine_similarity(q_emb, context_embeddings)[0]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return {
        "contexts": [all_contexts[i] for i in top_idx],
        "scores":   [float(scores[i]) for i in top_idx],
    }

# ============================================================================
# STEP 3: GPT GENERATION  (v1 SDK)
# ============================================================================
def generate_gpt(question: str, context: dict | None = None, use_context: bool = True) -> tuple[str, int]:
    """
    Call GPT-4 and return (answer_text, word_count).

    Parameters
    ----------
    question    : The medical question string.
    context     : Dict returned by retrieve() – used when use_context=True.
    use_context : Whether to inject retrieved passages into the prompt.

    Returns
    -------
    (answer_text, token_length)  – on API error returns an error string + -1.
    """
    if use_context and context and context.get("contexts"):
        combined = " | ".join(context["contexts"])
        user_msg = (
            "Based on the following medical context, answer the question with "
            "yes, no, or maybe, followed by brief reasoning.\n\n"
            f"Context: {combined}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
    else:
        user_msg = (
            "Answer the following medical question with yes, no, or maybe, "
            "followed by brief reasoning.\n\n"
            f"Question: {question}\n\nAnswer:"
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=MAX_TOKENS,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        return answer, len(answer.split())

    except Exception as exc:
        # Log and continue – never crash the whole run
        short_err = str(exc)[:120]
        print(f"    [API ERROR] {short_err}")
        return f"[GPT Error: {short_err}]", -1


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
    {"label": "GPT + NO_RAG", "model": "gpt", "retrieval_setup": "no_rag", "use_rag": False},
    {"label": "GPT + RAG",    "model": "gpt", "retrieval_setup": "rag",    "use_rag": True},
]

results = []
run_ts  = datetime.now().isoformat(timespec="seconds")

for cond in CONDITIONS:
    print("="*80)
    print(f"Condition: {cond['label']}")
    print("="*80)

    for idx, row in eval_df.iterrows():
        question  = row["question"]
        true_label = str(row["final_decision"]).lower()

        # Retrieval
        retrieved = retrieve(question) if cond["use_rag"] else None

        # Generation
        answer, tok_len = generate_gpt(
            question,
            context     = retrieved,
            use_context = cond["use_rag"],
        )

        pred_label = extract_label(answer)

        results.append({
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
        })

        if (idx + 1) % 25 == 0:
            print(f"  Processed {idx + 1}/{N_SAMPLES} samples")

    print(f"✓ Completed {cond['label']}\n")

# ============================================================================
# STEP 6: SAVE RESULTS
# ============================================================================
results_df = pd.DataFrame(results)
out_experiments = OUTPUT_DIR / "gpt_experiments.csv"
results_df.to_csv(out_experiments, index=False)
print(f"✓ Saved: {out_experiments}  ({len(results_df)} rows)\n")

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
    f1   = f1_score(y_true, y_pred, average="macro", zero_division=0)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="macro", zero_division=0)

    metrics.append({
        "model":            model,
        "retrieval_setup":  setup,
        "num_samples":      len(sub),
        "accuracy":         round(acc,  4),
        "macro_f1":         round(f1,   4),
        "precision_macro":  round(prec, 4),
        "recall_macro":     round(rec,  4),
    })

    print(f"{model.upper()} + {setup.upper()}:")
    print(f"  Samples  : {len(sub)}")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  Macro F1 : {f1:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall   : {rec:.4f}\n")

metrics_df = pd.DataFrame(metrics)
out_metrics = OUTPUT_DIR / "gpt_metrics_summary.csv"
metrics_df.to_csv(out_metrics, index=False)
print(f"✓ Saved: {out_metrics}\n")

# ============================================================================
# DONE
# ============================================================================
print("="*80)
print("EXPERIMENT COMPLETE")
print("="*80)
print(f"\nOutput files:")
print(f"  1. {out_experiments}")
print(f"  2. {out_metrics}")
print()
print(metrics_df.to_string(index=False))
