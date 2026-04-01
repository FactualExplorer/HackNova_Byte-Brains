"""
Task 6 (Chaos Round): Stress Test
Scenario: Nifty 50 drops 10% in a single week.
Uses Beta to estimate expected loss per stock, Portfolio A, and Portfolio B.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'submissions')
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

NIFTY_DROP = -0.10  # 10% drop scenario

SECTOR_MAP = {
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking',
    'KOTAKBANK': 'Banking', 'AXISBANK': 'Banking',
    'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
    'DIVISLAB': 'Pharma', 'APOLLOHOSP': 'Pharma',
}

SECTOR_COLORS = {
    'Banking': '#2563eb',
    'IT': '#16a34a',
    'Pharma': '#dc2626',
    'Portfolio': '#22d3ee',
}


def run_stress_test():
    """Run Chaos Round stress test."""
    print("=" * 60)
    print("CHAOS ROUND: STRESS TEST")
    print(f"Scenario: Nifty 50 drops {abs(NIFTY_DROP)*100:.0f}% in one week")
    print("=" * 60)
    
    # Load metrics
    metrics = pd.read_csv(os.path.join(SUBMISSIONS_DIR, 'metrics_summary.csv'))
    
    # Load portfolio allocations
    alloc = pd.read_csv(os.path.join(SUBMISSIONS_DIR, 'portfolio_allocations.csv'))
    
    # ── Per-stock expected loss ──
    stress_results = []
    for _, row in metrics.iterrows():
        ticker = row['Ticker']
        beta = row['Beta vs Nifty 50']
        expected_loss = beta * NIFTY_DROP * 100  # as percentage
        
        stress_results.append({
            'Ticker': ticker,
            'Sector': row['Sector'],
            'Beta': round(beta, 4),
            'Expected Loss (%)': round(expected_loss, 2),
        })
        
        print(f"  {ticker:12s} | Beta: {beta:6.4f} | Expected Loss: {expected_loss:7.2f}%")
    
    stress_df = pd.DataFrame(stress_results)
    
    # ── Most exposed & safest refuge ──
    most_exposed_idx = stress_df['Expected Loss (%)'].idxmin()
    safest_idx = stress_df['Expected Loss (%)'].idxmax()
    most_exposed = stress_df.loc[most_exposed_idx]
    safest = stress_df.loc[safest_idx]
    
    print(f"\n  🔴 Most Exposed: {most_exposed['Ticker']} (Beta: {most_exposed['Beta']:.4f}, Expected Loss: {most_exposed['Expected Loss (%)']:.2f}%)")
    print(f"  🟢 Safest Refuge: {safest['Ticker']} (Beta: {safest['Beta']:.4f}, Expected Loss: {safest['Expected Loss (%)']:.2f}%)")
    
    # ── Portfolio-level stress ──
    print("\n  📊 Portfolio Stress Test:")
    
    # Portfolio A (equal weight)
    weights_a = alloc.set_index('Ticker')['Portfolio A Weight (%)'].to_dict()
    port_a_loss = sum(
        (weights_a.get(r['Ticker'], 0) / 100) * r['Expected Loss (%)']
        for _, r in stress_df.iterrows()
    )
    
    # Portfolio B
    weights_b = alloc.set_index('Ticker')['Portfolio B Weight (%)'].to_dict()
    port_b_loss = sum(
        (weights_b.get(r['Ticker'], 0) / 100) * r['Expected Loss (%)']
        for _, r in stress_df.iterrows()
    )
    
    print(f"     Portfolio A Expected Loss: {port_a_loss:.2f}%")
    print(f"     Portfolio B Expected Loss: {port_b_loss:.2f}%")
    
    # Save clean stress results (stocks only) for chart
    stock_stress = stress_df.copy()
    
    # Add portfolio rows to export
    stress_export = pd.concat([stress_df, pd.DataFrame([
        {'Ticker': 'PORTFOLIO A', 'Sector': 'Portfolio', 'Beta': '-', 'Expected Loss (%)': round(port_a_loss, 2)},
        {'Ticker': 'PORTFOLIO B', 'Sector': 'Portfolio', 'Beta': '-', 'Expected Loss (%)': round(port_b_loss, 2)},
        {'Ticker': '', 'Sector': '', 'Beta': '', 'Expected Loss (%)': ''},
        {'Ticker': 'MOST EXPOSED', 'Sector': most_exposed['Sector'], 'Beta': most_exposed['Beta'], 'Expected Loss (%)': most_exposed['Expected Loss (%)']},
        {'Ticker': f"  → {most_exposed['Ticker']}", 'Sector': '', 'Beta': '', 'Expected Loss (%)': ''},
        {'Ticker': 'SAFEST REFUGE', 'Sector': safest['Sector'], 'Beta': safest['Beta'], 'Expected Loss (%)': safest['Expected Loss (%)']},
        {'Ticker': f"  → {safest['Ticker']}", 'Sector': '', 'Beta': '', 'Expected Loss (%)': ''},
    ])], ignore_index=True)
    
    # Save
    stress_path = os.path.join(SUBMISSIONS_DIR, 'chaos_round_stress_test.csv')
    stress_export.to_csv(stress_path, index=False)
    print(f"\n💾 Stress test saved: {stress_path}")
    
    return stock_stress, port_a_loss, port_b_loss, most_exposed, safest


def generate_stress_chart(stock_stress, port_a_loss, port_b_loss, most_exposed, safest):
    """Generate stress test bar chart."""
    print("\n📈 Generating Chaos Round Stress Chart...")
    
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    # Sort by expected loss (most negative = most exposed at top)
    df = stock_stress.sort_values('Expected Loss (%)', ascending=True).reset_index(drop=True)
    
    # Add portfolio bars
    port_data = pd.DataFrame([
        {'Ticker': 'Port A (Equal)', 'Sector': 'Portfolio', 'Expected Loss (%)': round(port_a_loss, 2)},
        {'Ticker': 'Port B (Optimized)', 'Sector': 'Portfolio', 'Expected Loss (%)': round(port_b_loss, 2)},
    ])
    df = pd.concat([df, port_data], ignore_index=True)
    
    # Colors
    colors = []
    for _, row in df.iterrows():
        colors.append(SECTOR_COLORS.get(row['Sector'], '#8b5cf6'))
    
    # Bar chart
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df['Expected Loss (%)'], color=colors, alpha=0.85,
                   edgecolor='white', linewidth=0.5, height=0.7)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['Ticker'], fontsize=10, color='white', fontweight='bold')
    
    # Add value labels
    for i, (val, ticker) in enumerate(zip(df['Expected Loss (%)'], df['Ticker'])):
        ax.text(val - 0.3, i, f'{val:.2f}%', va='center', ha='right',
                fontsize=9, fontweight='bold', color='white')
    
    # Highlight most exposed and safest
    most_exposed_idx = df[df['Ticker'] == most_exposed['Ticker']].index
    safest_idx = df[df['Ticker'] == safest['Ticker']].index
    
    if len(most_exposed_idx) > 0:
        bars[most_exposed_idx[0]].set_edgecolor('#ef4444')
        bars[most_exposed_idx[0]].set_linewidth(3)
        ax.annotate('🔴 MOST EXPOSED', (df.loc[most_exposed_idx[0], 'Expected Loss (%)'], most_exposed_idx[0]),
                    textcoords="offset points", xytext=(-80, 15),
                    fontsize=10, fontweight='bold', color='#ef4444',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#ef4444', alpha=0.9))
    
    if len(safest_idx) > 0:
        bars[safest_idx[0]].set_edgecolor('#22c55e')
        bars[safest_idx[0]].set_linewidth(3)
        ax.annotate('🟢 SAFEST REFUGE', (df.loc[safest_idx[0], 'Expected Loss (%)'], safest_idx[0]),
                    textcoords="offset points", xytext=(-80, -15),
                    fontsize=10, fontweight='bold', color='#22c55e',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#22c55e', alpha=0.9))
    
    # Add a vertical line at Nifty drop
    ax.axvline(x=NIFTY_DROP * 100, color='#fbbf24', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Nifty 50 Drop ({NIFTY_DROP*100:.0f}%)')
    
    ax.set_xlabel('Expected Loss (%)', fontsize=13, color='white', fontweight='bold')
    ax.set_title('⚡ Chaos Round — Stress Test: Nifty 50 Drops 10%\nExpected Impact by Stock & Portfolio',
                 fontsize=16, color='white', fontweight='bold', pad=15)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2563eb', label='Banking'),
        Patch(facecolor='#16a34a', label='IT'),
        Patch(facecolor='#dc2626', label='Pharma'),
        Patch(facecolor='#22d3ee', label='Portfolio'),
    ]
    ax.legend(handles=legend_elements, fontsize=10, loc='lower left',
              facecolor='#334155', edgecolor='#475569', labelcolor='white', framealpha=0.9)
    
    ax.grid(True, alpha=0.15, color='#94a3b8', axis='x')
    ax.tick_params(colors='#cbd5e1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'chaos_stress_test.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"   ✅ Saved: {path}")


if __name__ == '__main__':
    stock_stress, port_a_loss, port_b_loss, most_exposed, safest = run_stress_test()
    generate_stress_chart(stock_stress, port_a_loss, port_b_loss, most_exposed, safest)
    
    print("\n" + "=" * 60)
    print("✅ CHAOS ROUND COMPLETE — Stress Test")
    print("=" * 60)
    print(f"\nDeliverables:")
    print(f"  📊 submissions/chaos_round_stress_test.csv")
    print(f"  📈 charts/chaos_stress_test.png")
    print(f"\n⚠️  Remember: You must defend WHY certain stocks are 'safe' or 'exposed'")
    print(f"    during the judge Q&A. The math is here — the judgment is yours.")
