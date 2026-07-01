import re
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Funded Strategy Analyzer V4", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    :root {
        --bg: #071018;
        --panel: rgba(15, 25, 38, 0.78);
        --panel-strong: rgba(18, 31, 48, 0.94);
        --border: rgba(148, 163, 184, 0.18);
        --text: #eaf2ff;
        --muted: #8ea3b8;
        --blue: #38bdf8;
        --green: #22c55e;
        --yellow: #f59e0b;
        --red: #ef4444;
        --purple: #8b5cf6;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 34rem),
            radial-gradient(circle at top right, rgba(139, 92, 246, 0.14), transparent 32rem),
            linear-gradient(135deg, #060b12 0%, #0a111d 48%, #071018 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    section[data-testid="stSidebar"] {
        background: rgba(8, 14, 23, 0.92);
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        letter-spacing: -0.02em;
    }

    .hero {
        padding: 1.45rem 1.6rem;
        border: 1px solid var(--border);
        border-radius: 26px;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(14, 37, 55, 0.78));
        box-shadow: 0 24px 80px rgba(0,0,0,0.28);
        margin-bottom: 1.1rem;
    }

    .hero-kicker {
        color: var(--blue);
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.7rem);
        font-weight: 900;
        line-height: 0.98;
        letter-spacing: -0.06em;
        margin-bottom: 0.7rem;
    }

    .hero-subtitle {
        color: var(--muted);
        font-size: 1.02rem;
        max-width: 860px;
        line-height: 1.55;
    }

    .hero-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .chip {
        border: 1px solid rgba(56, 189, 248, 0.22);
        background: rgba(56, 189, 248, 0.08);
        color: #c9f1ff;
        border-radius: 999px;
        padding: 0.42rem 0.72rem;
        font-size: 0.82rem;
        font-weight: 700;
    }

    .mini-card {
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1rem 1.05rem;
        background: rgba(15, 23, 42, 0.70);
        min-height: 104px;
    }

    .mini-title {
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 0.35rem;
    }

    .mini-text {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .verdict-card {
        border-radius: 22px;
        padding: 1rem 1.15rem;
        border: 1px solid var(--border);
        margin: 1rem 0 1rem;
        font-weight: 800;
        font-size: 1rem;
    }
    .verdict-pass { background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.32); color: #bbf7d0; }
    .verdict-warn { background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.32); color: #fde68a; }
    .verdict-fail { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.32); color: #fecaca; }

    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.70);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1rem 1rem 0.85rem 1rem;
        box-shadow: 0 14px 34px rgba(0,0,0,0.12);
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--muted) !important;
        font-weight: 800;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fbff;
        font-weight: 900;
        font-size: 1.65rem !important;
        letter-spacing: -0.04em;
    }
    div[data-testid="stMetricDelta"] {
        font-weight: 800;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(15, 23, 42, 0.54);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.35rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        padding: 0.7rem 1rem;
        font-weight: 800;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.13);
        color: #e0f7ff;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(15, 23, 42, 0.64);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1rem;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
    }
    .stButton button, .stDownloadButton button {
        border-radius: 14px !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
        background: rgba(56, 189, 248, 0.10) !important;
        color: #dff7ff !important;
        font-weight: 800 !important;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: rgba(56, 189, 248, 0.55) !important;
        background: rgba(56, 189, 248, 0.18) !important;
    }
    hr { border-color: var(--border); }
