from backend.llm import generate_response


def _fallback_explanation(state):

    risk_score = state.get("risk_score", 0)
    allocation = state.get("allocation", {})

    stocks = allocation.get("Stocks", 0)
    bonds = allocation.get("Bonds", 0)
    cash = allocation.get("Cash", 0)

    if risk_score <= 30:
        risk_level = "conservative"

    elif risk_score <= 60:
        risk_level = "moderate"

    else:
        risk_level = "growth-oriented"

    return (
        f"This portfolio follows a {risk_level} risk strategy "
        f"with {stocks}% Stocks, {bonds}% Bonds and {cash}% Cash. "
        f"The allocation is designed to balance growth potential "
        f"with risk management based on the investor's calculated "
        f"risk score of {risk_score}."
    )


def explanation_agent(state):

    # Skip if explanation already exists
    if state.get("explanation"):

        state["logs"].append(
            "Explanation Agent: explanation already set, skipping."
        )

        return state

    prompt = f"""
You are a professional financial advisor.

Risk Score:
{state['risk_score']}

Allocation:
{state['allocation']}

Explain in under 120 words why this portfolio matches the risk level.

Be concise and professional.
"""

    # --------------------------------------------------
    # Try OpenAI
    # --------------------------------------------------

    try:

        explanation = generate_response(prompt)

        if not explanation:

            raise ValueError(
                "Empty response received from AI."
            )

        state["explanation"] = explanation

        state["logs"].append(
            "Explanation Agent generated AI reasoning."
        )

    # --------------------------------------------------
    # OpenAI unavailable → local fallback
    # --------------------------------------------------

    except Exception as e:

        state["explanation"] = _fallback_explanation(
            state
        )

        state["logs"].append(
            f"Explanation Agent: AI unavailable ({e}). "
            "Used deterministic explanation fallback."
        )

    return state