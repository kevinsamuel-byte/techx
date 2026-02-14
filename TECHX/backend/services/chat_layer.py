import re
from typing import Any

from .agent_layer import add_goal, mark_module_task, regenerate_resume, register_dispute, remove_module

WHY_PATTERN = re.compile(r"\b(why|reason|changed|change|explain)\b", re.IGNORECASE)
TASK_ID_PATTERN = re.compile(r"\btask\s*#?\s*(\d+)\b", re.IGNORECASE)


def _extract_task_id(message: str) -> int | None:
    match = TASK_ID_PATTERN.search(message)
    if not match:
        return None
    return int(match.group(1))


def _latest_change_explanation(state: dict[str, Any]) -> str:
    changes = state.get("change_log", [])
    if not changes:
        return "No plan changes have been logged yet."
    latest = changes[-1]
    return (
        f"Latest change ({latest['timestamp']}): action={latest['action']}, "
        f"reason={latest['reason']}."
    )


def _task_breakdown(task: dict[str, Any]) -> str:
    return (
        f"Task {task['task_id']} breakdown: 1) define output in 5 minutes, "
        f"2) execute focused work for {max(task['estimated_time'] - 10, 10)} minutes, "
        "3) finish with a 10-minute review and notes."
    )


def _next_actions(state: dict[str, Any]) -> str:
    pending = [t for t in state.get("tasks", []) if t.get("status") == "pending"][:3]
    if not pending:
        return "No pending tasks right now. Ask me to refresh the plan or submit feedback to continue the loop."
    goal = state.get("goal") or "your target role"
    task_lines = "; ".join([f"#{t['task_id']} ({t['difficulty']}) {t['title']}" for t in pending])
    return f"Your goal is {goal}. Next tasks: {task_lines}."


def _detect_module(message: str) -> str | None:
    lower = message.lower()
    for module in ["education", "softskills", "certification"]:
        if module in lower:
            return module
    if "soft skill" in lower:
        return "softskills"
    return None


def respond_to_message(state: dict[str, Any], message: str) -> dict[str, Any]:
    lower = message.lower().strip()

    if lower.startswith("add new goal") or lower.startswith("set goal"):
        goal = message.split(":", 1)[1].strip() if ":" in message else message.replace("add new goal", "").replace("set goal", "").strip()
        if goal:
            add_goal(state, goal)
            return {"reply": f"AGENT GURU updated your goal to '{goal}' and refreshed all module roadmaps."}

    if "remove" in lower and "module" in lower:
        module = _detect_module(lower)
        if module:
            remove_module(state, module)
            return {"reply": f"AGENT GURU removed the {module} module from your plan."}

    if "complete" in lower and "module" in lower:
        module = _detect_module(lower)
        task_id = _extract_task_id(lower) or 1
        if module:
            mark_module_task(state, module, task_id, True)
            return {"reply": f"Marked {module} module task #{task_id} as completed."}

    if "create new resume" in lower or "new resume" in lower:
        regenerate_resume(state, from_scratch=True)
        return {"reply": "AGENT GURU created a fresh resume draft from your current profile."}

    if "update resume" in lower or "improve resume" in lower:
        regenerate_resume(state, from_scratch=False)
        return {"reply": "AGENT GURU updated your resume with latest progress evidence."}

    if WHY_PATTERN.search(message):
        return {"reply": _latest_change_explanation(state)}

    if "break down" in lower or "confused" in lower:
        task_id = _extract_task_id(message)
        target_task = None
        if task_id is not None:
            for task in state.get("tasks", []):
                if int(task.get("task_id", -1)) == task_id:
                    target_task = task
                    break
        if not target_task:
            target_task = next((t for t in state.get("tasks", []) if t.get("status") == "pending"), None)
        if target_task:
            return {"reply": _task_breakdown(target_task)}
        return {"reply": "I can break down tasks as soon as at least one task is available."}

    if any(token in lower for token in ["too hard", "stuck", "difficult"]):
        task_id = _extract_task_id(message)
        register_dispute(state, dispute_type="difficulty", task_id=task_id, details=message)
        return {"reply": "I logged a difficulty dispute and requested replanning from the agent."}

    if "no time" in lower or ("time" in lower and "less" in lower):
        task_id = _extract_task_id(message)
        register_dispute(state, dispute_type="time", task_id=task_id, details=message)
        return {"reply": "I logged a time-constraint dispute and asked the agent to reduce effort intensity."}

    if "next" in lower or "what should i do" in lower or "plan" in lower:
        return {"reply": _next_actions(state)}

    return {
        "reply": "AGENT GURU can add goals, remove modules, update resumes, explain roadmap logic, and adjust tasks. "
        + _next_actions(state)
    }