</style>
""", unsafe_allow_html=True)


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
        or find_first_col(cols, ["exit", "time"])
        or find_first_col(cols, ["entry", "time"])
        or find_first_col(cols, ["time"])
    )

    side_col = (
        find_first_col(cols, ["type"])
        or find_first_col(cols, ["direction"])
        or find_first_col(cols, ["side"])
        or find_first_col(cols, ["signal"])
    )

    return profit_col, date_col, side_col


def drawdown_from_cumulative(cumulative_pnl: pd.Series):
    """Max drawdown from a cumulative P&L series, using 0 as the starting peak."""
    if len(cumulative_pnl) == 0:
        return 0.0, pd.Series(dtype=float)
    values = np.concatenate([[0.0], cumulative_pnl.astype(float).to_numpy()])
    peaks = np.maximum.accumulate(values)
    dds = peaks - values
    return float(np.max(dds)), pd.Series(dds[1:], index=cumulative_pnl.index)


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
    return f"{sign}${abs(float(x)):,.2f}"


def format_number(x):
    if x == np.inf:
        return "∞"
    if pd.isna(x) or x is None:
        return "—"
    return f"{float(x):,.2f}"


def calc_grade(metrics, passes_rules: bool, rolling_pass_rate=None, safe_dd_pass=None):
    score = 0

    if metrics["net_profit"] > 0:
        score += 15

    if metrics["profit_factor"] >= 2.0:
        score += 20
    elif metrics["profit_factor"] >= 1.5:
        score += 14
    elif metrics["profit_factor"] >= 1.2:
        score += 7

    if metrics["win_rate"] >= 55:
        score += 12
    elif metrics["win_rate"] >= 45:
        score += 8

    if metrics["avg_trade"] > 0:
        score += 8

    if passes_rules:
        score += 20
    else:
        score -= 15

    if safe_dd_pass is True:
        score += 10
    elif safe_dd_pass is False:
        score -= 5

    if rolling_pass_rate is not None:
        if rolling_pass_rate >= 80:
            score += 15
        elif rolling_pass_rate >= 60:
            score += 10
        elif rolling_pass_rate >= 40:
            score += 5
        else:
            score -= 5

    score = int(max(0, min(100, score)))

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


def run_rolling_eval(
    daily_pnl: pd.Series,
    profit_target: float,
    max_drawdown_limit: float,
    max_daily_loss_limit: float,
    use_consistency_rule: bool,
    consistency_percent: float,
    window_days: int,
    stop_when_target_hit: bool,
):
    """Daily closed-P&L rolling evaluation simulator."""
    if daily_pnl.empty:
        return pd.DataFrame(), {}

    daily_pnl = daily_pnl.sort_index()
    all_days = pd.date_range(daily_pnl.index.min(), daily_pnl.index.max(), freq="D")
    daily_full = daily_pnl.reindex([d.date() for d in all_days], fill_value=0.0)

    n_days = len(daily_full)
    if n_days == 0:
        return pd.DataFrame(), {}

    # If the backtest is shorter than the evaluation window, still test the available period once.
    if n_days < window_days:
        start_positions = [0]
    else:
        start_positions = list(range(0, n_days - window_days + 1))

    records = []
    for pos in start_positions:
        window = daily_full.iloc[pos : min(pos + window_days, n_days)].copy()
        start_date = window.index[0]
        end_date = window.index[-1]
        cum = window.cumsum()

        target_hit = bool((cum >= profit_target).any())
        if target_hit:
            hit_date = cum[cum >= profit_target].index[0]
            days_to_target = int((pd.to_datetime(hit_date) - pd.to_datetime(start_date)).days) + 1
            if stop_when_target_hit:
                eval_window = window.loc[:hit_date]
                eval_cum = eval_window.cumsum()
            else:
                eval_window = window
                eval_cum = cum
        else:
            hit_date = None
            days_to_target = np.nan
            eval_window = window
            eval_cum = cum

        eval_net = float(eval_window.sum())
        eval_max_dd, _ = drawdown_from_cumulative(eval_cum)
        worst_daily_loss = abs(float(eval_window.min())) if len(eval_window) else 0.0
        biggest_winning_day = float(eval_window.max()) if len(eval_window) else 0.0

        passes_target = target_hit
        passes_dd = eval_max_dd <= max_drawdown_limit
        passes_daily = worst_daily_loss <= max_daily_loss_limit
        if use_consistency_rule and eval_net > 0:
            consistency_limit = eval_net * (consistency_percent / 100)
            passes_consistency = biggest_winning_day <= consistency_limit
        else:
            consistency_limit = np.nan
            passes_consistency = True

        passed = passes_target and passes_dd and passes_daily and passes_consistency
        if passed:
            status = "PASS"
        elif not passes_dd:
            status = "FAIL_DRAWDOWN"
        elif not passes_daily:
            status = "FAIL_DAILY_LOSS"
        elif not passes_target:
            status = "FAIL_TARGET"
        else:
            status = "FAIL_CONSISTENCY"

        records.append(
            {
                "Start": start_date,
                "End": end_date,
                "Days Tested": int(len(window)),
                "Status": status,
                "Passed": passed,
                "Target Hit": target_hit,
                "Days to Target": days_to_target,
                "P&L at Stop/End": eval_net,
                "Max Drawdown": eval_max_dd,
                "Worst Daily Loss": worst_daily_loss,
                "Biggest Winning Day": biggest_winning_day,
                "Consistency Limit": consistency_limit,
            }
        )

    result = pd.DataFrame(records)
    if result.empty:
        return result, {}

    passed_rows = result[result["Passed"]]
    summary = {
        "windows": int(len(result)),
        "passed": int(result["Passed"].sum()),
        "pass_rate": float(result["Passed"].mean() * 100),
        "failed_drawdown": int((result["Status"] == "FAIL_DRAWDOWN").sum()),
        "failed_target": int((result["Status"] == "FAIL_TARGET").sum()),
        "failed_daily": int((result["Status"] == "FAIL_DAILY_LOSS").sum()),
        "failed_consistency": int((result["Status"] == "FAIL_CONSISTENCY").sum()),
        "avg_days_to_target": float(passed_rows["Days to Target"].mean()) if len(passed_rows) else np.nan,
        "best_window_pnl": float(result["P&L at Stop/End"].max()),
        "worst_window_pnl": float(result["P&L at Stop/End"].min()),
        "worst_window_dd": float(result["Max Drawdown"].max()),
    }
    return result, summary


def style_status(status: str):
    if status == "PASS":
        return "✅ PASS"
    if status == "FAIL_DRAWDOWN":
        return "❌ Drawdown"
    if status == "FAIL_TARGET":
        return "⚠️ Target"
    if status == "FAIL_DAILY_LOSS":
        return "❌ Daily loss"
    if status == "FAIL_CONSISTENCY":
        return "⚠️ Consistency"
    return status


# -----------------------------
# App UI
# -----------------------------

st.markdown("""
<div class="hero">
  <div class="hero-kicker">TradingView CSV → funded evaluation answer</div>
  <div class="hero-title">Funded Strategy Analyzer V4</div>
  <div class="hero-subtitle">Upload a strategy trade list and instantly check profit target, drawdown, consistency, and rolling 30-day pass rate. Cleaner layout, same simple workflow.</div>
  <div class="hero-chips">
    <span class="chip">Rolling 30D simulator</span>
    <span class="chip">Drawdown safety goal</span>
    <span class="chip">Version comparison</span>
    <span class="chip">TradingView exit-row fix</span>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Funded Rules")
    profit_target = st.number_input("Profit target", value=9000.0, step=100.0)
    max_total_drawdown_limit = st.number_input("Max total drawdown allowed", value=4500.0, step=50.0)
    max_daily_loss_limit = st.number_input("Max daily loss allowed", value=999999.0, step=50.0)

    st.markdown("### Safety Goal")
    personal_safe_dd = st.number_input(
        "Personal max drawdown goal",
        value=3500.0,
        step=50.0,
        help="This is stricter than the official rule. It helps show if a strategy has a real cushion.",
    )

    st.markdown("### Rolling Test")
    rolling_window_days = st.number_input("Evaluation window days", value=30, min_value=5, max_value=120, step=1)
    stop_when_target_hit = st.checkbox("Assume you stop trading after target is hit", value=True)

    st.markdown("### Consistency Rule")
    use_consistency_rule = st.checkbox("Use consistency rule", value=True)
    consistency_percent = st.number_input(
        "Max % of profit from biggest winning day",
        value=50.0,
        min_value=1.0,
        max_value=100.0,
        step=1.0,
    )

    st.markdown("### Realism Adjustments")
    commission_per_trade = st.number_input("Extra commission per closed trade", value=1.50, step=0.25)
    slippage_per_trade = st.number_input("Extra slippage estimate per closed trade", value=2.00, step=0.25)
    st.caption("Set both to 0 if you want to match TradingView exactly.")

    st.markdown("### Optional")
    starting_balance = st.number_input("Starting balance", value=150000.0, step=1000.0)

