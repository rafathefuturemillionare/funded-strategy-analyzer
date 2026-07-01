# Funded Strategy Analyzer V2

A Streamlit dashboard for checking TradingView strategy CSV exports against funded-account rules.

## V2 Fixes

- Fixes TradingView double-counting by keeping **Exit** rows only and ignoring **Entry** rows.
- Shows original CSV rows vs rows used as closed trades.
- Shows backtest start/end dates, calendar days, and trades per active day.
- Shows raw net P&L and cost-adjusted net profit separately.
- Adds a 50% consistency-rule checker.

## Run

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Important

If you want the dashboard to match TradingView exactly, set:

- Extra commission per closed trade = 0
- Extra slippage estimate per closed trade = 0

If you want a more conservative test, leave realistic extra costs on.
