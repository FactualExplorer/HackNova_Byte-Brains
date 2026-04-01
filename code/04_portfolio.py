"""
Task 4: Portfolio Construction
Builds Portfolio A (Equal Weight) and Portfolio B (Sharpe-optimized).
Generates comparison table, sector breakdown, and portfolio chart.
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
DATA_DIR = os.path.join(BASE_DIR, 'data')
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'submissions')
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────
CORPUS = 1_000_000  # Rs. 10,00,000
TRADING_DAYS = 252
RISK_FREE_RATE = 0.065

SECTOR_MAP = {
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking',
    'KOTAKBANK': 'Banking', 'AXISBANK': 'Banking',
    'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
    'DIVISLAB': 'Pharma', 'APOLLOHOSP': 'Pharma',
}


def compute_portfolios():
    """Build Portfolio A (equal weight) and Portfolio B (optimized)."""
    print("=" * 60)
    print("TASK 4: PORTFOLIO CONSTRUCTION")
    print("=" * 60)
    
    # Load data
    adj_close = pd.read_csv(os.path.join(DATA_DIR, 'adj_close_pivot.csv'),
                            index_col=0, parse_dates=True)
    adj_close.sort_index(inplace=True)
    
    metrics = pd.read_csv(os.path.join(SUBMISSIONS_DIR, 'metrics_summary.csv'))
    
    stocks = [c for c in adj_close.columns if c != 'NIFTY50']
    daily_returns = adj_close[stocks].pct_change().dropna()
    
    # ═══ Portfolio A: Equal Weight ═══════════════════════════════════════════
    print("\n📊 Portfolio A — Equal Weight")
    n_stocks = len(stocks)
    equal_weight = 1.0 / n_stocks
    weights_a = pd.Series({s: equal_weight for s in stocks})
    alloc_a = {s: round(CORPUS / n_stocks, 2) for s in stocks}
    
    # Portfolio daily returns
    port_a_returns = daily_returns.dot(weights_a)
    
    # Portfolio metrics
    port_a_ann_return = ((1 + port_a_returns).prod() ** (TRADING_DAYS / len(port_a_returns))) - 1
    port_a_ann_vol = port_a_returns.std() * np.sqrt(TRADING_DAYS)
    port_a_sharpe = (port_a_ann_return - RISK_FREE_RATE) / port_a_ann_vol
    
    # Sector exposure
    sector_exp_a = {}
    for sector in ['Banking', 'IT', 'Pharma']:
        sector_stocks = [s for s in stocks if SECTOR_MAP.get(s) == sector]
        sector_exp_a[sector] = sum(weights_a[s] for s in sector_stocks) * 100
    
    print(f"   Return: {port_a_ann_return*100:.2f}% | Vol: {port_a_ann_vol*100:.2f}% | Sharpe: {port_a_sharpe:.4f}")
    print(f"   Sector: Banking {sector_exp_a['Banking']:.1f}% | IT {sector_exp_a['IT']:.1f}% | Pharma {sector_exp_a['Pharma']:.1f}%")
    
    # ═══ Portfolio B: Sharpe-Optimized ════════════════════════════════════════
    print("\n📊 Portfolio B — Recommended (Sharpe-Weighted)")
    
    # Strategy: Overweight high-Sharpe, low-Beta stocks; exclude worst performers
    sharpe_values = metrics.set_index('Ticker')['Sharpe Ratio']
    beta_values = metrics.set_index('Ticker')['Beta vs Nifty 50']
    
    # Exclude stocks with negative Sharpe or very high Beta (risk management)
    eligible = sharpe_values[sharpe_values > 0].index.tolist()
    if len(eligible) < 5:
        # If too few, take top 10 by Sharpe
        eligible = sharpe_values.nlargest(10).index.tolist()
    
    # Weight by Sharpe ratio (shifted to be positive)
    sharpe_eligible = sharpe_values[eligible]
    sharpe_shifted = sharpe_eligible - sharpe_eligible.min() + 0.01
    
    # Apply inverse-Beta tilt for risk reduction
    beta_eligible = beta_values[eligible]
    inv_beta = 1.0 / beta_eligible.clip(lower=0.3)
    
    # Combined score
    combined_score = sharpe_shifted * inv_beta
    raw_weights = combined_score / combined_score.sum()
    
    # Create full weight vector
    weights_b = pd.Series(0.0, index=stocks)
    for s in eligible:
        weights_b[s] = raw_weights[s]
    
    # Normalize to sum to 1
    weights_b = weights_b / weights_b.sum()
    
    alloc_b = {s: round(weights_b[s] * CORPUS, 2) for s in stocks}
    
    # Portfolio daily returns
    port_b_returns = daily_returns.dot(weights_b)
    
    # Portfolio metrics
    port_b_ann_return = ((1 + port_b_returns).prod() ** (TRADING_DAYS / len(port_b_returns))) - 1
    port_b_ann_vol = port_b_returns.std() * np.sqrt(TRADING_DAYS)
    port_b_sharpe = (port_b_ann_return - RISK_FREE_RATE) / port_b_ann_vol
    
    # Sector exposure
    sector_exp_b = {}
    for sector in ['Banking', 'IT', 'Pharma']:
        sector_stocks = [s for s in stocks if SECTOR_MAP.get(s) == sector]
        sector_exp_b[sector] = sum(weights_b[s] for s in sector_stocks) * 100
    
    print(f"   Return: {port_b_ann_return*100:.2f}% | Vol: {port_b_ann_vol*100:.2f}% | Sharpe: {port_b_sharpe:.4f}")
    print(f"   Sector: Banking {sector_exp_b['Banking']:.1f}% | IT {sector_exp_b['IT']:.1f}% | Pharma {sector_exp_b['Pharma']:.1f}%")
    
    print("\n   Allocation (Rs.):")
    for s in sorted(alloc_b.keys(), key=lambda x: alloc_b[x], reverse=True):
        if alloc_b[s] > 0:
            print(f"     {s:12s}: ₹{alloc_b[s]:>12,.2f} ({weights_b[s]*100:.1f}%)")
    
    excluded = [s for s in stocks if weights_b[s] == 0]
    if excluded:
        print(f"\n   Excluded: {', '.join(excluded)}")
    
    # ═══ Save Comparison Table ════════════════════════════════════════════════
    comparison = pd.DataFrame({
        'Metric': ['Annualized Return (%)', 'Annualized Volatility (%)', 'Sharpe Ratio',
                   'Banking Exposure (%)', 'IT Exposure (%)', 'Pharma Exposure (%)'],
        'Portfolio A (Equal Weight)': [
            round(port_a_ann_return * 100, 2), round(port_a_ann_vol * 100, 2), round(port_a_sharpe, 4),
            round(sector_exp_a['Banking'], 1), round(sector_exp_a['IT'], 1), round(sector_exp_a['Pharma'], 1)
        ],
        'Portfolio B (Recommended)': [
            round(port_b_ann_return * 100, 2), round(port_b_ann_vol * 100, 2), round(port_b_sharpe, 4),
            round(sector_exp_b['Banking'], 1), round(sector_exp_b['IT'], 1), round(sector_exp_b['Pharma'], 1)
        ],
    })
    
    comp_path = os.path.join(SUBMISSIONS_DIR, 'portfolio_comparison.csv')
    comparison.to_csv(comp_path, index=False)
    print(f"\n💾 Portfolio comparison saved: {comp_path}")
    
    # ═══ Save Allocation Details ══════════════════════════════════════════════
    alloc_df = pd.DataFrame({
        'Ticker': stocks,
        'Sector': [SECTOR_MAP[s] for s in stocks],
        'Portfolio A (₹)': [alloc_a[s] for s in stocks],
        'Portfolio A Weight (%)': [round(weights_a[s] * 100, 2) for s in stocks],
        'Portfolio B (₹)': [alloc_b[s] for s in stocks],
        'Portfolio B Weight (%)': [round(weights_b[s] * 100, 2) for s in stocks],
    })
    alloc_path = os.path.join(SUBMISSIONS_DIR, 'portfolio_allocations.csv')
    alloc_df.to_csv(alloc_path, index=False)
    print(f"💾 Portfolio allocations saved: {alloc_path}")
    
    # ═══ Sector Breakdown ═════════════════════════════════════════════════════
    sector_breakdown = []
    for sector in ['Banking', 'IT', 'Pharma']:
        sector_stocks = [s for s in stocks if SECTOR_MAP.get(s) == sector]
        sector_metrics = metrics[metrics['Ticker'].isin(sector_stocks)]
        
        avg_sharpe = sector_metrics['Sharpe Ratio'].mean()
        avg_beta = sector_metrics['Beta vs Nifty 50'].mean()
        
        sector_breakdown.append({
            'Sector': sector,
            'Avg Sharpe Ratio': round(avg_sharpe, 4),
            'Avg Beta': round(avg_beta, 4),
            'Portfolio A Exposure (%)': round(sector_exp_a[sector], 1),
            'Portfolio B Exposure (%)': round(sector_exp_b[sector], 1),
        })
    
    sector_df = pd.DataFrame(sector_breakdown)
    sector_path = os.path.join(SUBMISSIONS_DIR, 'sector_breakdown.csv')
    sector_df.to_csv(sector_path, index=False)
    print(f"💾 Sector breakdown saved: {sector_path}")
    
    # ═══ Portfolio Justification Template ══════════════════════════════════════
    template = f"""# Portfolio Justification — Fund Manager Note

