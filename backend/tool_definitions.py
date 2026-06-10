import os
import numpy as np
import pandas as pd
import yfinance as yf
from langchain_core.tools import tool

# Path: backend/tool_definitions.py  →  backend/data/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # → backend/
DATA_DIR = os.path.join(BASE_DIR, "data")               # → backend/data/

# Load CSV data ONCE at module import — avoids disk reads on every simulation call
_equity_returns = pd.read_csv(os.path.join(DATA_DIR, "nifty_annual_returns.csv"))["Return"].values
_bond_returns   = pd.read_csv(os.path.join(DATA_DIR, "bond_annual_returns.csv"))["Return"].values


# ──────────────────────────────────────────────
# TOOL 1: Calculate Risk Score
# ──────────────────────────────────────────────
@tool
def tool_calculate_risk_score(age: int, income: float, years: int, loss: int) -> dict:
    """
    Calculate a risk score (0-100) for an investor based on their profile.
    Use this when you need to assess how much risk an investor can handle.

    Args:
        age:    Investor's age in years
        income: Annual income in rupees
        years:  Investment horizon in years
        loss:   Risk tolerance on a scale of 1 to 10

    Returns:
        Dictionary with risk_score (int) and risk_label (str)
    """
    age_score       = max(0, 100 - age)
    income_score    = min(100, income / 1000)
    horizon_score   = min(100, years * 5)
    tolerance_score = loss * 10

    risk_score = int(min(100, (
        age_score       * 0.2 +
        income_score    * 0.2 +
        horizon_score   * 0.3 +
        tolerance_score * 0.3
    )))

    label = "High Risk" if risk_score > 70 else "Moderate Risk" if risk_score > 40 else "Conservative"
    return {"risk_score": risk_score, "risk_label": label}


# ──────────────────────────────────────────────
# TOOL 2: Compute Allocation
# ──────────────────────────────────────────────
@tool
def tool_compute_allocation(risk_score: int) -> dict:
    """
    Compute the optimal portfolio allocation (Stocks, Bonds, Cash) based on risk score.
    Use this after calculating the risk score to generate an investment strategy.

    Args:
        risk_score: Integer between 0 and 100 representing investor risk level

    Returns:
        Dictionary with Stocks (%), Bonds (%), Cash (%) allocations
    """
    if risk_score > 75:
        return {"Stocks": 80, "Bonds": 15, "Cash": 5}
    elif risk_score > 45:
        return {"Stocks": 55, "Bonds": 30, "Cash": 15}
    else:
        return {"Stocks": 30, "Bonds": 45, "Cash": 25}


# ──────────────────────────────────────────────
# TOOL 3: Fetch Live NIFTY Return
# ──────────────────────────────────────────────
@tool
def tool_fetch_live_nifty() -> dict:
    """
    Fetch the live annualized NIFTY 50 return from Yahoo Finance.
    Use this to get real-time market data before running simulations.
    Falls back to a safe default if network is unavailable.

    Returns:
        Dictionary with live_return (float) and source (str)
    """
    try:
        nifty = yf.Ticker("^NSEI")
        hist  = nifty.history(period="1y")
        if hist.empty:
            raise ValueError("Empty data from yfinance")
        live_return = float(hist["Close"].pct_change().mean() * 252)
        return {"live_return": round(live_return, 4), "source": "Yahoo Finance (live)"}
    except Exception as e:
        return {"live_return": 0.12, "source": f"Fallback default (error: {str(e)})"}


# ──────────────────────────────────────────────
# TOOL 4: Run Monte Carlo Simulation
# ──────────────────────────────────────────────
@tool
def tool_run_simulation(stocks_pct: float, bonds_pct: float, cash_pct: float,
                        amount: float, live_nifty_return: float = None) -> dict:
    """
    Run a 1000-iteration Monte Carlo simulation to project portfolio performance.
    Use this to stress-test the portfolio allocation and compute outcome probabilities.

    Args:
        stocks_pct:         Percentage allocation to stocks (e.g. 55)
        bonds_pct:          Percentage allocation to bonds (e.g. 30)
        cash_pct:           Percentage allocation to cash (e.g. 15)
        amount:             Total investment amount in rupees
        live_nifty_return:  Optional live NIFTY return. If None, uses historical CSV.

    Returns:
        Dictionary with Expected Value, Worst 5% Case, Best 5% Case
    """
    try:
        # Use module-level arrays loaded once at startup
        equity_returns = _equity_returns
        bond_returns   = _bond_returns

        simulations = []
        for _ in range(1000):
            stock_r = live_nifty_return if live_nifty_return is not None else float(np.random.choice(equity_returns))
            bond_r  = float(np.random.choice(bond_returns))
            cash_r  = 0.03
            port_r  = (stocks_pct/100)*stock_r + (bonds_pct/100)*bond_r + (cash_pct/100)*cash_r
            simulations.append(amount * (1 + port_r))

        return {
            "Expected Value":  round(float(np.mean(simulations)), 2),
            "Worst 5% Case":   round(float(np.percentile(simulations, 5)), 2),
            "Best 5% Case":    round(float(np.percentile(simulations, 95)), 2)
        }
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
# TOOL 5: Check Compliance
# ──────────────────────────────────────────────
@tool
def tool_check_compliance(risk_score: int, stocks_pct: float,
                          bonds_pct: float, cash_pct: float, age: int) -> dict:
    """
    Check whether a portfolio allocation is compliant with regulatory guidelines.
    Use this to validate the strategy matches investor age and risk profile.

    Args:
        risk_score:  Investor risk score (0-100)
        stocks_pct:  Percentage in stocks
        bonds_pct:   Percentage in bonds
        cash_pct:    Percentage in cash
        age:         Investor age

    Returns:
        Dictionary with status, reason, and suggestion
    """
    issues = []

    if age > 60 and stocks_pct > 40:
        issues.append(f"Investor is {age} years old but has {stocks_pct}% in stocks — exceeds 40% limit for age > 60.")
    if risk_score > 70 and stocks_pct < 50:
        issues.append(f"High risk score ({risk_score}) but stocks ({stocks_pct}%) below 50%.")
    if risk_score < 40 and stocks_pct > 50:
        issues.append(f"Low risk score ({risk_score}) but stocks ({stocks_pct}%) exceeds 50%.")
    if cash_pct > 40:
        issues.append(f"Cash allocation ({cash_pct}%) is too high — capital underutilised.")

    if issues:
        return {
            "status":     "Not Compliant",
            "reason":     " | ".join(issues),
            "suggestion": "Rebalance portfolio to match risk profile and age-based guidelines."
        }
    return {
        "status":     "Compliant",
        "reason":     "Portfolio meets all regulatory guidelines for this investor profile.",
        "suggestion": "No changes needed."
    }


# ──────────────────────────────────────────────
# Export all tools as a list
# ──────────────────────────────────────────────
ALL_TOOLS = [
    tool_calculate_risk_score,
    tool_compute_allocation,
    tool_fetch_live_nifty,
    tool_run_simulation,
    tool_check_compliance,
]