# Funded Strategy Analyzer V3

A simple Streamlit website for checking TradingView strategy CSVs against funded-account rules.

## What V3 adds

- Clean tabs so the site does not feel cluttered
- Rolling 30-day evaluation simulator
- Personal safety drawdown goal
- Version comparison table
- Download buttons for cleaned trades, rolling results, and comparisons

## Run locally

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy on Streamlit Cloud

Upload/replace these files in your GitHub repo:

- `app.py`
- `requirements.txt`
- `README.md`

Then redeploy or reboot the Streamlit app.

## Notes

The rolling simulator uses daily closed P&L from the CSV. It is a decision tool, not a guarantee of live performance. TradingView may show slightly different max drawdown because it can use intrabar/open-equity drawdown.
