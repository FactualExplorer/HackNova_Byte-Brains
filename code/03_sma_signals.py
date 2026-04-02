"""
Technical Signal Dashboard
Computes 50-day and 200-day SMA for 15 stocks.
Identifies Golden Cross / Death Cross / Neutral signals.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import warnings
warnings.filterwarnings('ignore')

# Paths─
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

# Representative stocks for SMA charts (one per sector)
CHART_STOCKS = {
    'Banking': 'HDFCBANK',
    'IT': 'TCS',
    'Pharma': 'SUNPHARMA',
}

SECTOR_COLORS = {
    'Banking': '#2563eb',
    'IT': '#16a34a',
    'Pharma': '#dc2626',
}


def compute_sma_signals():
    """Compute SMA-50, SMA-200, and identify crossover signals."""
    print("\nComputing SMA signals...")
    
    adj_close = pd.read_csv(os.path.join(DATA_DIR, 'adj_close_pivot.csv'), 
                            index_col=0, parse_dates=True)
    adj_close.sort_index(inplace=True)
    
    stocks = [c for c in adj_close.columns if c != 'NIFTY50']
    results = []
    
    for ticker in stocks:
        prices = adj_close[ticker].dropna()
        
        # Compute SMAs
        sma_50 = prices.rolling(50).mean()
        sma_200 = prices.rolling(200).mean()
        
        # Current values (as of last date)
        last_sma50 = sma_50.iloc[-1]
        last_sma200 = sma_200.iloc[-1]
        
        # Determine signal
        if last_sma50 > last_sma200:
            signal = 'Golden Cross'
        elif last_sma50 < last_sma200:
            signal = 'Death Cross'
        else:
            signal = 'Neutral'
        
        # Find last crossover date
        sma_diff = sma_50 - sma_200
        sma_diff = sma_diff.dropna()
        
        crossover_date = 'N/A'
        if len(sma_diff) > 1:
            # Sign changes indicate crossovers
            sign_changes = (sma_diff > 0).astype(int).diff()
            crossovers = sign_changes[sign_changes != 0].dropna()
            if len(crossovers) > 0:
                crossover_date = crossovers.index[-1].strftime('%Y-%m-%d')
        
        sector = SECTOR_MAP.get(ticker, 'Unknown')
        
        results.append({
            'Ticker': ticker,
            'Sector': sector,
            'SMA-50': round(last_sma50, 2),
            'SMA-200': round(last_sma200, 2),
            'Signal': signal,
            'Last Crossover Date': crossover_date,
        })
        
        print(f"  {ticker:12s} | SMA-50: {last_sma50:10.2f} | SMA-200: {last_sma200:10.2f} | {signal:12s} | Last X: {crossover_date}")
    
    signal_df = pd.DataFrame(results)
    
    csv_path = os.path.join(SUBMISSIONS_DIR, 'sma_signal_table.csv')
    signal_df.to_csv(csv_path, index=False)
    print(f"\nSMA signals: {csv_path}")
    
    return signal_df


def generate_sma_chart(ticker, sector):
    """Generate price chart with SMA overlay and crossover markers."""
    adj_close = pd.read_csv(os.path.join(DATA_DIR, 'adj_close_pivot.csv'),
                            index_col=0, parse_dates=True)
    adj_close.sort_index(inplace=True)
    
    prices = adj_close[ticker].dropna()
    sma_50 = prices.rolling(50).mean()
    sma_200 = prices.rolling(200).mean()
    
    # Find all crossover points
    sma_diff = sma_50 - sma_200
    sma_diff = sma_diff.dropna()
    sign_changes = (sma_diff > 0).astype(int).diff()
    crossovers = sign_changes[sign_changes != 0].dropna()
    
    # Create chart
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    color = SECTOR_COLORS.get(sector, '#8b5cf6')
    
    # Plot price and SMAs
    ax.plot(prices.index, prices, color=color, linewidth=1.5, alpha=0.9, label=f'{ticker} Price')
    ax.plot(sma_50.index, sma_50, color='#fbbf24', linewidth=1.8, linestyle='--', alpha=0.8, label='SMA-50')
    ax.plot(sma_200.index, sma_200, color='#f97316', linewidth=1.8, linestyle='-.', alpha=0.8, label='SMA-200')
    
    # Fill between SMAs for visual clarity
    valid_idx = sma_200.dropna().index
    ax.fill_between(valid_idx, sma_50[valid_idx], sma_200[valid_idx],
                    where=sma_50[valid_idx] > sma_200[valid_idx],
                    color='#22c55e', alpha=0.1, label='Bullish Zone')
    ax.fill_between(valid_idx, sma_50[valid_idx], sma_200[valid_idx],
                    where=sma_50[valid_idx] <= sma_200[valid_idx],
                    color='#ef4444', alpha=0.1, label='Bearish Zone')
    
    # Mark crossover events
    for date, val in crossovers.items():
        if date in prices.index:
            price_at_cross = prices[date]
            if val > 0:  # Golden Cross (SMA50 crosses above SMA200)
                ax.scatter(date, price_at_cross, color='#22c55e', s=200, zorder=10,
                          marker='^', edgecolors='white', linewidth=2)
                ax.annotate('Golden\nCross', (date, price_at_cross),
                          textcoords="offset points", xytext=(15, 20),
                          fontsize=9, color='#22c55e', fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#22c55e', alpha=0.8),
                          arrowprops=dict(arrowstyle='->', color='#22c55e', lw=1.5))
            else:  # Death Cross
                ax.scatter(date, price_at_cross, color='#ef4444', s=200, zorder=10,
                          marker='v', edgecolors='white', linewidth=2)
                ax.annotate('Death\nCross', (date, price_at_cross),
                          textcoords="offset points", xytext=(15, -30),
                          fontsize=9, color='#ef4444', fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#ef4444', alpha=0.8),
                          arrowprops=dict(arrowstyle='->', color='#ef4444', lw=1.5))
    
    ax.set_xlabel('Date', fontsize=12, color='white', fontweight='bold')
    ax.set_ylabel('Price (₹)', fontsize=12, color='white', fontweight='bold')
    ax.set_title(f'{ticker} ({sector}) — Price with 50-Day & 200-Day SMA (2023–2024)',
                 fontsize=15, color='white', fontweight='bold', pad=15)
    
    ax.legend(fontsize=10, loc='upper left', facecolor='#334155', edgecolor='#475569',
              labelcolor='white', framealpha=0.9, ncol=3)
    ax.grid(True, alpha=0.15, color='#94a3b8')
    ax.tick_params(colors='#cbd5e1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    chart_name = f'sma_{sector.lower()}.png'
    path = os.path.join(CHARTS_DIR, chart_name)
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  SMA chart: {path}")


if __name__ == '__main__':
    signal_df = compute_sma_signals()
    
    print("\nGenerating SMA charts...")
    for sector, ticker in CHART_STOCKS.items():
        print(f"\n  {ticker} ({sector})...")
        generate_sma_chart(ticker, sector)
    
    print("\nTask 3 complete.")
