"""
Research-Grade Baseline Experiment: Multi-Model & Multi-Condition QA
====================================================================
Runs 4 conditions over PubMedQA dataset (N=100):
  1) Flan-T5 + No-RAG
  2) Flan-T5 + RAG
  3) GPT-4 + No-RAG
  4) GPT-4 + RAG

Output:
  - results/all_experiments.csv (detailed results, ~400 rows)
  - results/metrics_summary.csv (4 rows: one per condition)
"""

import pandas as pd
import numpy as np
import torch
import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Transformers
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer

# Similarity
from sklearn.metrics.pairwise import cosine_similarity

# Metrics
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix

# ============================================================================
# CONFIGURATION
# ============================================================================
N_SAMPLES = 100  # Configurable sample size for quick testing (set to 100 for full run)
SAMPLE_SIZE = N_SAMPLES
TOP_K_RETRIEVAL = 3
MAX_ANSWER_LENGTH = 150
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_DIR = Path("results_v3")  # Full run with 100 samples
OUTPUT_DIR.mkdir(exist_ok=True)

print("\n" + "="*80)
print("RESEARCH-GRADE BASELINE EXPERIMENT")
print("="*80)
print(f"Device: {DEVICE}")
print(f"Sample Size: {SAMPLE_SIZE}")
print(f"Top-K Retrieval: {TOP_K_RETRIEVAL}")
print(f"Output Directory: {OUTPUT_DIR}")
if N_SAMPLES < 100:
    print(f"\n⚠ SANITY CHECK MODE: Running with N_SAMPLES = {N_SAMPLES}\n")
else:
    print()

# ============================================================================
# STEP 1: LOAD DATASET
# ============================================================================
print("STEP 1: Loading PubMedQA dataset...")
df = pd.read_csv("data_samples/pubmedqa_500.csv")
# Use first SAMPLE_SIZE samples
eval_df = df.head(SAMPLE_SIZE).copy().reset_index(drop=True)
eval_df['sample_id'] = range(len(eval_df))
print(f"✓ Loaded {len(eval_df)} samples")
print(f"  Columns: {eval_df.columns.tolist()}")
print(f"  Label distribution:\n{eval_df['final_decision'].value_counts()}\n")

# ============================================================================
# STEP 2: BUILD RETRIEVER (Sentence Transformers + Cosine Similarity)
# ============================================================================
print("STEP 2: Building retriever (MiniLM + Cosine Similarity)...")
retriever_model = SentenceTransformer('all-MiniLM-L6-v2')

# Embed all contexts
contexts = df['context'].fillna("").tolist()
context_embeddings = retriever_model.encode(contexts, show_progress_bar=False)
print(f"✓ Embedded {len(contexts)} contexts")
print(f"  Embedding dimension: {context_embeddings.shape[1]}\n")

def retrieve_contexts(question, k=TOP_K_RETRIEVAL):
    """
    Retrieve top-k contexts for a question using cosine similarity.
    Returns: (contexts_str, top1_similarity, mean_similarity)
    """
    question_emb = retriever_model.encode([question])
    
    # Compute cosine similarity between question and all contexts
    similarities = cosine_similarity(question_emb, context_embeddings)[0]
    
    # Get top-k indices
    top_k_indices = np.argsort(similarities)[::-1][:k]
    top_k_sims = similarities[top_k_indices]
    
    retrieved_context_texts = [contexts[idx] for idx in top_k_indices]
    concatenated = " | ".join(retrieved_context_texts)
    
    top1_sim = float(top_k_sims[0])
    mean_sim = float(np.mean(top_k_sims))
    
    return concatenated, top1_sim, mean_sim

# STEP 3: LOAD LANGUAGE MODELS
# ============================================================================
print("STEP 3: Loading language models...")

# Model 1: Flan-T5-base
print("  Loading Flan-T5-base...")
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
flan_model = flan_model.to(DEVICE)
print("  ✓ Flan-T5-base loaded")

