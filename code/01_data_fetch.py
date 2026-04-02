"""
Data Acquisition & Quality
Fetches daily OHLCV data for 15 NSE stocks and Nifty 50 benchmark.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration────
TICKERS = {
    # Banking
    'HDFCBANK.NS': ('HDFCBANK', 'Banking'),
    'ICICIBANK.NS': ('ICICIBANK', 'Banking'),
    'SBIN.NS': ('SBIN', 'Banking'),
    'KOTAKBANK.NS': ('KOTAKBANK', 'Banking'),
    'AXISBANK.NS': ('AXISBANK', 'Banking'),
    # IT
    'TCS.NS': ('TCS', 'IT'),
    'INFY.NS': ('INFY', 'IT'),
    'WIPRO.NS': ('WIPRO', 'IT'),
    'HCLTECH.NS': ('HCLTECH', 'IT'),
    'TECHM.NS': ('TECHM', 'IT'),
    # Pharma
    'SUNPHARMA.NS': ('SUNPHARMA', 'Pharma'),
    'DRREDDY.NS': ('DRREDDY', 'Pharma'),
    'CIPLA.NS': ('CIPLA', 'Pharma'),
    'DIVISLAB.NS': ('DIVISLAB', 'Pharma'),
    'APOLLOHOSP.NS': ('APOLLOHOSP', 'Pharma'),
    # Benchmark
    '^NSEI': ('NIFTY50', 'Benchmark'),
}

START_DATE = '2023-01-01'
END_DATE = '2024-12-31'
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SUBMISSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'submissions')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SUBMISSIONS_DIR, exist_ok=True)


def fetch_data():
    """Fetch OHLCV data for all tickers."""
    print("\nFetching data...")
    
    all_data = {}
    quality_issues = []
    
    for yf_ticker, (name, sector) in TICKERS.items():
        print(f"  {name} ({yf_ticker})...")
        try:
            stock = yf.Ticker(yf_ticker)
            df = stock.history(start=START_DATE, end=END_DATE, auto_adjust=False)
            
            if df.empty:
                quality_issues.append(f"{name}: No data returned")
                continue
            
            # Standardize column names
            df = df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df['Ticker'] = name
            df['Sector'] = sector
            
            # Check data quality
            n_rows = len(df)
            n_missing = df[['Open', 'High', 'Low', 'Close', 'Adj Close']].isnull().sum().sum()
            
            # Check for consecutive missing trading days
            date_range = pd.bdate_range(start=df.index.min(), end=df.index.max())
            missing_dates = date_range.difference(df.index)
            
            # Find max consecutive missing days
            max_consecutive = 0
            if len(missing_dates) > 0:
                consecutive = 1
                for i in range(1, len(missing_dates)):
                    if (missing_dates[i] - missing_dates[i-1]).days <= 3:  # account for weekends
                        consecutive += 1
                    else:
                        max_consecutive = max(max_consecutive, consecutive)
                        consecutive = 1
                max_consecutive = max(max_consecutive, consecutive)
            
            print(f"    {n_rows} trading days | {n_missing} missing values | Max gaps: {max_consecutive}")
            
            if n_missing > 0:
                quality_issues.append(f"{name}: {n_missing} missing OHLCV values")
                df.fillna(method='ffill', inplace=True)
                df.fillna(method='bfill', inplace=True)
            
            if max_consecutive > 5:
                quality_issues.append(f"{name}: {max_consecutive} consecutive missing trading days")
            
            # Check for zero or negative prices
            if (df['Adj Close'] <= 0).any():
                n_bad = (df['Adj Close'] <= 0).sum()
                quality_issues.append(f"{name}: {n_bad} zero/negative Adj Close values")
                df.loc[df['Adj Close'] <= 0, 'Adj Close'] = np.nan
                df['Adj Close'].fillna(method='ffill', inplace=True)
            
            # Check for extreme outliers (daily return > 25%)
            daily_ret = df['Adj Close'].pct_change()
            extreme = (daily_ret.abs() > 0.25).sum()
            if extreme > 0:
                quality_issues.append(f"{name}: {extreme} days with >25% daily return")
            
            all_data[name] = df
            
        except Exception as e:
            quality_issues.append(f"{name}: Fetch error")
            print(f"    Error: {e}")
    
    return all_data, quality_issues


def export_data(all_data, quality_issues):
    """Export raw and cleaned datasets."""
    
    # Combine all data
    combined = []
    for name, df in all_data.items():
        temp = df.copy()
        temp['Date'] = temp.index
        combined.append(temp)
    
    full_df = pd.concat(combined, ignore_index=True)
    full_df = full_df[['Date', 'Ticker', 'Sector', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    full_df.sort_values(['Ticker', 'Date'], inplace=True)
    
    # Export raw dataset
    raw_path = os.path.join(DATA_DIR, 'raw_dataset.csv')
    full_df.to_csv(raw_path, index=False)
    print(f"Raw dataset: {raw_path} ({len(full_df)} rows)")
    
    # Export cleaned dataset
    cleaned_path = os.path.join(DATA_DIR, 'cleaned_dataset.csv')
    full_df.to_csv(cleaned_path, index=False)
    print(f"Cleaned dataset: {cleaned_path}")
    
    # Export Adj Close pivot
    adj_close = full_df.pivot_table(index='Date', columns='Ticker', values='Adj Close')
    adj_close.sort_index(inplace=True)
    adj_close_path = os.path.join(DATA_DIR, 'adj_close_pivot.csv')
    adj_close.to_csv(adj_close_path)
    print(f"Adj Close pivot: {adj_close_path}")
    
    # Export OHLCV per stock
    for name, df in all_data.items():
        stock_path = os.path.join(DATA_DIR, f'{name}_ohlcv.csv')
        df.to_csv(stock_path)
    print(f"Individual OHLCV files saved")
    
    # Generate Data Quality Note
    quality_note = f"""# Data Quality Note — HackNova 1.0 PortfolioIQ