uploaded_file = st.file_uploader("Upload your TradingView CSV", type=["csv"], label_visibility="visible")

if uploaded_file is None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="mini-card"><div class="mini-title">1. Export trades</div><div class="mini-text">TradingView Strategy Tester → List of Trades → export CSV.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="mini-card"><div class="mini-title">2. Upload here</div><div class="mini-text">The app removes TradingView entry-row double counting automatically.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="mini-card"><div class="mini-title">3. Pick the best version</div><div class="mini-text">Check rolling pass rate, drawdown cushion, and save versions to compare.</div></div>', unsafe_allow_html=True)
    st.stop()

try:
    raw_df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

if raw_df.empty:
    st.error("The CSV loaded, but it has no rows.")
    st.stop()

profit_guess, date_guess, side_guess = detect_columns(raw_df)
cols = list(raw_df.columns)
none_option = "None"

with st.expander("CSV settings", expanded=True):
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

    auto_exit_filter = st.checkbox(
        "TradingView export fix: use Exit rows only",
        value=True,
        help="TradingView often exports Entry and Exit rows. This prevents double-counting.",
    )

if "trade number" in normalize_name(profit_col) or normalize_name(profit_col) in {"trade", "trade no", "trade number"}:
    st.error("The P&L column is set to Trade number. Choose Net PnL USD, Profit, or another actual P&L column.")
    st.stop()