# Model 2: BioBart-base
print("  Loading BioBart-base...")
try:
    biobart_tokenizer = AutoTokenizer.from_pretrained("GanjinZero/biobart-base")
    biobart_model = AutoModelForSeq2SeqLM.from_pretrained("GanjinZero/biobart-base")
    biobart_model = biobart_model.to(DEVICE)
    print("  ✓ BioBart-base loaded")
    biobart_available = True
except Exception as e:
    print(f"  ⚠ BioBart-base failed: {str(e)[:50]}... Skipping")
    biobart_available = False

# Model 3: DistilBART
print("  Loading DistilBART (CNN)...")
try:
    distilbart_tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")
    distilbart_model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6")
    distilbart_model = distilbart_model.to(DEVICE)
    print("  ✓ DistilBART loaded\n")
    distilbart_available = True
except Exception as e:
    print(f"  ⚠ DistilBART failed: {str(e)[:50]}... Skipping")
    distilbart_available = False
    print()

def generate_flan_t5(question, context=None, use_context=True):
    """
    Generate answer using Flan-T5.
    Returns: (answer_text, token_length)
    """
    if use_context and context:
        prompt = f"""Based on the following medical context, answer the question with yes, no, or maybe, followed by brief reasoning.

Context: {context}

Question: {question}

Answer:"""
    else:
        prompt = f"""Answer the following medical question with yes, no, or maybe, followed by brief reasoning.

Question: {question}

Answer:"""
    
    inputs = flan_tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(DEVICE)
    
    with torch.no_grad():
        outputs = flan_model.generate(
            **inputs,
            max_length=MAX_ANSWER_LENGTH,
            min_length=5,
            num_beams=4,
            early_stopping=True,
            temperature=0.7,
            do_sample=False
        )
    
    answer_text = flan_tokenizer.decode(outputs[0], skip_special_tokens=True)
    token_length = len(outputs[0])
    
    return answer_text, token_length

def generate_biobart(question, context=None, use_context=True):
    """
    Generate answer using BioBart.
    Returns: (answer_text, token_length)
    """
    if use_context and context:
        prompt = f"""Based on the following medical context, answer the question with yes, no, or maybe, followed by brief reasoning.

Context: {context}

Question: {question}

Answer:"""
    else:
        prompt = f"""Answer the following medical question with yes, no, or maybe, followed by brief reasoning.

Question: {question}

Answer:"""
    
    inputs = biobart_tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(DEVICE)
    
    with torch.no_grad():
        outputs = biobart_model.generate(
            **inputs,
            max_length=MAX_ANSWER_LENGTH,
            min_length=5,
            num_beams=4,
            early_stopping=True,
            do_sample=False
        )
    
    answer_text = biobart_tokenizer.decode(outputs[0], skip_special_tokens=True)
    token_length = len(outputs[0])
    
    return answer_text, token_length

def generate_distilbart(question, context=None, use_context=True):
    """
    Generate answer using DistilBART.
    Returns: (answer_text, token_length)
    """
    if use_context and context:
        prompt = f"""Based on the following medical context, answer the question with yes, no, or maybe, followed by brief reasoning.

Context: {context}

Question: {question}

Answer:"""
    else:
        prompt = f"""Answer the following medical question with yes, no, or maybe, followed by brief reasoning.

Question: {question}

Answer:"""
    
    inputs = distilbart_tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(DEVICE)
    
    with torch.no_grad():
        outputs = distilbart_model.generate(
            **inputs,
            max_length=MAX_ANSWER_LENGTH,
            min_length=5,
            num_beams=4,
            early_stopping=True,
            do_sample=False
        )
    
    answer_text = distilbart_tokenizer.decode(outputs[0], skip_special_tokens=True)
    token_length = len(outputs[0])
    
    return answer_text, token_length

