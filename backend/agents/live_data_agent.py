import yfinance as yf


def live_data_agent(state):
    """
    Fetches live NIFTY 50 annual return from Yahoo Finance.
    Stores it in state so simulation_agent can use real market data.
    """

    # Fix — skip if tool_calling_agent already fetched live data
    if state.get("live_nifty_return") is not None:
        state["logs"].append("Live Data Agent: live_nifty_return already set, skipping.")
        return state

    try:
        nifty = yf.Ticker("^NSEI")
        hist  = nifty.history(period="1y")

        if hist.empty:
            raise ValueError("No data returned from yfinance.")

        # Annualized return = average daily % change * 252 trading days
        live_return = hist["Close"].pct_change().mean() * 252

        state["live_nifty_return"] = float(live_return)
        state["logs"].append(
            f"Live Data Agent: NIFTY live annual return = {live_return:.4f}"
        )

    except Exception as e:
        # Fallback: if internet is down or API fails, set None
        state["live_nifty_return"] = None
        state["logs"].append(
            f"Live Data Agent: Failed to fetch live data - {e}. Will use historical CSV."
        )

    return state