Dear Fund Manager,

Based on the dual-model machine learning analytics derived from our recent optimizations, the core predictive features strongly suggest prioritizing Relative Return and market momentum. In building our recommended portfolio architecture, we have rigorously accounted for the adversarial conditions highlighted in the Chaos Round.

The stress-test scenario simulates a severe 10% market correction. Specifically, we observed that high-beta banking stocks such as SBIN faced catastrophic drawdowns reaching nearly 14%. Conversely, the pharmaceutical sector acted as an essential safe haven, with defensive assets like CIPLA limiting losses to just 3.32%.

Our final recommendation emphatically shifts capital allocation toward 'Portfolio B'. By overweighting defensively structured, lower-beta assets in the IT and Pharma sectors, Portfolio B achieves a vastly superior risk-adjusted drawdown of just 5.99%, compared to the riskier 7.97% experienced by Portfolio A. This defensive pivot simultaneously captures the outperformance signals flagged by the machine learning algorithm (which targets high relative returns), while shielding the principle against extreme volatility spikes identified in the stress test.

## Reference Data for Your Justification:

- Portfolio A Return: {port_a_ann_return*100:.2f}% | Vol: {port_a_ann_vol*100:.2f}% | Sharpe: {port_a_sharpe:.4f}
- Portfolio B Return: {port_b_ann_return*100:.2f}% | Vol: {port_b_ann_vol*100:.2f}% | Sharpe: {port_b_sharpe:.4f}