# -----------------------------
# Prepare data
# -----------------------------

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

cost_per_closed_trade = commission_per_trade + slippage_per_trade
trades["Adjusted Profit"] = trades["Raw Profit"] - cost_per_closed_trade
trades = trades.reset_index(drop=True)
trades["Trade #"] = trades.index + 1
trades["Cumulative P&L"] = trades["Adjusted Profit"].cumsum()
trades["Raw Cumulative P&L"] = trades["Raw Profit"].cumsum()
trades["Equity"] = starting_balance + trades["Cumulative P&L"]

profits = trades["Adjusted Profit"]
raw_profits = trades["Raw Profit"]

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
max_dd, dd_series = drawdown_from_cumulative(trades["Cumulative P&L"])
loss_streak = longest_losing_streak(profits)
trades["Drawdown"] = dd_series

worst_dd_date = "—"
if trades["Datetime"].notna().any() and len(trades):
    worst_dd_idx = trades["Drawdown"].idxmax()
    worst_dd_date = str(trades.loc[worst_dd_idx, "Datetime"])

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

passes_profit_target = net_profit >= profit_target
passes_total_dd = max_dd <= max_total_drawdown_limit
passes_safe_dd = max_dd <= personal_safe_dd
passes_daily_loss = max_daily_loss_actual <= max_daily_loss_limit if len(daily_pnl) else True

if use_consistency_rule and len(daily_pnl) and net_profit > 0:
    consistency_limit_dollars = net_profit * (consistency_percent / 100)
    passes_consistency = biggest_winning_day <= consistency_limit_dollars
else:
    consistency_limit_dollars = np.nan
    passes_consistency = True

passes_rules = passes_profit_target and passes_total_dd and passes_daily_loss and passes_consistency

rolling_df, rolling_summary = run_rolling_eval(
    daily_pnl=daily_pnl,
    profit_target=profit_target,
    max_drawdown_limit=max_total_drawdown_limit,
    max_daily_loss_limit=max_daily_loss_limit,
    use_consistency_rule=use_consistency_rule,
    consistency_percent=consistency_percent,
    window_days=int(rolling_window_days),
    stop_when_target_hit=stop_when_target_hit,
)
rolling_pass_rate = rolling_summary.get("pass_rate") if rolling_summary else None

metrics = {
    "net_profit": net_profit,
    "profit_factor": profit_factor,
    "win_rate": win_rate,
    "avg_trade": avg_trade,
    "max_drawdown": max_dd,
}
score, grade = calc_grade(metrics, passes_rules, rolling_pass_rate, passes_safe_dd)

# -----------------------------
# Clean results UI
# -----------------------------

if passes_rules and passes_safe_dd:
    st.markdown('<div class="verdict-card verdict-pass">✅ Verdict: passes the entered rules and stays under your personal drawdown goal.</div>', unsafe_allow_html=True)
elif passes_rules:
    st.markdown('<div class="verdict-card verdict-warn">⚠️ Verdict: passes the official rules, but drawdown is above your personal safety goal.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="verdict-card verdict-fail">❌ Verdict: fails at least one funded-rule check.</div>', unsafe_allow_html=True)

