"""
Phi-3 Mini Quick Test: 10 No-RAG + 10 RAG = 20 rows
Saves each row immediately so nothing is lost.
"""

import uuid, requests, pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# ── config ──────────────────────────────────────────────────────────────────
N        = 10                       # samples per condition
MODEL    = "phi3:mini"
URL      = "http://localhost:11434/api/generate"
TIMEOUT  = 60                       # seconds per request
OUT      = Path("results_llama"); OUT.mkdir(exist_ok=True)
OUTFILE  = OUT / "phi3_results.csv"

# ── load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("data_samples/pubmedqa_500.csv").head(N).reset_index(drop=True)
print(f"Loaded {len(df)} samples\n")

# ── retriever ────────────────────────────────────────────────────────────────
enc  = SentenceTransformer("all-MiniLM-L6-v2")
ctxs = pd.read_csv("data_samples/pubmedqa_500.csv")["context"].fillna("").tolist()
embs = enc.encode(ctxs, show_progress_bar=False)

def retrieve(q):
    scores = cosine_similarity(enc.encode([q]), embs)[0]
    top3   = np.argsort(scores)[::-1][:3]
    # keep only first 150 chars per passage to avoid very long prompts
    return " | ".join(ctxs[i][:150] for i in top3)

# ── generate ─────────────────────────────────────────────────────────────────
def ask(prompt):
    try:
        r = requests.post(URL, json={
            "model": MODEL, "prompt": prompt,
            "stream": False, "options": {"num_predict": 80, "temperature": 0.3}
        }, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["response"].strip()
    except Exception as e:
        return f"[ERROR: {str(e)[:60]}]"

def label(text):
    t = text.lower()
    if "yes"   in t: return "yes"
    if "no"    in t: return "no"
    if "maybe" in t or "perhaps" in t: return "maybe"
    return "maybe"

# ── run ──────────────────────────────────────────────────────────────────────
rows = []
ts   = datetime.now().isoformat(timespec="seconds")

for setup in ["no_rag", "rag"]:
    print(f"\n{'='*60}\nCondition: PHI3 + {setup.upper()}\n{'='*60}")
    for i, row in df.iterrows():
        q = row["question"]

        if setup == "rag":
            ctx    = retrieve(q)
            prompt = (f"Using this medical context: {ctx}\n\n"
                      f"Answer yes, no, or maybe: {q}\n\nAnswer:")
        else:
            prompt = f"Answer yes, no, or maybe: {q}\n\nAnswer:"

        answer = ask(prompt)
        pred   = label(answer)
        true   = str(row["final_decision"]).lower()
        ok     = pred == true

        rows.append({
            "run_id":           str(uuid.uuid4()),
            "timestamp":        ts,
            "model":            "phi3_mini",
            "retrieval_setup":  setup,
            "sample_id":        i,
            "question":         q,
            "true_label":       true,
            "prediction_label": pred,
            "correct":          ok,
            "generated_answer": answer,
        })

        # save every row immediately
        pd.DataFrame(rows).to_csv(OUTFILE, index=False)
        status = "✓" if ok else "✗"
        print(f"  [{i+1:2d}/{N}] {status} true={true} pred={pred}  {answer[:60]}")

# ── metrics ──────────────────────────────────────────────────────────────────
rdf = pd.DataFrame(rows)
print(f"\n\nResults saved to {OUTFILE}  ({len(rdf)} rows)\n")
print(f"{'='*60}")

metrics = []
for setup in ["no_rag", "rag"]:
    sub    = rdf[rdf["retrieval_setup"] == setup]
    y_true = sub["true_label"].values
    y_pred = sub["prediction_label"].values
    acc    = accuracy_score(y_true, y_pred)
    f1     = f1_score(y_true, y_pred, average="macro", zero_division=0)
    prec   = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec    = recall_score(y_true, y_pred, average="macro", zero_division=0)
    metrics.append({"model":"phi3_mini","retrieval_setup":setup,
                    "num_samples":len(sub),"accuracy":round(acc,4),
                    "macro_f1":round(f1,4),"precision_macro":round(prec,4),
                    "recall_macro":round(rec,4)})
    print(f"PHI3 + {setup.upper()}: accuracy={acc:.2f}  macro_f1={f1:.2f}")

mdf = pd.DataFrame(metrics)
mdf.to_csv(OUT / "phi3_metrics_summary.csv", index=False)
print(f"\nMetrics saved to {OUT}/phi3_metrics_summary.csv")
