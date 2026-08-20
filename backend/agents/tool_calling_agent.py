"""
Tool Calling Agent
------------------
Uses the LLM for autonomous tool selection when available.

If the LLM/API is unavailable (for example, insufficient quota),
the agent automatically switches to deterministic local tools.
"""

import json
from langchain_core.messages import HumanMessage, ToolMessage

from ..llm import llm
from ..tool_definitions import ALL_TOOLS


# Bind tools to the LLM
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Tool lookup
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def _direct_compliance(risk_score, allocation, age):
    """
    Deterministic compliance fallback.
    Does not require OpenAI.
    """

    stocks = allocation.get("Stocks", 0)
    bonds = allocation.get("Bonds", 0)
    cash = allocation.get("Cash", 0)

    total = stocks + bonds + cash

    if total != 100:
        return {
            "status": "Not Compliant",
            "reason": "Portfolio allocation must total 100%.",
            "suggestion": "Adjust Stocks, Bonds and Cash so the total equals 100%."
        }

    if age < 25 and stocks <= 80:
        status = "Compliant"
        reason = "The allocation is within the configured risk guidelines."
        suggestion = "No correction required."
    elif age >= 60 and stocks <= 60:
        status = "Compliant"
        reason = "The allocation provides a relatively conservative equity exposure for the investor age."
        suggestion = "No correction required."
    elif age >= 60 and stocks > 60:
        status = "Not Compliant"
        reason = "Equity exposure is relatively high for the investor age."
        suggestion = "Consider reducing Stocks and increasing Bonds/Cash."
    else:
        status = "Compliant"
        reason = "The allocation is within the configured portfolio rules."
        suggestion = "No correction required."

    return {
        "status": status,
        "reason": reason,
        "suggestion": suggestion
    }


def _run_tools_directly(profile: dict, logs: list) -> dict:
    """
    Deterministic fallback when OpenAI is unavailable.

    Uses local tools directly and does not require an LLM.
    """

    logs.append(
        "Tool Calling Agent: OpenAI unavailable — using deterministic fallback."
    )

    results = {}

    # --------------------------------------------------
    # 1. Risk Score
    # --------------------------------------------------

    logs.append(
        "Tool Calling Agent: → calculating risk score locally"
    )

    r1 = TOOL_MAP["tool_calculate_risk_score"].invoke({
        "age": profile.get("age", 30),
        "income": profile.get("income", 500000),
        "years": profile.get("years", 10),
        "loss": profile.get("loss", 5)
    })

    results["risk_score"] = r1.get("risk_score")

    logs.append(
        f"Tool Calling Agent: ← risk_score = {results['risk_score']}"
    )

    # --------------------------------------------------
    # 2. Allocation
    # --------------------------------------------------

    logs.append(
        "Tool Calling Agent: → calculating allocation locally"
    )

    allocation = TOOL_MAP["tool_compute_allocation"].invoke({
        "risk_score": results["risk_score"]
    })

    results["allocation"] = allocation

    logs.append(
        f"Tool Calling Agent: ← allocation = {allocation}"
    )

    # --------------------------------------------------
    # 3. Live NIFTY
    # --------------------------------------------------

    logs.append(
        "Tool Calling Agent: → fetching NIFTY data"
    )

    try:
        r3 = TOOL_MAP["tool_fetch_live_nifty"].invoke({})

        results["live_nifty_return"] = r3.get("live_return")

        logs.append(
            f"Tool Calling Agent: ← live_return = "
            f"{results['live_nifty_return']} "
            f"({r3.get('source')})"
        )

    except Exception as e:
        results["live_nifty_return"] = None

        logs.append(
            f"Tool Calling Agent: NIFTY unavailable — {e}"
        )

    # --------------------------------------------------
    # 4. Simulation
    # --------------------------------------------------

    logs.append(
        "Tool Calling Agent: → running Monte Carlo simulation locally"
    )

    alloc = results["allocation"]

    r4 = TOOL_MAP["tool_run_simulation"].invoke({
        "stocks_pct": alloc.get("Stocks", 55),
        "bonds_pct": alloc.get("Bonds", 30),
        "cash_pct": alloc.get("Cash", 15),
        "amount": profile.get("amount", 100000),
        "live_nifty_return": results["live_nifty_return"]
    })

    results["stress_test"] = r4

    logs.append(
        "Tool Calling Agent: ← Monte Carlo simulation completed"
    )

    # --------------------------------------------------
    # 5. Compliance — LOCAL FALLBACK
    # --------------------------------------------------

    compliance_result = _direct_compliance(
        results["risk_score"],
        allocation,
        profile.get("age", 30)
    )

    results["compliance_review"] = (
        f"STATUS: {compliance_result['status']}\n"
        f"REASON: {compliance_result['reason']}\n"
        f"SUGGESTION: {compliance_result['suggestion']}"
    )

    logs.append(
        "Tool Calling Agent: ← compliance check completed locally"
    )

    logs.append(
        "Tool Calling Agent: Deterministic fallback completed."
    )

    return results