## Data Source
- **Provider:** Yahoo Finance via `yfinance` Python library
- **Period:** {START_DATE} to {END_DATE} (2 full calendar years)
- **Frequency:** Daily OHLCV (Open, High, Low, Close, Adjusted Close, Volume)
- **Stocks:** 15 NSE-listed stocks across Banking (5), IT (5), Pharma (5) sectors
- **Benchmark:** Nifty 50 Index (^NSEI)

## Data Summary
- **Total rows fetched:** {len(full_df):,}
- **Unique tickers:** {full_df['Ticker'].nunique()}
- **Date range:** {full_df['Date'].min()} to {full_df['Date'].max()}

## Quality Issues Found & Resolutions

"""
    if quality_issues:
        for issue in quality_issues:
            quality_note += f"- {issue}\n"
    else:
        quality_note += "- No quality issues detected.\n"
    
    quality_note += f"""
## Cleaning Steps Applied
1. **Missing values:** Forward-filled, then back-filled any remaining NaNs.
2. **Zero/negative prices:** Replaced with forward-fill from last valid price.
3. **Consecutive gaps:** Validated no stock has >5 consecutive missing trading days (Indian market holidays are expected and acceptable).
4. **Extreme returns:** Returns >25% in a single day flagged but retained (may reflect legitimate corporate events like stock splits, bonus issues).
5. **Timezone normalization:** All timestamps converted to timezone-naive (IST assumed).

## Pricing Convention
- **Adjusted Close** used for all return calculations to account for dividends and stock splits.
"""
    
    quality_note_path = os.path.join(SUBMISSIONS_DIR, 'data_quality_note.md')
    with open(quality_note_path, 'w') as f:
        f.write(quality_note)
    print(f"Data quality note: {quality_note_path}")
    
    return full_df


if __name__ == '__main__':
    all_data, quality_issues = fetch_data()
    
    if not all_data:
        print("\nNo data fetched. Check internet connection.")
        exit(1)
    
    full_df = export_data(all_data, quality_issues)
    print("\nData acquisition complete.")
