"""
Master Pipeline Runner — HackNova 2 PortfolioIQ
Runs all tasks in sequence and prints final submission checklist.
"""

import subprocess
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCRIPTS_DIR = os.path.dirname(__file__)

TASKS = [
    ('01_data_fetch.py', 'Task 1: Data Acquisition & Quality'),
    ('02_risk_return.py', 'Task 2: Risk & Return Analysis'),
    ('03_sma_signals.py', 'Task 3: Technical Signal Dashboard'),
    ('04_portfolio.py', 'Task 4: Portfolio Construction'),
    ('05_ml_model.py', 'Task 5: ML Model Training & Evaluation'),
    ('06_chaos_round.py', 'Task 6: Chaos Round Stress Test'),
    ('07_generate_slides.py', 'Task 7: Presentation Slides'),
]


def run_task(script_name, description):
    """Run a single task script."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f"\n{'━' * 70}")
    print(f"▶ RUNNING: {description}")
    print(f"  Script: {script_name}")
    print(f"{'━' * 70}")
    
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ {description} — PASSED ({elapsed:.1f}s)")
            return True
        else:
            print(result.stdout)
            print(f"\n❌ STDERR:\n{result.stderr}")
            print(f"\n❌ {description} — FAILED ({elapsed:.1f}s)")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️ {description} — TIMEOUT (>300s)")
        return False
    except Exception as e:
        print(f"\n❌ {description} — ERROR: {e}")
        return False


def check_deliverables():
    """Check final submission deliverables."""
    print(f"\n\n{'═' * 70}")
    print("📋 FINAL SUBMISSION CHECKLIST")
    print(f"{'═' * 70}")
    
    deliverables = [
        ('data/raw_dataset.csv', 'Raw fetched dataset (15 stocks + Nifty 50)'),
        ('data/cleaned_dataset.csv', 'Cleaned dataset'),
        ('data/adj_close_pivot.csv', 'Adj Close pivot table'),
        ('submissions/metrics_summary.csv', 'Metrics summary table (6 metrics × 15 stocks)'),
        ('submissions/metrics_summary.xlsx', 'Metrics summary (Excel)'),
        ('charts/risk_return_scatter.png', 'Risk-Return scatter plot'),
        ('charts/correlation_heatmap.png', 'Correlation heatmap'),
        ('submissions/sma_signal_table.csv', 'SMA Signal table'),
        ('charts/sma_banking.png', 'SMA chart — Banking sector'),
        ('charts/sma_it.png', 'SMA chart — IT sector'),
        ('charts/sma_pharma.png', 'SMA chart — Pharma sector'),
        ('submissions/portfolio_comparison.csv', 'Portfolio A vs B comparison'),
        ('submissions/portfolio_allocations.csv', 'Portfolio allocations'),
        ('submissions/sector_breakdown.csv', 'Sector breakdown'),
        ('charts/portfolio_comparison.png', 'Portfolio comparison chart'),
        ('submissions/portfolio_justification_TEMPLATE.md', 'Portfolio justification template'),
        ('data/ml_feature_matrix.csv', 'ML feature matrix'),
        ('submissions/ml_comparison_table.csv', 'ML model comparison table'),
        ('submissions/ml_sector_evaluation.csv', 'ML per-sector evaluation'),
        ('charts/ml_feature_importance.png', 'ML feature importance chart'),
        ('charts/ml_confusion_matrix.png', 'ML confusion matrix chart'),
        ('charts/ml_roc_curve.png', 'ML ROC curve'),
        ('submissions/chaos_round_stress_test.csv', 'Chaos round stress test'),
        ('charts/chaos_stress_test.png', 'Chaos round stress chart'),
        ('submissions/presentation.pptx', 'Presentation slides (PPTX)'),
        ('n8n/price_alert_workflow.json', 'n8n workflow JSON'),
        ('n8n/n8n_workflow_diagram.png', 'n8n workflow diagram'),
    ]
    
    all_ok = True
    for rel_path, description in deliverables:
        full_path = os.path.join(BASE_DIR, rel_path)
        exists = os.path.exists(full_path)
        if exists:
            size = os.path.getsize(full_path)
            size_str = f"{size/1024:.1f} KB" if size < 1048576 else f"{size/1048576:.1f} MB"
            print(f"  ✅ {description:45s}  ({size_str})")
        else:
            print(f"  ❌ {description:45s}  MISSING")
            all_ok = False
    
    print(f"\n{'─' * 70}")
    
    manual_items = [
        "Portfolio justification (200 words) — YOU must write this",
        "n8n live demo — Import JSON into n8n and run it live",
        "Export presentation.pptx → PDF for final submission",
        "Prepare judge Q&A answers using your computed metrics",
    ]
    
    print("\n⚠️  MANUAL ITEMS (cannot be automated):")
    for item in manual_items:
        print(f"  📌 {item}")
    
    return all_ok


if __name__ == '__main__':
    print("═" * 70)
    print("🚀 HackNova 2 — PortfolioIQ: FULL PIPELINE RUNNER")
    print("═" * 70)
    
    start_total = time.time()
    results = {}
    
    for script, desc in TASKS:
        success = run_task(script, desc)
        results[desc] = success
        if not success:
            print(f"\n⚠️  {desc} failed. Continuing with remaining tasks...")
    
    elapsed_total = time.time() - start_total
    
    # Summary
    print(f"\n\n{'═' * 70}")
    print("📊 PIPELINE SUMMARY")
    print(f"{'═' * 70}")
    
    for desc, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {desc}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\n  Result: {passed}/{total} tasks passed ({elapsed_total:.1f}s total)")
    
    # Check deliverables
    check_deliverables()
    
    print(f"\n{'═' * 70}")
    print("🏁 PIPELINE COMPLETE")
    print(f"{'═' * 70}")