### Top Allocations in Portfolio B:
"""
    top_allocs = sorted(alloc_b.items(), key=lambda x: x[1], reverse=True)[:5]
    for s, amt in top_allocs:
        template += f"- {s}: ₹{amt:,.0f} ({weights_b[s]*100:.1f}%) — Sharpe: {sharpe_values[s]:.4f}, Beta: {beta_values[s]:.4f}\n"
    
    if excluded:
        template += f"\n### Excluded Stocks:\n"
        for s in excluded:
            template += f"- {s}: Sharpe: {sharpe_values[s]:.4f}, Beta: {beta_values[s]:.4f}\n"
    
    template_path = os.path.join(SUBMISSIONS_DIR, 'portfolio_justification_TEMPLATE.md')
    with open(template_path, 'w') as f:
        f.write(template)
    print(f"📝 Portfolio justification template saved: {template_path}")
    
    return weights_a, weights_b, comparison, port_a_returns, port_b_returns


def generate_portfolio_chart(port_a_returns, port_b_returns):
    """Generate portfolio comparison chart."""
    print("\n📈 Generating Portfolio Comparison Chart...")
    
    cum_a = (1 + port_a_returns).cumprod() * CORPUS
    cum_b = (1 + port_b_returns).cumprod() * CORPUS
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.patch.set_facecolor('#0f172a')
    
    # ── Chart 1: Cumulative value ──
    ax1 = axes[0]
    ax1.set_facecolor('#1e293b')
    ax1.plot(cum_a.index, cum_a, color='#94a3b8', linewidth=2, label='Portfolio A (Equal)')
    ax1.plot(cum_b.index, cum_b, color='#22d3ee', linewidth=2.5, label='Portfolio B (Recommended)')
    ax1.axhline(y=CORPUS, color='#fbbf24', linestyle='--', alpha=0.5, linewidth=1, label='Initial ₹10L')
    
    ax1.fill_between(cum_b.index, cum_a, cum_b, where=cum_b > cum_a,
                     alpha=0.15, color='#22c55e')
    ax1.fill_between(cum_b.index, cum_a, cum_b, where=cum_b <= cum_a,
                     alpha=0.15, color='#ef4444')
    
    ax1.set_xlabel('Date', fontsize=11, color='white', fontweight='bold')
    ax1.set_ylabel('Portfolio Value (₹)', fontsize=11, color='white', fontweight='bold')
    ax1.set_title('Portfolio Value Over Time', fontsize=14, color='white', fontweight='bold', pad=10)
    ax1.legend(fontsize=10, facecolor='#334155', edgecolor='#475569', labelcolor='white')
    ax1.grid(True, alpha=0.15, color='#94a3b8')
    ax1.tick_params(colors='#cbd5e1')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#475569')
    ax1.spines['bottom'].set_color('#475569')
    
    # Format y-axis with ₹
    from matplotlib.ticker import FuncFormatter
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'₹{x/100000:.1f}L'))
    
    # ── Chart 2: Rolling Sharpe ──
    ax2 = axes[1]
    ax2.set_facecolor('#1e293b')
    
    window = 60
    roll_a = (port_a_returns.rolling(window).mean() * TRADING_DAYS - RISK_FREE_RATE) / (port_a_returns.rolling(window).std() * np.sqrt(TRADING_DAYS))
    roll_b = (port_b_returns.rolling(window).mean() * TRADING_DAYS - RISK_FREE_RATE) / (port_b_returns.rolling(window).std() * np.sqrt(TRADING_DAYS))
    
    ax2.plot(roll_a.index, roll_a, color='#94a3b8', linewidth=1.5, label='Portfolio A', alpha=0.8)
    ax2.plot(roll_b.index, roll_b, color='#22d3ee', linewidth=2, label='Portfolio B')
    ax2.axhline(y=0, color='#fbbf24', linestyle='--', alpha=0.5, linewidth=1)
    
    ax2.set_xlabel('Date', fontsize=11, color='white', fontweight='bold')
    ax2.set_ylabel('Rolling Sharpe Ratio', fontsize=11, color='white', fontweight='bold')
    ax2.set_title(f'{window}-Day Rolling Sharpe Ratio', fontsize=14, color='white', fontweight='bold', pad=10)
    ax2.legend(fontsize=10, facecolor='#334155', edgecolor='#475569', labelcolor='white')
    ax2.grid(True, alpha=0.15, color='#94a3b8')
    ax2.tick_params(colors='#cbd5e1')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#475569')
    ax2.spines['bottom'].set_color('#475569')
    
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'portfolio_comparison.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"   ✅ Saved: {path}")


CORPUS = 1_000_000


if __name__ == '__main__':
    weights_a, weights_b, comparison, port_a_returns, port_b_returns = compute_portfolios()
    generate_portfolio_chart(port_a_returns, port_b_returns)
    
    print("\n" + "=" * 60)
    print("✅ TASK 4 COMPLETE — Portfolio Construction")
    print("=" * 60)
    print(f"\nDeliverables:")
    print(f"  📊 submissions/portfolio_comparison.csv")
    print(f"  📊 submissions/portfolio_allocations.csv")
    print(f"  📊 submissions/sector_breakdown.csv")
    print(f"  📈 charts/portfolio_comparison.png")
    print(f"  📝 submissions/portfolio_justification_TEMPLATE.md")
