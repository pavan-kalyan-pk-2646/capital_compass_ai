from backend.llm import generate_response

def explanation_agent(state):

    # Skip-if-set guard — consistent with all other agents
    if state.get("explanation"):
        state["logs"].append("Explanation Agent: explanation already set, skipping.")
        return state

    prompt = f"""
You are a professional financial advisor.

Risk Score: {state['risk_score']}
Allocation: {state['allocation']}

Explain in under 120 words why this portfolio matches the risk level.
Be concise and professional.
"""

    explanation = generate_response(prompt)

    state["explanation"] = explanation
    state["logs"].append("Explanation Agent generated reasoning.")

    return state