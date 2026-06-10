"""
tool_calling_agent.py
----------------------
LangChain-powered agent using bind_tools() so the LLM autonomously decides
which tools to call and in what order.

Place this file at:  backend/agents/tool_calling_agent.py
"""

import json
from langchain_core.messages import HumanMessage, ToolMessage

# Use relative imports — this file lives inside backend/agents/
from ..llm import llm
from ..tool_definitions import ALL_TOOLS

# Bind all 5 tools to the LLM — now it knows what it can call
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Quick lookup: tool_name → callable
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def _run_tools_directly(profile: dict, logs: list) -> dict:
    """
    Fallback: when the LLM doesn't support bind_tools(),
    we directly invoke all 5 tools in the correct order.
    This preserves the full tool-calling pipeline — only the
    LLM decision layer is bypassed.
    """
    logs.append("Tool Calling Agent: LLM does not support tools — running direct tool execution fallback.")

    results = {}

    # Tool 1 — Risk Score
    logs.append("Tool Calling Agent: → calling 'tool_calculate_risk_score'")
    r1 = TOOL_MAP["tool_calculate_risk_score"].invoke({
        "age":    profile.get("age", 30),
        "income": profile.get("income", 500000),
        "years":  profile.get("years", 10),
        "loss":   profile.get("loss", 5)
    })
    logs.append(f"Tool Calling Agent: ← risk_score = {r1.get('risk_score')}")
    results["risk_score"] = r1.get("risk_score")

    # Tool 2 — Allocation
    logs.append("Tool Calling Agent: → calling 'tool_compute_allocation'")
    r2 = TOOL_MAP["tool_compute_allocation"].invoke({"risk_score": results["risk_score"]})
    logs.append(f"Tool Calling Agent: ← allocation = {r2}")
    results["allocation"] = r2

    # Tool 3 — Live NIFTY
    logs.append("Tool Calling Agent: → calling 'tool_fetch_live_nifty'")
    r3 = TOOL_MAP["tool_fetch_live_nifty"].invoke({})
    logs.append(f"Tool Calling Agent: ← live_return = {r3.get('live_return')} ({r3.get('source')})")
    results["live_nifty_return"] = r3.get("live_return")

    # Tool 4 — Simulation
    logs.append("Tool Calling Agent: → calling 'tool_run_simulation'")
    alloc = results["allocation"]
    r4 = TOOL_MAP["tool_run_simulation"].invoke({
        "stocks_pct":         alloc.get("Stocks", 55),
        "bonds_pct":          alloc.get("Bonds", 30),
        "cash_pct":           alloc.get("Cash", 15),
        "amount":             profile.get("amount", 100000),
        "live_nifty_return":  results["live_nifty_return"]
    })
    logs.append(f"Tool Calling Agent: ← stress_test = {r4}")
    results["stress_test"] = r4

    # Tool 5 — Compliance
    logs.append("Tool Calling Agent: → calling 'tool_check_compliance'")
    r5 = TOOL_MAP["tool_check_compliance"].invoke({
        "risk_score":  results["risk_score"],
        "stocks_pct":  alloc.get("Stocks", 55),
        "bonds_pct":   alloc.get("Bonds", 30),
        "cash_pct":    alloc.get("Cash", 15),
        "age":         profile.get("age", 30)
    })
    logs.append(f"Tool Calling Agent: ← compliance = {r5.get('status')}")
    results["compliance_review"] = (
        f"STATUS: {r5.get('status', '')}\n"
        f"REASON: {r5.get('reason', '')}\n"
        f"SUGGESTION: {r5.get('suggestion', '')}"
    )

    logs.append("Tool Calling Agent: All 5 tools executed via direct fallback.")
    return results


def tool_calling_agent(state: dict) -> dict:
    """
    LLM-powered agent that autonomously:
      1. Reads the investor profile from LangGraph state
      2. Tries to use bind_tools() so the LLM decides which tools to call
      3. Falls back to direct tool execution if the LLM doesn't support tools
      4. Writes all results back into state for downstream agents
    """

    profile = state.get("profile", {})
    logs    = state.get("logs", [])

    logs.append("Tool Calling Agent: Starting autonomous tool selection...")

    # ── Try LLM-driven tool calling first ──────────────────────────────────
    try:
        prompt = f"""You are an autonomous financial portfolio AI.

You have access to these tools:
- tool_calculate_risk_score: Compute investor risk score from age, income, years, loss
- tool_compute_allocation: Generate Stocks/Bonds/Cash allocation from risk score
- tool_fetch_live_nifty: Get live NIFTY 50 annual return from Yahoo Finance
- tool_run_simulation: Run 1000 Monte Carlo simulations on the portfolio
- tool_check_compliance: Validate the portfolio against regulatory guidelines

Given this investor profile, call the tools in the correct order to build a complete portfolio analysis.
You MUST call all relevant tools. Start with tool_calculate_risk_score.

Investor Profile:
{json.dumps(profile, indent=2)}"""

        messages   = [HumanMessage(content=prompt)]
        risk_score = None
        allocation = None
        live_return = None
        stress_test = None
        compliance  = None

        for iteration in range(10):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                logs.append(f"Tool Calling Agent: LLM completed after {iteration + 1} turn(s).")
                break

            for tc in response.tool_calls:
                name    = tc["name"]
                args    = tc["args"]
                tool_id = tc["id"]

                logs.append(f"Tool Calling Agent: → calling '{name}' {args}")

                if name not in TOOL_MAP:
                    result = {"error": f"Unknown tool: {name}"}
                else:
                    try:
                        result = TOOL_MAP[name].invoke(args)
                    except Exception as e:
                        result = {"error": str(e)}

                logs.append(f"Tool Calling Agent: ← '{name}' returned {result}")

                if name == "tool_calculate_risk_score" and "error" not in result:
                    risk_score = result.get("risk_score")
                elif name == "tool_compute_allocation" and "error" not in result:
                    allocation = result
                elif name == "tool_fetch_live_nifty" and "error" not in result:
                    live_return = result.get("live_return")
                elif name == "tool_run_simulation" and "error" not in result:
                    stress_test = result
                elif name == "tool_check_compliance" and "error" not in result:
                    compliance = (
                        f"STATUS: {result.get('status', '')}\n"
                        f"REASON: {result.get('reason', '')}\n"
                        f"SUGGESTION: {result.get('suggestion', '')}"
                    )

                messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_id))

        # Write LLM-driven results to state
        if risk_score  is not None: state["risk_score"]       = risk_score
        if allocation  is not None: state["allocation"]        = allocation
        if live_return is not None: state["live_nifty_return"] = live_return
        if stress_test is not None: state["stress_test"]       = stress_test
        if compliance  is not None: state["compliance_review"] = compliance
        logs.append("Tool Calling Agent: LLM-driven tool calling complete.")

    except Exception as e:
        # ── Fallback: LLM doesn't support tools — run them directly ────────
        logs.append(f"Tool Calling Agent: bind_tools() failed ({e})")
        fallback = _run_tools_directly(profile, logs)

        if fallback.get("risk_score")       is not None: state["risk_score"]       = fallback["risk_score"]
        if fallback.get("allocation")       is not None: state["allocation"]        = fallback["allocation"]
        if fallback.get("live_nifty_return") is not None: state["live_nifty_return"] = fallback["live_nifty_return"]
        if fallback.get("stress_test")      is not None: state["stress_test"]       = fallback["stress_test"]
        if fallback.get("compliance_review") is not None: state["compliance_review"] = fallback["compliance_review"]

    state["logs"] = logs
    logs.append("Tool Calling Agent: State fully updated.")
    return state