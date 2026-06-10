import os
import numpy as np
import pandas as pd

# Dynamically resolve path to data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # → backend/agents/
DATA_DIR = os.path.join(BASE_DIR, "../data")            # → backend/data/

# Fix — load CSVs ONCE at module import, not on every request
_equity_returns = pd.read_csv(os.path.join(DATA_DIR, "nifty_annual_returns.csv"))["Return"].values
_bond_returns   = pd.read_csv(os.path.join(DATA_DIR, "bond_annual_returns.csv"))["Return"].values


def simulation_agent(state):

    # Fix — skip if tool_calling_agent already ran the simulation
    if state.get("stress_test"):
        state["logs"].append("Simulation Agent: stress_test already set, skipping.")
        return state

    allocation = state.get("allocation")
    profile    = state.get("profile", {})
    amount     = profile.get("amount", 0)

    # Use live NIFTY return from live_data_agent if available
    live_return = state.get("live_nifty_return")

    simulations = []

    for _ in range(1000):

        # If live return fetched successfully, use it; otherwise pick from historical CSV
        stock_return = live_return if live_return is not None else float(np.random.choice(_equity_returns))
        bond_return  = float(np.random.choice(_bond_returns))
        cash_return  = 0.03  # 3% fixed

        portfolio_return = (
            (allocation["Stocks"] / 100) * stock_return +
            (allocation["Bonds"]  / 100) * bond_return  +
            (allocation["Cash"]   / 100) * cash_return
        )

        simulations.append(amount * (1 + portfolio_return))

    state["stress_test"] = {
        "Expected Value": float(np.mean(simulations)),
        "Worst 5% Case":  float(np.percentile(simulations, 5)),
        "Best 5% Case":   float(np.percentile(simulations, 95))
    }

    source = "live NIFTY data" if live_return is not None else "historical CSV data"
    state["logs"].append(f"Simulation Agent: Monte Carlo ran using {source}.")

    return state