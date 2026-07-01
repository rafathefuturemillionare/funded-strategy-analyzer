# Funded Strategy Analyzer V4

A cleaner Streamlit dashboard for checking whether a TradingView strategy trade-list CSV could pass a funded evaluation.

## Features

- TradingView CSV upload
- Exit-row filter to avoid double-counting TradingView entry/exit rows
- Funded rule check
- Personal drawdown safety goal
- Consistency rule check
- Rolling 30-day evaluation simulator
- Version comparison table
- Charts and downloadable CSV results
- Cleaner V4 interface

## Run locally

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

Upload these files to your GitHub repo:

- `app.py`
- `requirements.txt`
- `README.md`
- `sample_trades.csv`

Then reboot/redeploy the Streamlit app.