# ============================================================================
# STEP 4: GPT PLACEHOLDER FUNCTION
# ============================================================================
gpt_api_key = os.getenv("OPENAI_API_KEY")

def generate_gpt(question, context=None, use_context=True, debug=False, sample_id=None):
    """
    Generate answer using GPT-4 API.
    Returns: (answer_text, token_length)
    
    Args:
        debug: If True, prints verification logs for RAG mode
        sample_id: Sample index for debug logging
    """
    # Construct user message
    if use_context and context:
        user_msg = f"""Based on the following medical context, answer the question with yes, no, or maybe, followed by brief reasoning.

Context: {context}

Question: {question}

Answer:"""
    else:
        user_msg = f"""Answer the following medical question with yes, no, or maybe, followed by brief reasoning.

Question: {question}

Answer:"""
    
    # Debug logging for RAG mode
    if debug and use_context:
        print(f"\n  [DEBUG - Sample {sample_id}]")
        print(f"  Question: {question[:80]}...")
        if context:
            ctx_preview = context[:150].replace("\n", " ")
            print(f"  Retrieved Context (truncated): {ctx_preview}...")
        else:
            print("  ⚠ Retrieved Context: MISSING or EMPTY")
        print(f"  Prompt format verified: {('Context:' in user_msg and 'Question:' in user_msg)}")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=gpt_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=MAX_ANSWER_LENGTH,
            temperature=0.7
        )
        
        answer_text = response.choices[0].message.content
        token_length = len(answer_text.split())
        
        # Debug logging of response
        if debug and use_context:
            print(f"  Generated Answer: {answer_text[:80]}...")
        
        return answer_text, token_length
    
    except Exception as e:
        error_msg = str(e)[:50]
        return f"[GPT Error: {error_msg}]", 5

# ============================================================================
# STEP 5: EXTRACT LABEL FROM ANSWER (for binary classification)
# ============================================================================
def extract_label(answer_text):
    """
    Extract yes/no/maybe from generated answer text.
    Simple heuristic: look for first occurrence of yes/no/maybe.
    """
    text_lower = answer_text.lower()
    
    if 'yes' in text_lower:
        return 'yes'
    elif 'no' in text_lower:
        return 'no'
    elif 'maybe' in text_lower or 'perhaps' in text_lower or 'uncertain' in text_lower:
        return 'maybe'
    else:
        # Default: assign based on first word if it contains decision words
        first_word = text_lower.split()[0] if text_lower.split() else ""
        if first_word in ['yes', 'no', 'maybe']:
            return first_word
        else:
            return 'maybe'  # conservative default

# ============================================================================
# STEP 6: RUN EXPERIMENTS
# ============================================================================
print(f"STEP 5: Running baseline conditions (N_SAMPLES = {N_SAMPLES})...\n")

conditions = [
    ("flan_t5", "no_rag"),
    ("flan_t5", "rag"),
]

# Add BioBart conditions if available
if biobart_available:
    conditions.extend([
        ("biobart", "no_rag"),
        ("biobart", "rag"),
    ])

# Add DistilBART conditions if available
if distilbart_available:
    conditions.extend([
        ("distilbart", "no_rag"),
        ("distilbart", "rag"),
    ])

# Add GPT conditions only if API key is available
if gpt_api_key:
    conditions.extend([
        ("gpt", "no_rag"),
        ("gpt", "rag"),
    ])
else:
    print("⚠ Skipping GPT: missing OPENAI_API_KEY environment variable")
    print("  Set key with: $env:OPENAI_API_KEY = 'your-key-here'\n")

all_results = []
run_id = str(uuid.uuid4())[:8]

