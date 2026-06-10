from typing import TypedDict, Dict, Any, List, Optional

class AgentState(TypedDict, total=False):
    profile:           Dict[str, Any]
    risk_score:        int
    allocation:        Dict[str, int]
    stress_test:       Dict[str, float]
    explanation:       str
    logs:              list
    retry:             bool
    retry_count:       int
    compliance_review: str
    live_nifty_return: float
    tool_calls_made:   List[str]