"""
RUN_COMPARISON.ps1
==================
Quick batch runner for the multi-model comparison experiment

Usage:
  .\run_comparison.ps1

This will:
1. Activate the virtual environment
2. Run the multi-model comparison (30 samples)
3. Run the metrics analysis
4. Display results
"""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Navigate to experiments folder
cd healthhubqa/code_expermiments/code_expermiments

Write-Host "`nStarting Multi-Model Comparison Experiment..." -ForegroundColor Cyan
Write-Host "Grid: 2 models (Flan-T5, GPT) × 2 conditions (No-RAG, RAG)" -ForegroundColor Cyan
Write-Host "Samples: 30 (initially)" -ForegroundColor Cyan
Write-Host ""

# Run the main comparison
python 10_multi_model_comparison.py

# Check if results were generated
$resultsExist = Test-Path "results/multi_model_comparison/raw_results_*.csv"

if ($resultsExist) {
    Write-Host "`nRunning metrics analysis..." -ForegroundColor Green
    python 11_metrics_analysis.py
} else {
    Write-Host "`nWarning: Results not found. Please check the output above for errors." -ForegroundColor Yellow
}

Write-Host "`nDone! Check results/multi_model_comparison/ for CSV files." -ForegroundColor Green
