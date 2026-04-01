# HackNova 1.0 — PortfolioIQ Submission
## Team: [Byte Brains]
## Date: 01 April 2026

## Project Structure

### datasets/
- `raw_dataset.csv` — Raw OHLCV data for 15 NSE stocks + Nifty 50 (Jan 2023 – Dec 2024)
- `cleaned_dataset.csv` — Cleaned and validated dataset
- `adj_close_pivot.csv` — Adjusted close prices in pivot format

### metrics/
- `metrics_summary.csv` — All 6 metrics for 15 stocks (Return, Volatility, Sharpe, Beta, Max DD, SMA)
- `metrics_summary.xlsx` — Excel version

### sma/
- `sma_signal_table.csv` — Golden Cross / Death Cross signal table

### portfolio/
- `portfolio_comparison.csv` — Portfolio A (Equal) vs Portfolio B (Optimized)
- `portfolio_allocations.csv` — Per-stock allocation in Rs.
- `sector_breakdown.csv` — Average Sharpe and Beta per sector

### ml_model/
- `ml_feature_matrix.csv` — 18-feature matrix for all stocks
- `ml_comparison_table.csv` — Random Forest vs XGBoost comparison
- `ml_sector_evaluation.csv` — Per-sector model evaluation
- `ml_classification_report.csv` — Detailed classification metrics

### charts/
- All visualizations at 200 DPI (Risk-Return scatter, Correlation heatmap, SMA overlays, etc.)

### n8n/
- `price_alert_workflow.json` — Import into n8n for live demo
- `n8n_workflow_diagram.png` — Workflow canvas visualization

### presentation/
- `presentation.pptx` — 7-slide deck (export to PDF for submission)

### code/
- All Python scripts (run `python run_all.py` to reproduce all results)

## How to Reproduce
```bash
pip install -r code/requirements.txt
python code/run_all.py
```

## Tools Used
- Python 3.x (pandas, numpy, matplotlib, seaborn, scikit-learn, xgboost)
- n8n (workflow automation)
- Yahoo Finance (yfinance) for data acquisition
