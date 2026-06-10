from backend.tools import compute_allocation

def strategy_agent(state):

    # Fix — skip if tool_calling_agent already computed the allocation
    if state.get("allocation"):
        state["logs"].append("Strategy Agent: allocation already set, skipping.")
        return state

    allocation = compute_allocation(state["risk_score"])
    state["allocation"] = allocation
    state["logs"].append("Strategy Agent generated allocation.")

    return state