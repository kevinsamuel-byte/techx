from datetime import datetime, timezone


AGENT_SYSTEM_PROMPT = """
You are the decision-making layer of an execution-first career system.
You must create adaptive plans, tasks, and updates tied to measurable outcomes.
Always produce concise structured reasoning summaries.
""".strip()

CHAT_SYSTEM_PROMPT = """
You are the communication layer. You explain and negotiate, but do not make planning decisions.
When user disputes a task, log the dispute and request replanning from the agent controller.
""".strip()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_reasoning(decision: str, rationale: str, evidence: list[str] | None = None) -> dict:
    return {
        "timestamp": utc_now_iso(),
        "decision": decision,
        "rationale": rationale,
        "evidence": evidence or [],
    }
