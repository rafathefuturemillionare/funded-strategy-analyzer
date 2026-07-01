import re

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Funded Strategy Analyzer V2", layout="wide")


# -----------------------------
# Helper functions
# -----------------------------


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).strip().lower()).strip()


def money_to_float(value):
    """Convert values like '$1,234.50', '($55.20)', '−12.3', or plain numbers to float."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return np.nan

    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("−", "-")
    text = re.sub(r"[^0-9.\-]", "", text)

    if text in ("", "-", "."):
        return np.nan

    try:
        number = float(text)
        return -abs(number) if negative else number
    except ValueError:
        return np.nan


def find_first_col(columns, include_terms, exclude_terms=None):
    exclude_terms = exclude_terms or []
    normalized = {col: normalize_name(col) for col in columns}
    for col, ncol in normalized.items():
        if all(term in ncol for term in include_terms) and not any(term in ncol for term in exclude_terms):
            return col
    return None


def detect_columns(df: pd.DataFrame):
    cols = list(df.columns)

    profit_col = (
        find_first_col(cols, ["net", "pnl"], ["cum", "%", "percent"])
        or find_first_col(cols, ["net", "p", "l"], ["cum", "%", "percent"])
        or find_first_col(cols, ["profit"], ["cum", "%", "percent"])
        or find_first_col(cols, ["pnl"], ["cum", "%", "percent"])
        or find_first_col(cols, ["p l"], ["cum", "%", "percent"])
        or find_first_col(cols, ["pl"], ["cum", "%", "percent"])
    )

    date_col = (
        find_first_col(cols, ["date", "time"])
        or find_first_col(cols, ["time"])
        or find_first_col(cols, ["exit", "time"])
        or find_first_col(cols, ["entry", "time"])
    )

    side_col = (
        find_first_col(cols, ["type"])
        or find_first_col(cols, ["direction"])
        or find_first_col(cols, ["side"])
        or find_first_col(cols, ["signal"])
    )

    return profit_col, date_col, side_col


def max_drawdown(equity_or_pnl: pd.Series):
    running_peak = equity_or_pnl.cummax()
    drawdown = running_peak - equity_or_pnl
    return float(drawdown.max()), drawdown


def longest_losing_streak(profits: pd.Series):
    streak = 0
    max_streak = 0
    for p in profits.fillna(0):
        if p < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return int(max_streak)


def safe_divide(a, b):
    if b == 0:
        return np.inf if a > 0 else 0
    return a / b


def format_money(x):
    if pd.isna(x) or x is None:
        return "—"
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.2f}"


def format_number(x):
    if x == np.inf:
        return "∞"
    if pd.isna(x) or x is None:
        return "—"
    return f"{x:,.2f}"


def calc_grade(metrics, passes_rules: bool):
    score = 0

    if metrics["net_profit"] > 0:
        score += 20

    if metrics["profit_factor"] >= 2.0:
        score += 25
    elif metrics["profit_factor"] >= 1.5:
        score += 15
    elif metrics["profit_factor"] >= 1.2:
        score += 7

    if metrics["win_rate"] >= 50:
        score += 15
    elif metrics["win_rate"] >= 40:
        score += 8

    if metrics["avg_trade"] > 0:
        score += 10

    if metrics["max_drawdown"] <= max(metrics["net_profit"] * 0.25, 1):
        score += 15
    elif metrics["max_drawdown"] <= max(metrics["net_profit"] * 0.50, 1):
        score += 8

    if passes_rules:
        score += 15
    else:
        score -= 15

    score = max(0, min(100, score))

    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return score, grade


# -----------------------------
# App UI
# -----------------------------

st.title("Funded Strategy Analyzer V2")
st.caption("Upload a TradingView strategy trade-list CSV. V2 fixes TradingView entry/exit double-counting.")

with st.sidebar:
    st.header("Funded Rules")
    profit_target = st.number_input("Profit target", value=9000.0, step=100.0)
    max_total_drawdown_limit = st.number_input("Max total drawdown allowed", value=4500.0, step=50.0)
    max_daily_loss_limit = st.number_input("Max daily loss allowed", value=999999.0, step=50.0)

    st.header("Consistency Rule")
    use_consistency_rule = st.checkbox("Use consistency rule", value=True)
    consistency_percent = st.number_input("Max % of profit from biggest winning day", value=50.0, min_value=1.0, max_value=100.0, step=1.0)

    st.header("Realism Adjustments")
    commission_per_trade = st.number_input("Extra commission per closed trade", value=1.50, step=0.25)
    slippage_per_trade = st.number_input("Extra slippage estimate per closed trade", value=2.00, step=0.25)
    st.caption("Set both to 0 if you want the dashboard to match TradingView exactly.")

    st.header("Optional Settings")
    starting_balance = st.number_input("Starting balance", value=150000.0, step=1000.0)

uploaded_file = st.file_uploader("Upload your TradingView CSV", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV to begin. In TradingView Strategy Tester, export the List of Trades as a CSV.")
    st.stop()

try:
    raw_df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

if raw_df.empty:
    st.error("The CSV loaded, but it has no rows.")
    st.stop()

st.subheader("Column Mapping")
profit_guess, date_guess, side_guess = detect_columns(raw_df)

cols = list(raw_df.columns)
none_option = "None"

c1, c2, c3 = st.columns(3)
with c1:
    profit_col = st.selectbox(
        "Profit / P&L column",
        options=cols,
        index=cols.index(profit_guess) if profit_guess in cols else 0,
    )
with c2:
    date_options = [none_option] + cols
    date_col = st.selectbox(
        "Date/time column",
        options=date_options,
        index=date_options.index(date_guess) if date_guess in date_options else 0,
    )
with c3:
    side_options = [none_option] + cols
    side_col = st.selectbox(
        "Long/short or type column",
        options=side_options,
        index=side_options.index(side_guess) if side_guess in side_options else 0,
    )

st.subheader("TradingView Row Handling")
auto_exit_filter = st.checkbox(
    "Analyze closed trades only: keep Exit rows and ignore Entry rows",
    value=True,
    help="TradingView often exports one Entry row and one Exit row per trade. Counting both doubles the results.",
)

if "trade number" in normalize_name(profit_col) or normalize_name(profit_col) in {"trade", "trade no", "trade number"}:
    st.error("The P&L column is set to Trade number. Choose Net PnL USD, Profit, or another actual P&L column.")
    st.stop()

# Prepare dataframe
trades = raw_df.copy()
raw_row_count = len(trades)

if side_col != none_option:
    trades["Side"] = trades[side_col].astype(str)
else:
    trades["Side"] = "Unknown"

entry_rows = int(trades["Side"].str.contains("entry", case=False, na=False).sum())
exit_rows = int(trades["Side"].str.contains("exit", case=False, na=False).sum())

if auto_exit_filter and exit_rows > 0:
    trades = trades[trades["Side"].str.contains("exit", case=False, na=False)].copy()

trades["Raw Profit"] = trades[profit_col].apply(money_to_float)
trades = trades.dropna(subset=["Raw Profit"]).copy()

if trades.empty:
    st.error("I could not find numeric profit values in the selected P&L column. Try choosing a different P&L column.")
    st.stop()

if date_col != none_option:
    trades["Datetime"] = pd.to_datetime(trades[date_col], errors="coerce")
    if trades["Datetime"].notna().any():
        trades = trades.sort_values("Datetime").copy()
else:
    trades["Datetime"] = pd.NaT

# Adjust for extra realistic costs
cost_per_closed_trade = commission_per_trade + slippage_per_trade
trades["Adjusted Profit"] = trades["Raw Profit"] - cost_per_closed_trade
profits = trades["Adjusted Profit"]
raw_profits = trades["Raw Profit"]

trades = trades.reset_index(drop=True)
trades["Trade #"] = trades.index + 1
trades["Cumulative P&L"] = trades["Adjusted Profit"].cumsum()
trades["Raw Cumulative P&L"] = trades["Raw Profit"].cumsum()
trades["Equity"] = starting_balance + trades["Cumulative P&L"]

net_profit = float(profits.sum())
raw_net_profit = float(raw_profits.sum())
total_extra_costs = float(cost_per_closed_trade * len(trades))
gross_profit = float(profits[profits > 0].sum())
gross_loss = float(profits[profits < 0].sum())
profit_factor = safe_divide(gross_profit, abs(gross_loss))
win_rate = float((profits > 0).mean() * 100)
total_trades = int(len(profits))
avg_trade = float(profits.mean())
avg_win = float(profits[profits > 0].mean()) if (profits > 0).any() else 0.0
avg_loss = float(profits[profits < 0].mean()) if (profits < 0).any() else 0.0
biggest_win = float(profits.max())
biggest_loss = float(profits.min())
max_dd, dd_series = max_drawdown(trades["Cumulative P&L"])
loss_streak = longest_losing_streak(profits)

trades["Drawdown"] = dd_series
worst_dd_date = "—"
if trades["Datetime"].notna().any() and len(trades):
    worst_dd_idx = trades["Drawdown"].idxmax()
    worst_dd_date = str(trades.loc[worst_dd_idx, "Datetime"])

# Date and daily stats
if trades["Datetime"].notna().any():
    trades["Date"] = trades["Datetime"].dt.date
    trades["Hour"] = trades["Datetime"].dt.hour
    start_dt = trades["Datetime"].min()
    end_dt = trades["Datetime"].max()
    calendar_days = max(int((end_dt - start_dt).days) + 1, 1)
    months = max(calendar_days / 30.4375, 1 / 30.4375)
    active_days = int(trades["Date"].nunique())
    daily_pnl = trades.groupby("Date")["Adjusted Profit"].sum().sort_index()
    max_daily_loss_actual = abs(float(daily_pnl.min())) if len(daily_pnl) else 0.0
    biggest_winning_day = float(daily_pnl.max()) if len(daily_pnl) else 0.0
    profit_per_month = net_profit / months
    trades_per_active_day = total_trades / active_days if active_days else 0.0
    hourly = trades.groupby("Hour")["Adjusted Profit"].agg(["count", "sum", "mean"]).reset_index()
    best_hour_row = hourly.sort_values("sum", ascending=False).head(1)
    worst_hour_row = hourly.sort_values("sum", ascending=True).head(1)
else:
    start_dt = None
    end_dt = None
    calendar_days = None
    active_days = None
    daily_pnl = pd.Series(dtype=float)
    max_daily_loss_actual = 0.0
    biggest_winning_day = 0.0
    profit_per_month = None
    trades_per_active_day = None
    hourly = pd.DataFrame()
    best_hour_row = pd.DataFrame()
    worst_hour_row = pd.DataFrame()

passes_profit_target = net_profit >= profit_target
passes_total_dd = max_dd <= max_total_drawdown_limit
passes_daily_loss = max_daily_loss_actual <= max_daily_loss_limit if len(daily_pnl) else True

if use_consistency_rule and len(daily_pnl) and net_profit > 0:
    consistency_limit_dollars = net_profit * (consistency_percent / 100)
    passes_consistency = biggest_winning_day <= consistency_limit_dollars
else:
    consistency_limit_dollars = np.nan
    passes_consistency = True

passes_rules = passes_profit_target and passes_total_dd and passes_daily_loss and passes_consistency

metrics = {
    "net_profit": net_profit,
    "profit_factor": profit_factor,
    "win_rate": win_rate,
    "avg_trade": avg_trade,
    "max_drawdown": max_dd,
}
score, grade = calc_grade(metrics, passes_rules)

# -----------------------------
# Results
# -----------------------------

st.subheader("Data Check")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Original CSV Rows", f"{raw_row_count:,}")
d2.metric("Rows Used as Closed Trades", f"{total_trades:,}")
d3.metric("Entry Rows Found", f"{entry_rows:,}")
d4.metric("Exit Rows Found", f"{exit_rows:,}")

if entry_rows > 0 and exit_rows > 0 and not auto_exit_filter:
    st.warning("This looks like a TradingView entry/exit export. Turn on the Exit-row filter or your results will probably be doubled.")
elif entry_rows > 0 and exit_rows > 0 and total_trades == exit_rows:
    st.success("Entry/exit double-counting fixed: the app is using Exit rows only.")

st.subheader("Backtest Period")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Start", str(start_dt.date()) if start_dt is not None else "No date")
p2.metric("End", str(end_dt.date()) if end_dt is not None else "No date")
p3.metric("Calendar Days", f"{calendar_days:,}" if calendar_days is not None else "No date")
p4.metric("Trades / Active Day", f"{trades_per_active_day:.2f}" if trades_per_active_day is not None else "No date")

st.subheader("Strategy Score")
score_col, grade_col, pass_col = st.columns(3)
score_col.metric("Score", f"{score}/100")
grade_col.metric("Grade", grade)
pass_col.metric("Funded Check", "PASS" if passes_rules else "FAIL")

st.subheader("Main Metrics")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Adjusted Net Profit", format_money(net_profit))
m2.metric("Profit Factor", format_number(profit_factor))
m3.metric("Win Rate", f"{win_rate:.1f}%")
m4.metric("Max Drawdown", format_money(max_dd))

m5, m6, m7, m8 = st.columns(4)
m5.metric("Closed Trades", f"{total_trades:,}")
m6.metric("Avg Trade", format_money(avg_trade))
m7.metric("Avg Win", format_money(avg_win))
m8.metric("Avg Loss", format_money(avg_loss))

m9, m10, m11, m12 = st.columns(4)
m9.metric("Raw Net P&L", format_money(raw_net_profit))
m10.metric("Extra Costs Subtracted", format_money(total_extra_costs))
m11.metric("Profit / Month", format_money(profit_per_month) if profit_per_month is not None else "No date")
m12.metric("Worst DD Time", worst_dd_date[:19] if worst_dd_date != "—" else "—")

m13, m14, m15, m16 = st.columns(4)
m13.metric("Biggest Win", format_money(biggest_win))
m14.metric("Biggest Loss", format_money(biggest_loss))
m15.metric("Longest Losing Streak", str(loss_streak))
m16.metric("Worst Daily Loss", format_money(max_daily_loss_actual) if len(daily_pnl) else "No date column")

st.subheader("Funded Rule Check")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Profit Target", "PASS" if passes_profit_target else "FAIL", f"Need {format_money(profit_target)}")
r2.metric("Total Drawdown", "PASS" if passes_total_dd else "FAIL", f"Limit {format_money(max_total_drawdown_limit)}")
r3.metric("Daily Loss", "PASS" if passes_daily_loss else "FAIL", f"Limit {format_money(max_daily_loss_limit)}")
r4.metric(
    "Consistency",
    "PASS" if passes_consistency else "FAIL",
    f"Biggest day {format_money(biggest_winning_day)} / Limit {format_money(consistency_limit_dollars)}" if use_consistency_rule and len(daily_pnl) and net_profit > 0 else "Not checked",
)

st.subheader("Charts")
st.write("Cumulative P&L")
st.line_chart(trades.set_index("Trade #")[["Cumulative P&L"]])
st.write("Drawdown")
st.line_chart(trades.set_index("Trade #")[["Drawdown"]])

if len(daily_pnl):
    st.write("Daily P&L")
    st.bar_chart(daily_pnl)

if not hourly.empty:
    st.write("P&L by Hour")
    st.bar_chart(hourly.set_index("Hour")[["sum"]])

st.subheader("Explanation")
notes = []

if entry_rows > 0 and exit_rows > 0:
    notes.append("TradingView exported both Entry and Exit rows. This version uses Exit rows only so each closed trade is counted once.")

if passes_rules:
    notes.append("This strategy passes the basic funded-rule check using the rules you entered.")
else:
    notes.append("This strategy fails at least one funded-rule check using the rules you entered.")

if profit_factor >= 2:
    notes.append("Profit factor is strong, which means gross wins are much larger than gross losses.")
elif profit_factor >= 1.3:
    notes.append("Profit factor is okay, but not amazing. It may need better filtering or risk control.")
else:
    notes.append("Profit factor is weak. This strategy probably needs major improvement before live use.")

if max_dd > max_total_drawdown_limit:
    notes.append("The biggest issue is total drawdown. A funded evaluation can fail even if the strategy is profitable overall.")

if use_consistency_rule and len(daily_pnl) and net_profit > 0 and not passes_consistency:
    notes.append("The consistency rule failed because one winning day contributes too much of the total profit.")

if len(daily_pnl) and max_daily_loss_actual > max_daily_loss_limit:
    notes.append("The strategy also has at least one day with too much loss.")

if total_trades > 500:
    notes.append("The strategy takes a lot of trades. Check whether commissions and slippage weaken the edge.")

if avg_trade <= cost_per_closed_trade * 2:
    notes.append("Average trade is small compared with estimated costs. That makes the backtest fragile.")

if not best_hour_row.empty and not worst_hour_row.empty:
    best_hour = int(best_hour_row.iloc[0]["Hour"])
    worst_hour = int(worst_hour_row.iloc[0]["Hour"])
    notes.append(f"Best hour by total P&L: {best_hour}:00. Worst hour by total P&L: {worst_hour}:00.")

for note in notes:
    st.write(f"- {note}")

st.subheader("Cleaned Trade Data")
show_cols = ["Trade #", "Raw Profit", "Adjusted Profit", "Cumulative P&L", "Drawdown", "Datetime", "Side"]
st.dataframe(trades[show_cols], use_container_width=True)

csv_output = trades.to_csv(index=False).encode("utf-8")
st.download_button("Download cleaned results", csv_output, "cleaned_strategy_results_v2.csv", "text/csv")
