from backend.rag.compliance_rag import build_compliance_rag
from backend.llm import llm

# Fix — build_compliance_rag() used to run at import time, which meant a
# single Chroma/embeddings failure would crash the entire Flask app on
# startup (every route, not just this agent). Load it lazily on first use
# instead, and cache it in-process afterward.
_vectordb = None


def _get_vectordb():
    global _vectordb
    if _vectordb is None:
        _vectordb = build_compliance_rag()
    return _vectordb


def compliance_agent(state):

    try:
        # Fix — skip if tool_calling_agent already ran compliance
        if state.get("compliance_review"):
            state["logs"].append("Compliance Agent: compliance_review already set, skipping.")
            return state

        risk_score = state.get("risk_score")
        allocation = state.get("allocation")
        profile    = state.get("profile", {})
        age        = profile.get("age")

        if not allocation:
            state["compliance_review"] = "Compliance skipped: No allocation generated."
            state["logs"].append("Compliance skipped (no allocation).")
            return state

        query = f"""
        Risk Score: {risk_score}
        Allocation: {allocation}
        Age: {age}
        """

        docs    = _get_vectordb().similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        prompt = f"""
        You are a financial compliance auditor.

        Regulatory Guidelines:
        {context}

        Portfolio Allocation:
        {allocation}

        Investor Age: {age}
        Risk Score: {risk_score}

        Respond in this exact format:

        STATUS: Compliant or Not Compliant
        REASON: Short explanation
        SUGGESTION: If not compliant, provide corrected allocation.
        """

        response = llm.invoke(prompt)

        state["compliance_review"] = response.content.strip()
        state["logs"].append("Compliance Agent performed regulatory validation.")

        return state

    except Exception as e:
        state["compliance_review"] = "Compliance check failed."
        state["logs"].append(f"Compliance error: {str(e)}")
        return state