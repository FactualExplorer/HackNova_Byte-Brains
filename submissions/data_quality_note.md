# Data Quality Note — HackNova 1.0 PortfolioIQ

## Data Source
- **Provider:** Yahoo Finance via `yfinance` Python library
- **Period:** 2023-01-01 to 2024-12-31 (2 full calendar years)
- **Frequency:** Daily OHLCV (Open, High, Low, Close, Adjusted Close, Volume)
- **Stocks:** 15 NSE-listed stocks across Banking (5), IT (5), Pharma (5) sectors
- **Benchmark:** Nifty 50 Index (^NSEI)

## Data Summary
- **Total rows fetched:** 7,840
- **Unique tickers:** 16
- **Date range:** 2023-01-02 00:00:00 to 2024-12-30 00:00:00

## Quality Issues Found & Resolutions

- No quality issues detected.

## Cleaning Steps Applied
1. **Missing values:** Forward-filled, then back-filled any remaining NaNs.
2. **Zero/negative prices:** Replaced with forward-fill from last valid price.
3. **Consecutive gaps:** Validated no stock has >5 consecutive missing trading days (Indian market holidays are expected and acceptable).
4. **Extreme returns:** Returns >25% in a single day flagged but retained (may reflect legitimate corporate events like stock splits, bonus issues).
5. **Timezone normalization:** All timestamps converted to timezone-naive (IST assumed).

## Pricing Convention
- **Adjusted Close** used for all return calculations to account for dividends and stock splits.
