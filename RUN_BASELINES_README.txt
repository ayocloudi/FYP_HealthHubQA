================================================================================
RUN_BASELINES.PY - RESEARCH-GRADE MULTI-MODEL QA EXPERIMENT
================================================================================

OVERVIEW
--------
Single script that runs 4 baseline conditions (or 2 if GPT key missing):
  1) Flan-T5-base + No-RAG      [Baseline local model]
  2) Flan-T5-base + RAG        [Baseline with context retrieval]
  3) GPT-4 + No-RAG            [Large model, no retrieval] (if API key present)
  4) GPT-4 + RAG               [Large model with retrieval] (if API key present)

INPUTS
------
- data_samples/pubmedqa_500.csv          (500 medical Q&A samples)
- OPENAI_API_KEY environment variable    (optional, for GPT conditions)

OUTPUTS (in results/ directory)
------
1. all_experiments.csv                   (400 rows, one per sample × condition)
   Columns:
   - run_id, timestamp, model, retrieval_setup, sample_id
   - question, true_label, prediction_label, correct
   - generated_answer, token_length
   - top1_similarity, mean_similarity, retrieved_contexts

2. metrics_summary.csv                   (2-4 rows, grouped by condition)
   Columns:
   - model, retrieval_setup, num_samples
   - accuracy, macro_f1, precision_macro, recall_macro

3. confusion_matrices.csv                (confusion matrix per condition)
   Columns:
   - model, retrieval_setup, true_label, predicted_label, count

4. prediction_distributions.csv          (label distribution per condition)
   Columns:
   - model, retrieval_setup, prediction_label, count, percentage

FEATURES ADDED (Latest Version)
------
✅ GPT-4 API integration (only runs if OPENAI_API_KEY env var is set)
✅ Explicit skip message if GPT key missing
✅ Confusion matrices CSV output
✅ Prediction distributions CSV output
✅ Handles 3-way classification (yes/no/maybe)
✅ Retrieval logging: top1_similarity, mean_similarity, retrieved_contexts

HOW TO RUN
----------

1. Set OpenAI API key (optional, for GPT experiments):
   PowerShell:
     $env:OPENAI_API_KEY = "your-key-here"
   
2. Run the experiment:
   python run_baselines.py

   Expected output:
   - Loading dataset... ✓
   - Building retriever (MiniLM + Cosine Similarity)... ✓
   - Loading language models (Flan-T5)... ✓
   - Running 4 baseline conditions...
     * Flan-T5 + No-RAG    [100 samples]
     * Flan-T5 + RAG       [100 samples]
     * GPT + No-RAG        [100 samples] (if key present)
     * GPT + RAG           [100 samples] (if key present)
   - Writing CSVs... ✓
   - Metrics summary printed to console

3. Check results/ directory for CSV files

RETRIEVAL SETUP (RAG conditions only)
------
Model:      all-MiniLM-L6-v2 (384-dim embeddings)
Index:      Cosine similarity search (not FAISS for stability)
Sample:     Full PubMedQA dataset (500 contexts)
Top-K:      3 contexts retrieved per question

GENERATION SETUP
------
Local Model:
  - Model: google/flan-t5-base
  - Max length: 150 tokens
  - Decoding: Beam search (num_beams=4)
  - Temperature: 0.7 (balanced)

API Model:
  - Model: GPT-4
  - Max tokens: 150
  - Temperature: 0.7
  - Requires OPENAI_API_KEY env var

LABEL EXTRACTION
------
Simple heuristic: Extract first occurrence of 'yes', 'no', or 'maybe' from
generated text. Defaults to 'maybe' if ambiguous.

METRICS COMPUTED
------
Accuracy:        % correct predictions
Macro F1:        Unweighted F1 across all 3 classes
Precision (macro): Unweighted precision across all 3 classes
Recall (macro):  Unweighted recall across all 3 classes

VERSION HISTORY
------
v1.0  (Feb 2026): Initial implementation, Flan-T5 + GPT, 2 conditions
v2.0  (Feb 2026): Added GPT conditional logic, confusion matrices, 
                  prediction distributions, explicit skip messages

TROUBLESHOOTING
------
Q: "No module named 'openai'" error
A: Install with: pip install openai

Q: "RepositoryNotFoundError" when loading models
A: Models require internet access. Check connection.

Q: GPT conditions are skipped
A: Set OPENAI_API_KEY before running:
   $env:OPENAI_API_KEY = "sk-proj-..."

Q: Script hangs on model loading
A: First run downloads models (~5GB total). Wait 5-10 min.

Q: CUDA out of memory
A: Set DEVICE=cpu. Script already auto-detects GPU.
