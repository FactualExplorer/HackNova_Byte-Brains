import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
import textwrap

BASE_DIR = '/Users/abdullah/Desktop/Hacknova'
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
SUB_DIR = os.path.join(BASE_DIR, 'submissions')

comp_df = pd.read_csv(os.path.join(SUB_DIR, 'ml_comparison_table.csv'))
fig, ax = plt.subplots(figsize=(10, 3))
fig.patch.set_facecolor('white')
ax.axis('tight')
ax.axis('off')
table = ax.table(cellText=comp_df.values, colLabels=comp_df.columns, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.5)
plt.title('ML Model Comparison - Predicting Stock Outperformance', fontsize=14, pad=20)
plt.savefig(os.path.join(CHARTS_DIR, 'model_comparison_table.png'), dpi=300, bbox_inches='tight')
plt.close()

feat_df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'ml_feature_matrix.csv'))
cols = ['Return_1d', 'Return_5d', 'Return_20d', 'Return_60d', 'Vol_5d', 'Vol_20d', 'Vol_60d',
        'SMA_10_ratio', 'SMA_50_ratio', 'SMA_200_ratio', 'SMA_50_200_ratio',
        'RSI_14', 'MACD', 'MACD_signal', 'MACD_hist', 'Beta_60d', 'Volume_ratio_20d', 'Rel_return_20d']
df = feat_df.dropna(subset=cols + ['Target']).copy()
X = df[cols].values
y = df['Target'].values

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
importances = pd.Series(rf.feature_importances_, index=cols).sort_values(ascending=False).head(3)

fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor('white')
ax.barh(importances.index[::-1], importances.values[::-1], color='#6366f1', edgecolor='black')
ax.set_title("Top 3 Predictive Features", fontsize=14, fontweight='bold')
ax.set_xlabel("Relative Importance")
for i, v in enumerate(importances.values[::-1]):
    ax.text(v + 0.002, i, f"{v:.3f}", va='center')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, 'top_3_features.png'), dpi=300, bbox_inches='tight')
plt.close()

text = (
    "Portfolio Recommendation & Chaos Round Justification\n\n"
    "Based on the dual-model machine learning analytics derived from our recent optimizations, the core predictive "
    "features strongly suggest prioritizing Relative Return and market momentum. In building our recommended "
    "portfolio architecture, we have rigorously accounted for the adversarial conditions highlighted in the Chaos Round.\n\n"
    "The stress-test scenario simulates a severe 10% market correction. Specifically, we observed that high-beta "
    "banking stocks such as SBIN faced catastrophic drawdowns reaching nearly 14%. Conversely, the pharmaceutical sector "
    "acted as an essential safe haven, with defensive assets like CIPLA limiting losses to just 3.32%.\n\n"
    "Our final recommendation emphatically shifts capital allocation toward 'Portfolio B'. By overweighting defensively "
    "structured, lower-beta assets in the IT and Pharma sectors, Portfolio B achieves a vastly superior risk-adjusted "
    "drawdown of just 5.99%, compared to the riskier 7.97% experienced by Portfolio A. This defensive pivot simultaneously "
    "captures the outperformance signals flagged by the machine learning algorithm (which targets high relative returns), "
    "while shielding the principle against extreme volatility spikes identified in the stress test."
)

wrapped_text = ""
for paragraph in text.split('\n\n'):
    wrapped_text += textwrap.fill(paragraph, width=85) + "\n\n"

fig = plt.figure(figsize=(8.5, 11))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0,0,1,1])
ax.axis('off')
ax.text(0.1, 0.9, wrapped_text, fontsize=12, family='sans-serif', va='top', ha='left', transform=ax.transAxes)
plt.savefig(os.path.join(SUB_DIR, 'Portfolio_Justification.pdf'), dpi=300, bbox_inches='tight')
plt.close()

print("Assets generated successfully!")