for model, setup in conditions:
    print(f"\n{'='*80}")
    print(f"Condition: {model.upper()} + {setup.upper()}")
    print('='*80)
    
    for idx, row in eval_df.iterrows():
        question = row['question']
        true_label = row['final_decision']
        sample_id = row['sample_id']
        
        # Retrieve contexts if RAG
        if setup == "rag":
            context, top1_sim, mean_sim = retrieve_contexts(question, k=TOP_K_RETRIEVAL)
            
            # Verification: warn if context is empty in RAG mode
            if not context or context.strip() == "":
                print(f"  ⚠ [Sample {sample_id}] Retrieval context not passed to prompt - EMPTY")
        else:
            context = None
            top1_sim = None
            mean_sim = None
        
        # Generate answer based on model
        if model == "flan_t5":
            answer, token_length = generate_flan_t5(
                question, 
                context=context, 
                use_context=(setup == "rag")
            )
        elif model == "biobart":
            answer, token_length = generate_biobart(
                question, 
                context=context, 
                use_context=(setup == "rag")
            )
        elif model == "distilbart":
            answer, token_length = generate_distilbart(
                question, 
                context=context, 
                use_context=(setup == "rag")
            )
        else:  # gpt
            # Enable debug logging every 5 samples for GPT + RAG
            debug_mode = (model == "gpt" and setup == "rag" and (sample_id + 1) % 5 == 0)
            answer, token_length = generate_gpt(
                question, 
                context=context, 
                use_context=(setup == "rag"),
                debug=debug_mode,
                sample_id=sample_id
            )
        
        # Extract predicted label
        pred_label = extract_label(answer)
        
        # Mark as correct
        is_correct = (pred_label == true_label)
        
        # Log result
        all_results.append({
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'retrieval_setup': setup,
            'sample_id': sample_id,
            'question': question,
            'true_label': true_label,
            'prediction_label': pred_label,
            'correct': int(is_correct),
            'generated_answer': answer,
            'token_length': token_length,
            'top1_similarity': top1_sim,
            'mean_similarity': mean_sim,
            'retrieved_contexts': context if setup == "rag" else ""
        })
        
        # Progress indicator
        if (idx + 1) % 25 == 0 or idx == len(eval_df) - 1:
            print(f"  Processed {idx + 1}/{len(eval_df)} samples")
    
    print(f"✓ Completed {model.upper()} + {setup.upper()}")

print(f"\n✓ All experiments completed. Total results: {len(all_results)}")

# ============================================================================
# STEP 7: WRITE UNIFIED CSV
# ============================================================================
print("\nSTEP 6: Writing results CSV...")

results_df = pd.DataFrame(all_results)
all_experiments_file = OUTPUT_DIR / "all_experiments.csv"
results_df.to_csv(all_experiments_file, index=False)
print(f"✓ Saved: {all_experiments_file}")
print(f"  Rows: {len(results_df)}")
print(f"  Columns: {results_df.columns.tolist()}")

# ============================================================================
# RETRIEVAL VERIFICATION (for RAG conditions)
# ============================================================================
print("\n[RETRIEVAL VERIFICATION]")
unique_models = results_df['model'].unique().tolist()
for model_name in unique_models:
    for setup in ['rag']:
        subset = results_df[(results_df['model'] == model_name) & (results_df['retrieval_setup'] == setup)]
        if len(subset) > 0:
            has_context = subset['retrieved_contexts'].notna() & (subset['retrieved_contexts'] != "")
            context_populated = has_context.sum()
            print(f"  {model_name.upper()} + RAG: {context_populated}/{len(subset)} samples have retrieved contexts")
            if context_populated == 0:
                print(f"    ⚠ WARNING: No retrieved contexts found for {model_name} RAG!")

# ============================================================================
# STEP 8: COMPUTE METRICS (grouped by model + retrieval_setup)
# ============================================================================
print("\nSTEP 7: Computing metrics...")

metrics_list = []

# Dynamically extract unique models from results
model_list = results_df['model'].unique().tolist()