def tool_calling_agent(state: dict) -> dict:

    profile = state.get("profile", {})
    logs = state.get("logs", [])

    logs.append(
        "Tool Calling Agent: Starting autonomous tool selection..."
    )

    # --------------------------------------------------
    # Try OpenAI first
    # --------------------------------------------------

    try:

        prompt = f"""
You are an autonomous financial portfolio AI.

You have access to these tools:

- tool_calculate_risk_score
- tool_compute_allocation
- tool_fetch_live_nifty
- tool_run_simulation
- tool_check_compliance

Given this investor profile, call the tools in the correct order
to build a complete portfolio analysis.

You MUST call all relevant tools.

Investor Profile:
{json.dumps(profile, indent=2)}
"""

        messages = [HumanMessage(content=prompt)]

        risk_score = None
        allocation = None
        live_return = None
        stress_test = None
        compliance = None

        for iteration in range(10):

            response = llm_with_tools.invoke(messages)

            messages.append(response)

            if not response.tool_calls:

                logs.append(
                    f"Tool Calling Agent: LLM completed after "
                    f"{iteration + 1} turn(s)."
                )

                break

            for tc in response.tool_calls:

                name = tc["name"]
                args = tc["args"]
                tool_id = tc["id"]

                logs.append(
                    f"Tool Calling Agent: → calling '{name}'"
                )

                if name not in TOOL_MAP:

                    result = {
                        "error": f"Unknown tool: {name}"
                    }

                else:

                    try:
                        result = TOOL_MAP[name].invoke(args)

                    except Exception as e:

                        result = {
                            "error": str(e)
                        }

                logs.append(
                    f"Tool Calling Agent: ← '{name}' returned"
                )

                if (
                    name == "tool_calculate_risk_score"
                    and "error" not in result
                ):
                    risk_score = result.get("risk_score")

                elif (
                    name == "tool_compute_allocation"
                    and "error" not in result
                ):
                    allocation = result

                elif (
                    name == "tool_fetch_live_nifty"
                    and "error" not in result
                ):
                    live_return = result.get("live_return")

                elif (
                    name == "tool_run_simulation"
                    and "error" not in result
                ):
                    stress_test = result

                elif (
                    name == "tool_check_compliance"
                    and "error" not in result
                ):
                    compliance = (
                        f"STATUS: {result.get('status', '')}\n"
                        f"REASON: {result.get('reason', '')}\n"
                        f"SUGGESTION: {result.get('suggestion', '')}"
                    )

                messages.append(
                    ToolMessage(
                        content=json.dumps(result),
                        tool_call_id=tool_id
                    )
                )

        if risk_score is not None:
            state["risk_score"] = risk_score

        if allocation is not None:
            state["allocation"] = allocation

        if live_return is not None:
            state["live_nifty_return"] = live_return

        if stress_test is not None:
            state["stress_test"] = stress_test

        if compliance is not None:
            state["compliance_review"] = compliance

        logs.append(
            "Tool Calling Agent: LLM-driven tool calling complete."
        )

    # --------------------------------------------------
    # OpenAI unavailable → local fallback
    # --------------------------------------------------

    except Exception as e:

        logs.append(
            f"Tool Calling Agent: OpenAI unavailable ({e})"
        )

        logs.append(
            "Tool Calling Agent: Switching to deterministic fallback."
        )

        fallback = _run_tools_directly(
            profile,
            logs
        )

        if fallback.get("risk_score") is not None:
            state["risk_score"] = fallback["risk_score"]

        if fallback.get("allocation") is not None:
            state["allocation"] = fallback["allocation"]

        if fallback.get("live_nifty_return") is not None:
            state["live_nifty_return"] = (
                fallback["live_nifty_return"]
            )

        if fallback.get("stress_test") is not None:
            state["stress_test"] = fallback["stress_test"]

        if fallback.get("compliance_review") is not None:
            state["compliance_review"] = (
                fallback["compliance_review"]
            )

    state["logs"] = logs

    logs.append(
        "Tool Calling Agent: State fully updated."
    )

    return state