# Compact top metrics
st.subheader("Quick Overview")
o1, o2, o3, o4 = st.columns(4)
o1.metric("Score", f"{score}/100", grade)
o2.metric("Funded Check", "PASS" if passes_rules else "FAIL")
o3.metric("Adjusted Profit", format_money(net_profit))
o4.metric("Max Drawdown", format_money(max_dd))

o5, o6, o7, o8 = st.columns(4)
o5.metric("Profit Factor", format_number(profit_factor))
o6.metric("Win Rate", f"{win_rate:.1f}%")
o7.metric("Closed Trades", f"{total_trades:,}")
o8.metric("Profit / Month", format_money(profit_per_month) if profit_per_month is not None else "No date")

st.divider()

tab_overview, tab_rolling, tab_compare, tab_charts, tab_data = st.tabs(
    ["✅ Rules", "📆 Rolling 30-Day", "🧪 Compare", "📈 Charts", "📄 Data"]
)

with tab_overview:
    st.subheader("Backtest Period")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Start", str(start_dt.date()) if start_dt is not None else "No date")
    p2.metric("End", str(end_dt.date()) if end_dt is not None else "No date")
    p3.metric("Calendar Days", f"{calendar_days:,}" if calendar_days is not None else "No date")
    p4.metric("Trades / Active Day", f"{trades_per_active_day:.2f}" if trades_per_active_day is not None else "No date")

    st.subheader("Funded Rule Check")
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Profit Target", "PASS" if passes_profit_target else "FAIL", f"Need {format_money(profit_target)}")
    r2.metric("Official DD", "PASS" if passes_total_dd else "FAIL", f"Limit {format_money(max_total_drawdown_limit)}")
    r3.metric("Safety DD", "PASS" if passes_safe_dd else "CLOSE", f"Goal {format_money(personal_safe_dd)}")
    r4.metric("Daily Loss", "PASS" if passes_daily_loss else "FAIL", f"Limit {format_money(max_daily_loss_limit)}")
    r5.metric(
        "Consistency",
        "PASS" if passes_consistency else "FAIL",
        f"Biggest day {format_money(biggest_winning_day)}" if use_consistency_rule and len(daily_pnl) else "Not checked",
    )

    st.subheader("Main Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Raw Net P&L", format_money(raw_net_profit))
    m2.metric("Extra Costs", format_money(total_extra_costs))
    m3.metric("Avg Trade", format_money(avg_trade))
    m4.metric("Worst DD Time", worst_dd_date[:19] if worst_dd_date != "—" else "—")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Biggest Win", format_money(biggest_win))
    m6.metric("Biggest Loss", format_money(biggest_loss))
    m7.metric("Longest Losing Streak", str(loss_streak))
    m8.metric("Worst Daily Loss", format_money(max_daily_loss_actual) if len(daily_pnl) else "No date")

    with st.expander("Data check"):
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Original CSV Rows", f"{raw_row_count:,}")
        d2.metric("Rows Used", f"{total_trades:,}")
        d3.metric("Entry Rows Found", f"{entry_rows:,}")
        d4.metric("Exit Rows Found", f"{exit_rows:,}")
        if entry_rows > 0 and exit_rows > 0 and total_trades == exit_rows:
            st.success("Entry/exit double-counting fixed: using Exit rows only.")
        elif entry_rows > 0 and exit_rows > 0 and not auto_exit_filter:
            st.warning("This looks like a TradingView entry/exit export. Turn on the Exit-row filter to avoid double-counting.")