for model in model_list:
    for setup in ['no_rag', 'rag']:
        subset = results_df[(results_df['model'] == model) & (results_df['retrieval_setup'] == setup)]
        
        if len(subset) == 0:
            continue
        
        y_true = subset['true_label'].values
        y_pred = subset['prediction_label'].values
        
        # Compute metrics (with zero_division=0 to handle edge cases)
        accuracy = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        macro_precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        
        metrics_list.append({
            'model': model,
            'retrieval_setup': setup,
            'num_samples': len(subset),
            'accuracy': round(accuracy, 4),
            'macro_f1': round(macro_f1, 4),
            'precision_macro': round(macro_precision, 4),
            'recall_macro': round(macro_recall, 4),
        })
        
        print(f"\n{model.upper()} + {setup.upper()}:")
        print(f"  Samples: {len(subset)}")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Macro F1: {macro_f1:.4f}")
        print(f"  Macro Precision: {macro_precision:.4f}")
        print(f"  Macro Recall: {macro_recall:.4f}")

# ============================================================================
# STEP 9: WRITE METRICS CSV
# ============================================================================
metrics_df = pd.DataFrame(metrics_list)
metrics_file = OUTPUT_DIR / "metrics_summary.csv"
metrics_df.to_csv(metrics_file, index=False)
print(f"\n✓ Saved: {metrics_file}\n")

# ============================================================================
# STEP 10: GENERATE CONFUSION MATRICES
# ============================================================================
print("STEP 8: Generating confusion matrices...\n")

confusion_matrices_list = []

for model in model_list:
    for setup in ['no_rag', 'rag']:
        subset = results_df[(results_df['model'] == model) & (results_df['retrieval_setup'] == setup)]
        
        if len(subset) == 0:
            continue
        
        y_true = subset['true_label'].values
        y_pred = subset['prediction_label'].values
        
        # Get unique labels from data
        labels = sorted(list(set(list(y_true) + list(y_pred))))
        
        # Compute confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Store as rows: one row = one predicted label in the matrix
        for i, pred_label in enumerate(labels):
            for j, true_label in enumerate(labels):
                confusion_matrices_list.append({
                    'model': model,
                    'retrieval_setup': setup,
                    'true_label': true_label,
                    'predicted_label': pred_label,
                    'count': int(cm[j, i])
                })

confusion_df = pd.DataFrame(confusion_matrices_list)
confusion_file = OUTPUT_DIR / "confusion_matrices.csv"
confusion_df.to_csv(confusion_file, index=False)
print(f"✓ Saved: {confusion_file}\n")

# ============================================================================
# STEP 11: GENERATE PREDICTION DISTRIBUTIONS
# ============================================================================
print("STEP 9: Generating prediction distributions...\n")

pred_dist_list = []

for model in model_list:
    for setup in ['no_rag', 'rag']:
        subset = results_df[(results_df['model'] == model) & (results_df['retrieval_setup'] == setup)]
        
        if len(subset) == 0:
            continue
        
        # Get distribution of predictions
        pred_counts = subset['prediction_label'].value_counts()
        total = len(subset)
        
        for label, count in pred_counts.items():
            pred_dist_list.append({
                'model': model,
                'retrieval_setup': setup,
                'prediction_label': label,
                'count': int(count),
                'percentage': round(100.0 * count / total, 2)
            })

pred_dist_df = pd.DataFrame(pred_dist_list)
pred_dist_file = OUTPUT_DIR / "prediction_distributions.csv"
pred_dist_df.to_csv(pred_dist_file, index=False)
print(f"✓ Saved: {pred_dist_file}\n")

# ============================================================================
# STEP 10: PRINT SUMMARY TABLE
# ============================================================================
print("="*80)
print("METRICS SUMMARY TABLE")
print("="*80 + "\n")
print(metrics_df.to_string(index=False))
print("\n" + "="*80)
print("EXPERIMENT COMPLETE")
print("="*80)
print(f"\nOutput files:")
print(f"  1. {all_experiments_file}")
print(f"  2. {metrics_file}")
print(f"  3. {confusion_file}")
print(f"  4. {pred_dist_file}\n")
