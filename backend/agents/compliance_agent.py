from backend.rag.compliance_rag import build_compliance_rag
from backend.llm import llm


_vectordb = None


def _get_vectordb():

    global _vectordb

    if _vectordb is None:
        _vectordb = build_compliance_rag()

    return _vectordb


def _fallback_compliance(risk_score, allocation, age):

    stocks = allocation.get("Stocks", 0)
    bonds = allocation.get("Bonds", 0)
    cash = allocation.get("Cash", 0)

    total = stocks + bonds + cash

    if total != 100:

        return (
            "STATUS: Not Compliant\n"
            "REASON: Portfolio allocation must total 100%.\n"
            "SUGGESTION: Adjust Stocks, Bonds and Cash so the total equals 100%."
        )

    if age >= 60 and stocks > 60:

        return (
            "STATUS: Not Compliant\n"
            "REASON: Equity exposure is relatively high for the investor age.\n"
            "SUGGESTION: Consider reducing Stocks and increasing Bonds or Cash."
        )

    return (
        "STATUS: Compliant\n"
        "REASON: The portfolio allocation is within the configured risk guidelines.\n"
        "SUGGESTION: No correction required."
    )


def compliance_agent(state):

    try:

        if state.get("compliance_review"):

            state["logs"].append(
                "Compliance Agent: compliance_review already set, skipping."
            )

            return state

        risk_score = state.get("risk_score")
        allocation = state.get("allocation")
        profile = state.get("profile", {})
        age = profile.get("age", 30)

        if not allocation:

            state["compliance_review"] = (
                "Compliance skipped: No allocation generated."
            )

            state["logs"].append(
                "Compliance skipped (no allocation)."
            )

            return state

        query = f"""
Risk Score: {risk_score}
Allocation: {allocation}
Age: {age}
"""

        # --------------------------------------------------
        # Try RAG + OpenAI
        # --------------------------------------------------

        try:

            docs = _get_vectordb().similarity_search(
                query,
                k=3
            )

            context = "\n".join(
                [doc.page_content for doc in docs]
            )

            prompt = f"""
You are a financial compliance auditor.

Regulatory Guidelines:
{context}

Portfolio Allocation:
{allocation}

Investor Age:
{age}

Risk Score:
{risk_score}

Respond in this exact format:

STATUS: Compliant or Not Compliant
REASON: Short explanation
SUGGESTION: If not compliant, provide corrected allocation.
"""

            response = llm.invoke(prompt)

            state["compliance_review"] = (
                response.content.strip()
            )

            state["logs"].append(
                "Compliance Agent performed regulatory validation using AI."
            )

            return state

        # --------------------------------------------------
        # OpenAI/RAG unavailable → local fallback
        # --------------------------------------------------

        except Exception as e:

            state["compliance_review"] = _fallback_compliance(
                risk_score,
                allocation,
                age
            )

            state["logs"].append(
                f"Compliance Agent: AI unavailable ({e}). "
                "Used deterministic compliance fallback."
            )

            return state

    except Exception as e:

        state["compliance_review"] = (
            _fallback_compliance(
                state.get("risk_score", 0),
                state.get("allocation", {}),
                state.get("profile", {}).get("age", 30)
            )
        )

        state["logs"].append(
            f"Compliance fallback activated: {e}"
        )

        return state