with tab_rolling:
    st.subheader(f"Rolling {int(rolling_window_days)}-Day Evaluation Simulator")
    st.caption("This uses daily closed P&L. It estimates whether each window hits the profit target before breaking the rules.")

    if not rolling_summary:
        st.info("Rolling test needs a valid date/time column.")
    else:
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Windows Tested", f"{rolling_summary['windows']:,}")
        g2.metric("Pass Rate", f"{rolling_summary['pass_rate']:.1f}%")
        g3.metric("Passed Windows", f"{rolling_summary['passed']:,}")
        g4.metric(
            "Avg Days to Target",
            "—" if pd.isna(rolling_summary["avg_days_to_target"]) else f"{rolling_summary['avg_days_to_target']:.1f}",
        )

        g5, g6, g7, g8 = st.columns(4)
        g5.metric("Failed Drawdown", f"{rolling_summary['failed_drawdown']:,}")
        g6.metric("Failed Target", f"{rolling_summary['failed_target']:,}")
        g7.metric("Worst Window DD", format_money(rolling_summary["worst_window_dd"]))
        g8.metric("Worst Window P&L", format_money(rolling_summary["worst_window_pnl"]))

        simple_roll = rolling_df.copy()
        simple_roll["Result"] = simple_roll["Status"].apply(style_status)
        display_roll = simple_roll[
            [
                "Start",
                "End",
                "Result",
                "Days to Target",
                "P&L at Stop/End",
                "Max Drawdown",
                "Worst Daily Loss",
                "Biggest Winning Day",
            ]
        ]
        st.dataframe(
            display_roll,
            use_container_width=True,
            hide_index=True,
            column_config={
                "P&L at Stop/End": st.column_config.NumberColumn(format="$%.2f"),
                "Max Drawdown": st.column_config.NumberColumn(format="$%.2f"),
                "Worst Daily Loss": st.column_config.NumberColumn(format="$%.2f"),
                "Biggest Winning Day": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

with tab_compare:
    st.subheader("Version Comparison")
    st.caption("Test a setting, name it, save it here, then upload another CSV. It only saves during this browser session.")

    if "comparison_runs" not in st.session_state:
        st.session_state.comparison_runs = []

    default_name = f"Version {len(st.session_state.comparison_runs) + 1}"
    version_name = st.text_input("Version name", value=default_name)

    add_col, clear_col = st.columns([1, 1])
    with add_col:
        if st.button("Add current result to comparison"):
            st.session_state.comparison_runs.append(
                {
                    "Version": version_name,
                    "Period": f"{str(start_dt.date()) if start_dt is not None else '?'} to {str(end_dt.date()) if end_dt is not None else '?'}",
                    "Adjusted Profit": net_profit,
                    "Max Drawdown": max_dd,
                    "Profit Factor": profit_factor,
                    "Win Rate %": win_rate,
                    "Trades": total_trades,
                    "Funded Check": "PASS" if passes_rules else "FAIL",
                    f"Rolling {int(rolling_window_days)}D Pass %": rolling_pass_rate if rolling_pass_rate is not None else np.nan,
                    "Score": score,
                    "Grade": grade,
                }
            )
            st.success(f"Added {version_name}.")
    with clear_col:
        if st.button("Clear comparison table"):
            st.session_state.comparison_runs = []
            st.info("Comparison table cleared.")

    if st.session_state.comparison_runs:
        compare_df = pd.DataFrame(st.session_state.comparison_runs)
        st.dataframe(
            compare_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Adjusted Profit": st.column_config.NumberColumn(format="$%.2f"),
                "Max Drawdown": st.column_config.NumberColumn(format="$%.2f"),
                "Profit Factor": st.column_config.NumberColumn(format="%.2f"),
                "Win Rate %": st.column_config.NumberColumn(format="%.1f%%"),
                f"Rolling {int(rolling_window_days)}D Pass %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )
        st.download_button(
            "Download comparison CSV",
            compare_df.to_csv(index=False).encode("utf-8"),
            "strategy_comparison.csv",
            "text/csv",
        )
    else:
        st.info("No saved versions yet. Upload/test a CSV, name it, then click Add current result.")

with tab_charts:
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

with tab_data:
    st.subheader("Cleaned Trade Data")
    show_cols = ["Trade #", "Raw Profit", "Adjusted Profit", "Cumulative P&L", "Drawdown", "Datetime", "Side"]
    st.dataframe(trades[show_cols], use_container_width=True)

    csv_output = trades.to_csv(index=False).encode("utf-8")
    st.download_button("Download cleaned results", csv_output, "cleaned_strategy_results_v3.csv", "text/csv")

    if not rolling_df.empty:
        st.download_button(
            "Download rolling test CSV",
            rolling_df.to_csv(index=False).encode("utf-8"),
            "rolling_30_day_results.csv",
            "text/csv",
        )
