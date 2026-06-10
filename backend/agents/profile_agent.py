from backend.risk_engine import calculate_risk_score

def profile_agent(state):

    profile = state["profile"]

    risk_score = calculate_risk_score(
        profile["age"],
        profile["income"],
        profile["years"],
        profile["loss"]
    )

    state["risk_score"] = risk_score
    state["logs"].append(f"Profile Agent: Risk score calculated = {risk_score}")

    return state