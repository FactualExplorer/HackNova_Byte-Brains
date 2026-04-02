"""
Risk & Return Analysis
Computes metrics for 15 stocks and generates charts.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Paths─
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'submissions')
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(SUBMISSIONS_DIR, exist_ok=True)

# Constants
TRADING_DAYS = 252
RISK_FREE_RATE = 0.065  # 6.5% p.a.

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
}


def load_data():
    """Load adj close pivot."""
    df = pd.read_csv(os.path.join(DATA_DIR, 'adj_close_pivot.csv'), index_col=0, parse_dates=True)
    df.sort_index(inplace=True)
    return df


def compute_metrics(adj_close):
    """Compute metrics for each stock."""
    print("\nComputing metrics...")
    
    # Separate benchmark
    stocks = [c for c in adj_close.columns if c != 'NIFTY50']
    nifty = adj_close['NIFTY50']
    
    # Daily returns
    daily_returns = adj_close[stocks].pct_change().dropna()
    nifty_returns = nifty.pct_change().dropna()
    
    # Align dates
    common_idx = daily_returns.index.intersection(nifty_returns.index)
    daily_returns = daily_returns.loc[common_idx]
    nifty_returns = nifty_returns.loc[common_idx]
    
    results = []
    
    for ticker in stocks:
        stock_prices = adj_close[ticker].dropna()
        stock_returns = daily_returns[ticker].dropna()
        
        n_days = len(stock_returns)
        
        # 1. Annualized Return (%)
        total_return = stock_prices.iloc[-1] / stock_prices.iloc[0]
        ann_return = (total_return ** (TRADING_DAYS / n_days)) - 1
        
        # 2. Annualized Volatility (%)
        ann_vol = stock_returns.std() * np.sqrt(TRADING_DAYS)
        
        # 3. Sharpe Ratio
        sharpe = (ann_return - RISK_FREE_RATE) / ann_vol
        
        # 4. Beta vs Nifty 50
        aligned_stock = stock_returns.loc[common_idx]
        aligned_nifty = nifty_returns.loc[common_idx]
        cov_matrix = np.cov(aligned_stock, aligned_nifty)
        beta = cov_matrix[0, 1] / cov_matrix[1, 1]
        
        # 5. Maximum Drawdown (%)
        cumulative = (1 + stock_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 6. SMA values (computed here, detailed in Task 3)
        sma_50 = stock_prices.rolling(50).mean().iloc[-1]
        sma_200 = stock_prices.rolling(200).mean().iloc[-1]
        
        # Determine signal
        if sma_50 > sma_200:
            signal = 'Golden Cross'
        elif sma_50 < sma_200:
            signal = 'Death Cross'
        else:
            signal = 'Neutral'
        
        sector = SECTOR_MAP.get(ticker, 'Unknown')
        
        results.append({
            'Ticker': ticker,
            'Sector': sector,
            'Annualized Return (%)': round(ann_return * 100, 2),
            'Annualized Volatility (%)': round(ann_vol * 100, 2),
            'Sharpe Ratio': round(sharpe, 4),
            'Beta vs Nifty 50': round(beta, 4),
            'Maximum Drawdown (%)': round(max_drawdown * 100, 2),
            'SMA-50': round(sma_50, 2),
            'SMA-200': round(sma_200, 2),
            'SMA Signal': signal,
        })
        
        print(f"\n{ticker} ({sector}):")
        print(f"      Return: {ann_return*100:.2f}% | Vol: {ann_vol*100:.2f}% | Sharpe: {sharpe:.4f}")
        print(f"      Beta: {beta:.4f} | Max DD: {max_drawdown*100:.2f}% | Signal: {signal}")
    
    metrics_df = pd.DataFrame(results)
    return metrics_df, daily_returns


def generate_risk_return_scatter(metrics_df):
    """Generate Risk-Return scatter plot."""
    print("\nGenerating Risk-Return scatter plot...")
    
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Set dark background
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    for sector in ['Banking', 'IT', 'Pharma']:
        subset = metrics_df[metrics_df['Sector'] == sector]
        color = SECTOR_COLORS[sector]
        ax.scatter(
            subset['Annualized Volatility (%)'],
            subset['Annualized Return (%)'],
            c=color, s=180, alpha=0.9, edgecolors='white', linewidth=1.5,
            label=sector, zorder=5
        )
        for _, row in subset.iterrows():
            ax.annotate(
                row['Ticker'],
                (row['Annualized Volatility (%)'], row['Annualized Return (%)']),
                textcoords="offset points", xytext=(10, 8),
                fontsize=9, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7, edgecolor='none')
            )
    
    # Add risk-free rate line
    ax.axhline(y=6.5, color='#fbbf24', linestyle='--', alpha=0.6, linewidth=1, label='Risk-Free Rate (6.5%)')
    
    ax.set_xlabel('Annualized Volatility (%)', fontsize=13, color='white', fontweight='bold')
    ax.set_ylabel('Annualized Return (%)', fontsize=13, color='white', fontweight='bold')
    ax.set_title('Risk-Return Map — 15 NSE Stocks (Jan 2023 – Dec 2024)',
                 fontsize=16, color='white', fontweight='bold', pad=20)
    
    ax.legend(fontsize=11, loc='upper left', facecolor='#334155', edgecolor='#475569',
              labelcolor='white', framealpha=0.9)
    ax.grid(True, alpha=0.2, color='#94a3b8')
    ax.tick_params(colors='#cbd5e1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'risk_return_scatter.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {path}")


def generate_correlation_heatmap(daily_returns):
    """Generate correlation heatmap of daily returns."""
    print("\nGenerating correlation heatmap...")
    
    stocks_only = [c for c in daily_returns.columns if c != 'NIFTY50']
    corr = daily_returns[stocks_only].corr()
    
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    
    sns.heatmap(
        corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn',
        center=0, vmin=-0.2, vmax=1.0,
        square=True, linewidths=0.5, linecolor='#334155',
        annot_kws={'size': 8, 'weight': 'bold'},
        cbar_kws={'shrink': 0.8, 'label': 'Correlation'},
        ax=ax
    )
    
    ax.set_title('Daily Returns Correlation — 15 NSE Stocks (2023–2024)',
                 fontsize=16, color='white', fontweight='bold', pad=20)
    ax.tick_params(colors='#cbd5e1', labelsize=10)
    
    # Color the tick labels by sector
    for label in ax.get_xticklabels():
        ticker = label.get_text()
        sector = SECTOR_MAP.get(ticker, 'Unknown')
        label.set_color(SECTOR_COLORS.get(sector, 'white'))
        label.set_fontweight('bold')
    for label in ax.get_yticklabels():
        ticker = label.get_text()
        sector = SECTOR_MAP.get(ticker, 'Unknown')
        label.set_color(SECTOR_COLORS.get(sector, 'white'))
        label.set_fontweight('bold')
    
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'correlation_heatmap.png')
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {path}")


def save_metrics(metrics_df):
    """Save metrics summary table."""
    csv_path = os.path.join(SUBMISSIONS_DIR, 'metrics_summary.csv')
    metrics_df.to_csv(csv_path, index=False)
    print(f"Metrics summary: {csv_path}")
    
    xlsx_path = os.path.join(SUBMISSIONS_DIR, 'metrics_summary.xlsx')
    metrics_df.to_excel(xlsx_path, index=False, sheet_name='Metrics')
    print(f"Metrics summary: {xlsx_path}")


if __name__ == '__main__':
    adj_close = load_data()
    metrics_df, daily_returns = compute_metrics(adj_close)
    save_metrics(metrics_df)
    generate_risk_return_scatter(metrics_df)
    generate_correlation_heatmap(daily_returns)
    
    print("\nTask 2 complete.")
