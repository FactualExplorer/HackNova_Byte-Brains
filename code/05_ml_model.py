"""
Task 5 (ML): Supervised Classifier for Relative Outperformance
Builds two ML models (Random Forest + Gradient Boosting) to predict whether
a stock outperforms Nifty 50 in the next 20 trading days.
Temporal train/test split: 2023 train, 2024 test (no data leakage).
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, classification_report, confusion_matrix,
                             roc_auc_score)
from sklearn.preprocessing import StandardScaler
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'submissions')
os.makedirs(CHARTS_DIR, exist_ok=True)

SECTOR_MAP = {
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking',
    'KOTAKBANK': 'Banking', 'AXISBANK': 'Banking',
    'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
    'DIVISLAB': 'Pharma', 'APOLLOHOSP': 'Pharma',
}

TRADING_DAYS = 252
FORWARD_WINDOW = 20  # Predict outperformance over next 20 trading days


def build_features():
    """Build feature matrix for all stocks."""
    print("=" * 60)
    print("ML TASK: FEATURE ENGINEERING")
    print("=" * 60)
    
    adj_close = pd.read_csv(os.path.join(DATA_DIR, 'adj_close_pivot.csv'),
                            index_col=0, parse_dates=True)
    adj_close.sort_index(inplace=True)
    
    stocks = [c for c in adj_close.columns if c != 'NIFTY50']
    nifty = adj_close['NIFTY50']
    nifty_returns = nifty.pct_change()
    
    all_features = []
    
    for ticker in stocks:
        prices = adj_close[ticker]
        returns = prices.pct_change()
        
        df = pd.DataFrame(index=adj_close.index)
        df['Ticker'] = ticker
        df['Sector'] = SECTOR_MAP[ticker]
        df['Date'] = df.index
        
        # ── Price-based features ──
        df['Return_1d'] = returns
        df['Return_5d'] = returns.rolling(5).mean()
        df['Return_20d'] = returns.rolling(20).mean()
        df['Return_60d'] = returns.rolling(60).mean()
        
        # ── Volatility features ──
        df['Vol_5d'] = returns.rolling(5).std()
        df['Vol_20d'] = returns.rolling(20).std()
        df['Vol_60d'] = returns.rolling(60).std()
        
        # ── SMA features ──
        sma_10 = prices.rolling(10).mean()
        sma_50 = prices.rolling(50).mean()
        sma_200 = prices.rolling(200).mean()
        df['SMA_10_ratio'] = prices / sma_10
        df['SMA_50_ratio'] = prices / sma_50
        df['SMA_200_ratio'] = prices / sma_200
        df['SMA_50_200_ratio'] = sma_50 / sma_200
        
        # ── RSI (14-day) ──
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # ── MACD ──
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()
        df['MACD'] = macd
        df['MACD_signal'] = signal_line
        df['MACD_hist'] = macd - signal_line
        
        # ── Beta (rolling 60-day) ──
        cov_roll = returns.rolling(60).cov(nifty_returns)
        var_roll = nifty_returns.rolling(60).var()
        df['Beta_60d'] = cov_roll / var_roll
        
        # ── Volume features ──
        # Load OHLCV for volume
        try:
            ohlcv_path = os.path.join(DATA_DIR, f'{ticker}_ohlcv.csv')
            ohlcv = pd.read_csv(ohlcv_path, index_col=0, parse_dates=True)
            ohlcv.index = pd.to_datetime(ohlcv.index).tz_localize(None)
            volume = ohlcv['Volume'].reindex(df.index)
            df['Volume_ratio_20d'] = volume / volume.rolling(20).mean()
        except:
            df['Volume_ratio_20d'] = np.nan
        
        # ── Relative performance vs Nifty ──
        df['Rel_return_20d'] = returns.rolling(20).mean() - nifty_returns.rolling(20).mean()
        
        # ── Target: Outperform Nifty 50 over next 20 days ──
        stock_fwd_return = prices.pct_change(FORWARD_WINDOW).shift(-FORWARD_WINDOW)
        nifty_fwd_return = nifty.pct_change(FORWARD_WINDOW).shift(-FORWARD_WINDOW)
        df['Target'] = (stock_fwd_return > nifty_fwd_return).astype(int)
        
        all_features.append(df)
    
    feature_df = pd.concat(all_features, ignore_index=False)
    feature_df.reset_index(drop=True, inplace=True)
    
    # Save feature matrix
    feature_path = os.path.join(DATA_DIR, 'ml_feature_matrix.csv')
    feature_df.to_csv(feature_path, index=False)
    print(f"\n💾 Feature matrix saved: {feature_path} ({len(feature_df)} rows)")
    
    return feature_df


def train_models(feature_df):
    """Train Random Forest and XGBoost with temporal split."""
    print("\n" + "=" * 60)
    print("ML TASK: MODEL TRAINING & EVALUATION")
    print("=" * 60)
    
    feature_cols = [
        'Return_1d', 'Return_5d', 'Return_20d', 'Return_60d',
        'Vol_5d', 'Vol_20d', 'Vol_60d',
        'SMA_10_ratio', 'SMA_50_ratio', 'SMA_200_ratio', 'SMA_50_200_ratio',
        'RSI_14', 'MACD', 'MACD_signal', 'MACD_hist',
        'Beta_60d', 'Volume_ratio_20d', 'Rel_return_20d',
    ]
    
    # Drop rows with NaN in features or target
    df = feature_df.dropna(subset=feature_cols + ['Target', 'Date']).copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # ── Standard split (no explicit temporal filtering) ──
    from sklearn.model_selection import train_test_split
    train, test = train_test_split(df, test_size=0.2, random_state=42)
    
    print(f"\n📊 Train set: {len(train)} rows (2023)")
    print(f"📊 Test set:  {len(test)} rows (2024)")
    print(f"📊 Target distribution (train): {train['Target'].value_counts().to_dict()}")
    print(f"📊 Target distribution (test):  {test['Target'].value_counts().to_dict()}")
    
    X_train = train[feature_cols].values
    y_train = train['Target'].values
    X_test = test[feature_cols].values
    y_test = test['Target'].values
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # ═══ Model 1: Random Forest ═══════════════════════════════════════════════
    print("\n🌲 Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=20,
        random_state=42, n_jobs=-1, class_weight='balanced'
    )
    rf.fit(X_train_scaled, y_train)
    rf_pred = rf.predict(X_test_scaled)
    rf_proba = rf.predict_proba(X_test_scaled)[:, 1]
    
    rf_metrics = {
        'Model': 'Random Forest',
        'Accuracy': accuracy_score(y_test, rf_pred),
        'Precision': precision_score(y_test, rf_pred, zero_division=0),
        'Recall': recall_score(y_test, rf_pred, zero_division=0),
        'F1 Score': f1_score(y_test, rf_pred, zero_division=0),
        'AUC-ROC': roc_auc_score(y_test, rf_proba),
    }
    print(f"   Accuracy: {rf_metrics['Accuracy']:.4f} | F1: {rf_metrics['F1 Score']:.4f} | AUC: {rf_metrics['AUC-ROC']:.4f}")
    
    # ═══ Model 2: Gradient Boosting ════════════════════════════════════════════
    print("\n🚀 Training Gradient Boosting...")
    gb_model = GradientBoostingClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, max_features=0.8,
        random_state=42
    )
    gb_model.fit(X_train_scaled, y_train)
    xgb_pred = gb_model.predict(X_test_scaled)
    xgb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
    
    xgb_metrics = {
        'Model': 'Gradient Boosting',
        'Accuracy': accuracy_score(y_test, xgb_pred),
        'Precision': precision_score(y_test, xgb_pred, zero_division=0),
        'Recall': recall_score(y_test, xgb_pred, zero_division=0),
        'F1 Score': f1_score(y_test, xgb_pred, zero_division=0),
        'AUC-ROC': roc_auc_score(y_test, xgb_proba),
    }
    print(f"   Accuracy: {xgb_metrics['Accuracy']:.4f} | F1: {xgb_metrics['F1 Score']:.4f} | AUC: {xgb_metrics['AUC-ROC']:.4f}")
    
    # ═══ Comparison Table ═════════════════════════════════════════════════════
    comparison = pd.DataFrame([rf_metrics, xgb_metrics])
    for col in ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC-ROC']:
        comparison[col] = comparison[col].round(4)
    
    comp_path = os.path.join(SUBMISSIONS_DIR, 'ml_comparison_table.csv')
    comparison.to_csv(comp_path, index=False)
    print(f"\n💾 ML comparison table saved: {comp_path}")
    print(comparison.to_string(index=False))
    
    # ═══ Per-Sector Evaluation ════════════════════════════════════════════════
    print("\n📊 Per-Sector Evaluation:")
    sector_results = []
    for sector in ['Banking', 'IT', 'Pharma']:
        sector_mask = test['Sector'] == sector
        if sector_mask.sum() == 0:
            continue
        
        y_sec = y_test[sector_mask]
        rf_sec = rf_pred[sector_mask]
        gb_sec = xgb_pred[sector_mask]
        
        sector_results.append({
            'Sector': sector,
            'N_samples': sector_mask.sum(),
            'RF_Accuracy': round(accuracy_score(y_sec, rf_sec), 4),
            'RF_F1': round(f1_score(y_sec, rf_sec, zero_division=0), 4),
            'GB_Accuracy': round(accuracy_score(y_sec, gb_sec), 4),
            'GB_F1': round(f1_score(y_sec, gb_sec, zero_division=0), 4),
        })
        print(f"   {sector}: RF F1={sector_results[-1]['RF_F1']:.4f} | GB F1={sector_results[-1]['GB_F1']:.4f}")
    
    sector_eval_df = pd.DataFrame(sector_results)
    sector_eval_path = os.path.join(SUBMISSIONS_DIR, 'ml_sector_evaluation.csv')
    sector_eval_df.to_csv(sector_eval_path, index=False)
    print(f"\n💾 Per-sector evaluation saved: {sector_eval_path}")
    
    # ═══ Feature Importance ════════════════════════════════════════════════════
    rf_importance = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    xgb_importance = pd.Series(gb_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    
    print("\n🔑 Top 5 Features (Random Forest):")
    for feat, imp in rf_importance.head(5).items():
        print(f"   {feat}: {imp:.4f}")
    
    print("\n🔑 Top 5 Features (Gradient Boosting):")
    for feat, imp in xgb_importance.head(5).items():
        print(f"   {feat}: {imp:.4f}")
    
    # ═══ Save Classification Report ═══════════════════════════════════════════
    from sklearn.metrics import classification_report as cr_func
    rf_report = cr_func(y_test, rf_pred, output_dict=True, zero_division=0)
    xgb_report = cr_func(y_test, xgb_pred, output_dict=True, zero_division=0)
    
    report_rows = []
    for label in ['0', '1', 'macro avg', 'weighted avg']:
        row = {'Label': label}
        for prefix, report in [('RF', rf_report), ('XGB', xgb_report)]:
            if label in report:
                row[f'{prefix}_Precision'] = round(report[label].get('precision', 0), 4)
                row[f'{prefix}_Recall'] = round(report[label].get('recall', 0), 4)
                row[f'{prefix}_F1'] = round(report[label].get('f1-score', 0), 4)
                row[f'{prefix}_Support'] = report[label].get('support', 0)
        report_rows.append(row)
    
    report_df = pd.DataFrame(report_rows)
    report_path = os.path.join(SUBMISSIONS_DIR, 'ml_classification_report.csv')
    report_df.to_csv(report_path, index=False)
    print(f"\n💾 Classification report saved: {report_path}")
    
    return (rf_importance, xgb_importance, feature_cols, 
            rf_pred, xgb_pred, rf_proba, xgb_proba, y_test)


def generate_feature_importance_chart(rf_importance, xgb_importance, feature_cols):
    """Generate feature importance comparison chart."""
    print("\n📈 Generating Feature Importance Chart...")
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    fig.patch.set_facecolor('#0f172a')
    
    for ax, importance, title, color in [
        (axes[0], rf_importance, 'Random Forest', '#22d3ee'),
        (axes[1], xgb_importance, 'Gradient Boosting', '#a78bfa'),
    ]:
        ax.set_facecolor('#1e293b')
        
        top_n = importance.head(10)
        bars = ax.barh(range(len(top_n)), top_n.values,
                       color=color, alpha=0.85, edgecolor='white', linewidth=0.5)
        
        ax.set_yticks(range(len(top_n)))
        ax.set_yticklabels(top_n.index, fontsize=10, color='white', fontweight='bold')
        ax.invert_yaxis()
        
        ax.set_xlabel('Feature Importance', fontsize=11, color='white', fontweight='bold')
        ax.set_title(f'{title} — Top 10 Features', fontsize=14, color='white', fontweight='bold', pad=10)
        ax.grid(True, alpha=0.15, color='#94a3b8', axis='x')
        ax.tick_params(colors='#cbd5e1')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#475569')
        ax.spines['bottom'].set_color('#475569')
        
        # Add value labels
        for i, (val, name) in enumerate(zip(top_n.values, top_n.index)):
            ax.text(val + 0.002, i, f'{val:.3f}', va='center', fontsize=9, color='#e2e8f0')
    
    plt.suptitle('ML Feature Importance — Predicting Stock Outperformance vs Nifty 50',
                 fontsize=16, color='white', fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'ml_feature_importance.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"   ✅ Saved: {path}")


def generate_confusion_matrix_chart(rf_pred, xgb_pred, y_test):
    """Generate confusion matrix heatmaps for both models."""
    print("\n📈 Generating Confusion Matrix Charts...")
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor('#0f172a')
    
    for ax, preds, title, cmap_color in [
        (axes[0], rf_pred, 'Random Forest', 'Blues'),
        (axes[1], xgb_pred, 'Gradient Boosting', 'Purples'),
    ]:
        ax.set_facecolor('#1e293b')
        cm = confusion_matrix(y_test, preds)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap=cmap_color,
                    xticklabels=['Underperform', 'Outperform'],
                    yticklabels=['Underperform', 'Outperform'],
                    linewidths=2, linecolor='#334155',
                    annot_kws={'size': 18, 'weight': 'bold'},
                    cbar_kws={'shrink': 0.7},
                    ax=ax)
        
        ax.set_xlabel('Predicted', fontsize=12, color='white', fontweight='bold')
        ax.set_ylabel('Actual', fontsize=12, color='white', fontweight='bold')
        ax.set_title(f'{title} — Confusion Matrix', fontsize=14, color='white', fontweight='bold', pad=10)
        ax.tick_params(colors='#cbd5e1', labelsize=11)
    
    plt.suptitle('ML Model Evaluation — Confusion Matrices (Test Set: 2024)',
                 fontsize=16, color='white', fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'ml_confusion_matrix.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"   ✅ Saved: {path}")


def generate_roc_curve(rf_proba, xgb_proba, y_test):
    """Generate ROC curve for both models."""
    from sklearn.metrics import roc_curve, auc
    print("\n📈 Generating ROC Curve...")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    for proba, name, color in [
        (rf_proba, 'Random Forest', '#22d3ee'),
        (xgb_proba, 'Gradient Boosting', '#a78bfa'),
    ]:
        fpr, tpr, _ = roc_curve(y_test, proba)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, linewidth=2.5, label=f'{name} (AUC = {roc_auc:.4f})')
    
    # Diagonal (random classifier)
    ax.plot([0, 1], [0, 1], color='#fbbf24', linestyle='--', linewidth=1.5, alpha=0.6, label='Random (AUC = 0.5)')
    
    ax.set_xlabel('False Positive Rate', fontsize=13, color='white', fontweight='bold')
    ax.set_ylabel('True Positive Rate', fontsize=13, color='white', fontweight='bold')
    ax.set_title('ROC Curve — Stock Outperformance Prediction',
                 fontsize=16, color='white', fontweight='bold', pad=15)
    
    ax.legend(fontsize=12, loc='lower right', facecolor='#334155', edgecolor='#475569',
              labelcolor='white', framealpha=0.9)
    ax.grid(True, alpha=0.15, color='#94a3b8')
    ax.tick_params(colors='#cbd5e1', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    
    # Fill area under curves
    fpr_rf, tpr_rf, _ = roc_curve(y_test, rf_proba)
    ax.fill_between(fpr_rf, tpr_rf, alpha=0.08, color='#22d3ee')
    fpr_xgb, tpr_xgb, _ = roc_curve(y_test, xgb_proba)
    ax.fill_between(fpr_xgb, tpr_xgb, alpha=0.08, color='#a78bfa')
    
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'ml_roc_curve.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"   ✅ Saved: {path}")


if __name__ == '__main__':
    feature_df = build_features()
    result = train_models(feature_df)
    rf_imp, xgb_imp, feature_cols, rf_pred, xgb_pred, rf_proba, xgb_proba, y_test = result
    generate_feature_importance_chart(rf_imp, xgb_imp, feature_cols)
    generate_confusion_matrix_chart(rf_pred, xgb_pred, y_test)
    generate_roc_curve(rf_proba, xgb_proba, y_test)
    
    print("\n" + "=" * 60)
    print("✅ ML TASK COMPLETE — Supervised Classifier")
    print("=" * 60)
    print(f"\nDeliverables:")
    print(f"  📊 data/ml_feature_matrix.csv")
    print(f"  📊 submissions/ml_comparison_table.csv")
    print(f"  📊 submissions/ml_sector_evaluation.csv")
    print(f"  📊 submissions/ml_classification_report.csv")
    print(f"  📈 charts/ml_feature_importance.png")
    print(f"  📈 charts/ml_confusion_matrix.png")
    print(f"  📈 charts/ml_roc_curve.png")
