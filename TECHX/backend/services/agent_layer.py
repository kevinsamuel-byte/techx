import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .llm_layer import summarize_reasoning

VALID_TASK_STATUSES = {"pending", "completed", "skipped", "stuck"}
VALID_MODULES = {"education", "softskills", "certification"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_progress(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return min(100, round((done / total) * 100))


def default_user_state(user_id: str) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "user_id": user_id,
        "created_at": now,
        "last_active": now,
        "onboarding_complete": False,
        "goal": None,
        "constraints": {
            "daily_time_available": None,
            "urgency_level": None,
        },
        "auth": {
            "providers": [],
            "resume_uploaded": False,
            "resume_source": None,
        },
        "profile": {
            "education": [],
            "experience": [],
            "projects": [],
            "achievements": [],
            "softskills": [],
        },
        "current_stage": None,
        "skills": [],
        "roadmap": [],
        "module_roadmaps": {
            "education": {"tasks": [], "progress": 0},
            "softskills": {"tasks": [], "progress": 0},
            "certification": {"tasks": [], "progress": 0, "recommendations": []},
        },
        "tasks": [],
        "disputes": [],
        "change_log": [],
        "reasoning_log": [],
        "resources": [],
        "resume": {
            "version": 0,
            "summary": "",
            "projects": [],
            "highlights": [],
            "last_updated": now,
            "raw_text": "",
        },
        "chat_history": [],
    }


def _next_numeric_id(items: list[dict[str, Any]], key: str) -> int:
    if not items:
        return 1
    return max(int(item.get(key, 0)) for item in items) + 1


def _ensure_state_shapes(state: dict[str, Any]) -> None:
    state.setdefault("skills", [])
    state.setdefault("roadmap", [])
    state.setdefault("tasks", [])
    state.setdefault("disputes", [])
    state.setdefault("change_log", [])
    state.setdefault("reasoning_log", [])
    state.setdefault("resources", [])
    state.setdefault("auth", {"providers": [], "resume_uploaded": False, "resume_source": None})
    state.setdefault("profile", {"education": [], "experience": [], "projects": [], "achievements": [], "softskills": []})
    state.setdefault("constraints", {"daily_time_available": None, "urgency_level": None})
    state.setdefault("resume", {"version": 0, "summary": "", "projects": [], "highlights": [], "last_updated": utc_now_iso(), "raw_text": ""})
    state.setdefault(
        "module_roadmaps",
        {
            "education": {"tasks": [], "progress": 0},
            "softskills": {"tasks": [], "progress": 0},
            "certification": {"tasks": [], "progress": 0, "recommendations": []},
        },
    )


def _log_reasoning(state: dict[str, Any], decision: str, rationale: str, evidence: list[str] | None = None) -> None:
    _ensure_state_shapes(state)
    summary = summarize_reasoning(decision=decision, rationale=rationale, evidence=evidence)
    summary["reasoning_id"] = _next_numeric_id(state["reasoning_log"], "reasoning_id")
    state["reasoning_log"].append(summary)


def log_change(state: dict[str, Any], reason: str, action: str, reasoning_summary: str) -> None:
    _ensure_state_shapes(state)
    entry = {
        "change_id": _next_numeric_id(state["change_log"], "change_id"),
        "reason": reason,
        "action": action,
        "timestamp": utc_now_iso(),
    }
    state["change_log"].append(entry)
    _log_reasoning(state, decision=action, rationale=reasoning_summary, evidence=[reason])


def touch_last_active(state: dict[str, Any]) -> None:
    state["last_active"] = utc_now_iso()


def _normalize_skill_name(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9+.# ]", "", raw).strip()
    return cleaned.title()


def infer_skills(onboarding_payload: dict[str, Any]) -> list[dict[str, Any]]:
    resume_text = (onboarding_payload.get("resume_text") or "").lower()
    github_url = (onboarding_payload.get("github_url") or "").lower()
    manual_skills = onboarding_payload.get("manual_skills") or []

    keyword_map: dict[str, tuple[list[str], str, float]] = {
        "Python": (["python", "fastapi", "django", "flask", "pandas"], "intermediate", 0.72),
        "JavaScript": (["javascript", "typescript", "node", "react", "next"], "intermediate", 0.72),
        "SQL": (["sql", "postgres", "mysql", "sqlite"], "intermediate", 0.68),
        "Git": (["git", "github", "pull request", "branch"], "intermediate", 0.66),
        "Cloud": (["aws", "gcp", "azure", "cloud"], "beginner", 0.55),
        "Data Structures": (["algorithm", "data structure", "leetcode"], "beginner", 0.58),
        "Testing": (["pytest", "jest", "unit test", "integration"], "beginner", 0.57),
        "Communication": (["communication", "collaboration", "stakeholder"], "beginner", 0.55),
    }

    inferred: dict[str, dict[str, Any]] = {}
    evidence_blob = f"{resume_text}\n{github_url}"
    for skill_name, (keywords, level, confidence) in keyword_map.items():
        if any(k in evidence_blob for k in keywords):
            inferred[skill_name] = {
                "name": skill_name,
                "level": level,
                "confidence": round(confidence, 2),
            }

    for skill in manual_skills:
        normalized = _normalize_skill_name(skill)
        if not normalized:
            continue
        prior = inferred.get(normalized)
        if prior:
            prior["confidence"] = max(prior["confidence"], 0.75)
            continue
        inferred[normalized] = {
            "name": normalized,
            "level": "beginner",
            "confidence": 0.6,
        }

    if not inferred:
        inferred["Learning Agility"] = {
            "name": "Learning Agility",
            "level": "beginner",
            "confidence": 0.5,
        }

    return sorted(inferred.values(), key=lambda s: s["confidence"], reverse=True)


def _extract_section(text: str, section_name: str) -> str:
    pattern = re.compile(rf"{section_name}\s*[:\n](.*?)(\n[A-Z][A-Za-z ]+:|$)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def extract_resume_profile(raw_text: str) -> dict[str, Any]:
    text = raw_text or ""
    lines = [ln.strip(" -\t") for ln in text.splitlines() if ln.strip()]

    skills_blob = _extract_section(text, "skills")
    if not skills_blob:
        skills_blob = "\n".join([ln for ln in lines if "," in ln and len(ln) < 120][:3])
    parsed_skills = [s.strip() for s in re.split(r"[,|]", skills_blob) if 1 < len(s.strip()) < 30][:20]

    profile = {
        "education": [ln for ln in lines if any(token in ln.lower() for token in ["university", "college", "bachelor", "master", "degree"])][:5],
        "experience": [ln for ln in lines if any(token in ln.lower() for token in ["engineer", "developer", "intern", "manager", "analyst"])][:8],
        "projects": [ln for ln in lines if "project" in ln.lower()][:6],
        "achievements": [ln for ln in lines if any(token in ln.lower() for token in ["award", "achieve", "improved", "%", "increased", "reduced"])][:8],
        "softskills": [s for s in parsed_skills if s.lower() in {"communication", "leadership", "teamwork", "problem solving", "collaboration", "adaptability"}],
    }

    return {
        "summary": " ".join(lines[:3])[:260] or "Profile extracted from resume.",
        "skills": parsed_skills,
        "profile": profile,
    }


def _role_skill_targets(goal: str) -> list[str]:
    goal_l = goal.lower()
    if "backend" in goal_l:
        return ["Python", "Sql", "Api Design", "Testing", "System Design"]
    if "frontend" in goal_l:
        return ["Javascript", "React", "Css", "State Management", "Testing"]
    if "data" in goal_l:
        return ["Python", "Sql", "Statistics", "Machine Learning", "Data Visualization"]
    if "product" in goal_l:
        return ["Roadmapping", "Analytics", "Stakeholder Communication", "Experimentation", "Prioritization"]
    return ["Python", "Javascript", "Sql", "Testing", "Communication"]


def _base_resources(goal: str) -> list[dict[str, str]]:
    return [
        {"title": f"{goal} interview prep", "url": "https://roadmap.sh", "type": "career-guidance"},
        {"title": "Behavioral communication framework", "url": "https://www.themuse.com/advice/star-interview-method", "type": "softskills"},
        {"title": "Learning path planning", "url": "https://www.coursera.org/career-academy", "type": "education"},
    ]


def recommend_certifications(goal: str, skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skill_names = {str(s.get("name", "")).lower() for s in skills}
    goal_l = goal.lower()

    recs = [
        {
            "id": 1,
            "provider": "Coursera",
            "title": "Google Project Management",
            "url": "https://www.coursera.org/professional-certificates/google-project-management",
            "stage": "foundation",
        },
        {
            "id": 2,
            "provider": "Udemy",
            "title": "Complete Communication Skills Master Class",
            "url": "https://www.udemy.com/topic/communication-skills/",
            "stage": "softskills",
        },
    ]

    if "backend" in goal_l or "python" in skill_names:
        recs.append(
            {
                "id": 3,
                "provider": "Coursera",
                "title": "Meta Back-End Developer",
                "url": "https://www.coursera.org/professional-certificates/meta-back-end-developer",
                "stage": "specialization",
            }
        )
    if "frontend" in goal_l or "javascript" in skill_names:
        recs.append(
            {
                "id": 4,
                "provider": "Coursera",
                "title": "Meta Front-End Developer",
                "url": "https://www.coursera.org/professional-certificates/meta-front-end-developer",
                "stage": "specialization",
            }
        )

    return recs[:8]


def _build_module_tasks(goal: str, skills: list[dict[str, Any]]) -> dict[str, Any]:
    skill_names = [s.get("name", "") for s in skills[:6]] or ["Communication", "Execution"]
    education_tasks = [
        {"task_id": 1, "title": f"Learn {goal} fundamentals", "completed": False},
        {"task_id": 2, "title": f"Study {skill_names[0]} deeply", "completed": False},
        {"task_id": 3, "title": "Build a mini project to validate learning", "completed": False},
    ]
    softskills_tasks = [
        {"task_id": 1, "title": "Practice STAR storytelling weekly", "completed": False},
        {"task_id": 2, "title": "Run peer feedback and communication drills", "completed": False},
        {"task_id": 3, "title": "Present one project walkthrough", "completed": False},
    ]
    certification_tasks = [
        {"task_id": 1, "title": "Pick certification track", "completed": False},
        {"task_id": 2, "title": "Finish first certification module", "completed": False},
        {"task_id": 3, "title": "Complete capstone and share credential", "completed": False},
    ]

    cert_recs = recommend_certifications(goal, skills)
    return {
        "education": {"tasks": education_tasks, "progress": 0},
        "softskills": {"tasks": softskills_tasks, "progress": 0},
        "certification": {"tasks": certification_tasks, "progress": 0, "recommendations": cert_recs},
    }


def refresh_module_roadmaps(state: dict[str, Any]) -> None:
    _ensure_state_shapes(state)
    goal = state.get("goal") or "Career Goal"
    state["module_roadmaps"] = _build_module_tasks(goal, state.get("skills", []))
    state["resources"] = _base_resources(goal)


def complete_onboarding(state: dict[str, Any], onboarding_payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_state_shapes(state)
    inferred_skills = infer_skills(onboarding_payload)
    state["skills"] = inferred_skills
    state["onboarding_complete"] = True

    resume_summary = (
        "Execution-focused candidate with demonstrated consistency in skill-building and delivery. "
        f"Initial profile synthesized from onboarding mode: {onboarding_payload.get('option', 'start_from_scratch')}."
    )
    state["resume"] = {
        "version": 1,
        "summary": resume_summary,
        "projects": [],
        "highlights": [
            f"Initial skill inventory built with {len(inferred_skills)} skills",
            "Baseline resume generated and ready for iterative upgrades",
        ],
        "last_updated": utc_now_iso(),
        "raw_text": onboarding_payload.get("resume_text") or "",
    }

    if onboarding_payload.get("resume_text"):
        state["auth"]["resume_uploaded"] = True
        state["auth"]["resume_source"] = "upload"
        parsed = extract_resume_profile(onboarding_payload.get("resume_text") or "")
        state["profile"] = parsed["profile"]

    refresh_module_roadmaps(state)
    touch_last_active(state)
    log_change(
        state,
        reason="Onboarding completed and baseline profile was created.",
        action="onboarding_initialized",
        reasoning_summary="Skills were inferred from available user inputs and resume v1 was generated.",
    )
    return state


def ingest_resume_text(state: dict[str, Any], raw_text: str, source: str = "upload") -> dict[str, Any]:
    _ensure_state_shapes(state)
    parsed = extract_resume_profile(raw_text)
    parsed_skills = infer_skills({"resume_text": raw_text, "manual_skills": parsed.get("skills", [])})

    state["skills"] = parsed_skills
    state["profile"] = parsed["profile"]
    state["resume"]["version"] = max(1, int(state["resume"].get("version", 0)) + 1)
    state["resume"]["summary"] = parsed["summary"]
    state["resume"]["raw_text"] = raw_text[:10000]
    state["resume"]["last_updated"] = utc_now_iso()
    state["auth"]["resume_uploaded"] = True
    state["auth"]["resume_source"] = source
    state["onboarding_complete"] = True

    refresh_module_roadmaps(state)
    touch_last_active(state)
    log_change(
        state,
        reason="Resume was uploaded and parsed into structured profile data.",
        action="resume_ingested",
        reasoning_summary="NLP-lite parsing extracted profile, skills, and baseline roadmap modules.",
    )
    return state


def register_auth_provider(state: dict[str, Any], provider: str, provider_user_id: str | None = None) -> None:
    _ensure_state_shapes(state)
    providers = state["auth"].setdefault("providers", [])
    provider = provider.lower().strip()
    if provider not in {"linkedin", "github"}:
        return
    if any(p.get("provider") == provider for p in providers):
        return
    providers.append(
        {
            "provider": provider,
            "provider_user_id": provider_user_id,
            "connected_at": utc_now_iso(),
        }
    )


def set_goal_and_constraints(
    state: dict[str, Any],
    target_role: str,
    daily_time_available: int,
    urgency_level: str,
) -> dict[str, Any]:
    _ensure_state_shapes(state)
    state["goal"] = target_role.strip()
    state["constraints"] = {
        "daily_time_available": daily_time_available,
        "urgency_level": urgency_level,
    }
    refresh_module_roadmaps(state)
    touch_last_active(state)
    log_change(
        state,
        reason="User provided execution goal and planning constraints.",
        action="constraints_updated",
        reasoning_summary="Roadmap and task difficulty will be conditioned on time and urgency constraints.",
    )
    return state


def generate_roadmap(state: dict[str, Any]) -> dict[str, Any]:
    _ensure_state_shapes(state)
    if not state.get("goal"):
        raise ValueError("Goal is required before roadmap generation.")

    target_skills = _role_skill_targets(state["goal"])
    skill_conf = {s["name"].lower(): float(s.get("confidence", 0.5)) for s in state.get("skills", [])}
    major_gaps = [s for s in target_skills if skill_conf.get(s.lower(), 0.0) < 0.7]
    urgency = state.get("constraints", {}).get("urgency_level") or "medium"

    stage_blueprint = [
        {
            "stage_id": 1,
            "title": "Core Skill Closure",
            "required_skills": major_gaps[:3] or target_skills[:3],
            "measurable_outcome": "Complete 6 focused practice outputs with tracked confidence gains.",
            "status": "in_progress",
        },
        {
            "stage_id": 2,
            "title": "Portfolio Proof",
            "required_skills": major_gaps[1:4] or target_skills[1:4],
            "measurable_outcome": "Ship one portfolio-grade project with documented tradeoffs.",
            "status": "pending",
        },
        {
            "stage_id": 3,
            "title": "Interview Readiness",
            "required_skills": target_skills[:4],
            "measurable_outcome": "Finish 3 mock interviews and close recurring weak areas.",
            "status": "pending",
        },
        {
            "stage_id": 4,
            "title": "Application Sprint",
            "required_skills": ["Communication", "Narrative", "Execution"],
            "measurable_outcome": "Submit 12 high-quality applications with tailored assets.",
            "status": "pending",
        },
    ]

    if urgency == "high":
        for stage in stage_blueprint:
            stage["measurable_outcome"] = f"Accelerated: {stage['measurable_outcome']}"

    state["roadmap"] = stage_blueprint
    state["current_stage"] = 1
    refresh_module_roadmaps(state)
    touch_last_active(state)
    log_change(
        state,
        reason="Roadmap regenerated based on role target, skill gaps, and urgency.",
        action="roadmap_generated",
        reasoning_summary="Stages were sequenced from skill closure to job execution and adapted for urgency.",
    )
    return state


def _difficulty_from_confidence(confidence: float) -> str:
    if confidence < 0.45:
        return "easy"
    if confidence < 0.75:
        return "medium"
    return "hard"


def _active_stage(state: dict[str, Any]) -> dict[str, Any] | None:
    for stage in state.get("roadmap", []):
        if stage.get("status") == "in_progress":
            return stage
    return None


def _next_task_id(state: dict[str, Any]) -> int:
    tasks = state.get("tasks", [])
    if not tasks:
        return 1
    return max(int(t.get("task_id", 0)) for t in tasks) + 1


def generate_daily_tasks(state: dict[str, Any]) -> dict[str, Any]:
    _ensure_state_shapes(state)
    stage = _active_stage(state)
    if not stage:
        return state

    pending_tasks = [t for t in state["tasks"] if t.get("status") == "pending"]
    if len(pending_tasks) >= 3:
        return state

    daily_time = int(state.get("constraints", {}).get("daily_time_available") or 90)
    slots = 3 - len(pending_tasks)
    stage_skills = stage.get("required_skills", []) or ["Execution"]
    skill_lookup = {s["name"].lower(): float(s.get("confidence", 0.5)) for s in state.get("skills", [])}

    proposed = []
    for idx in range(slots):
        skill = stage_skills[idx % len(stage_skills)]
        confidence = skill_lookup.get(skill.lower(), 0.4)
        task_title = f"{stage['title']}: Ship a focused output for {skill}"
        proposed.append(
            {
                "task_id": _next_task_id(state) + idx,
                "stage_id": stage["stage_id"],
                "title": task_title,
                "estimated_time": max(20, daily_time // max(1, 3)),
                "difficulty": _difficulty_from_confidence(confidence),
                "status": "pending",
            }
        )

    state["tasks"].extend(proposed)
    touch_last_active(state)
    log_change(
        state,
        reason="Task manager refilled based on active stage and daily time limit.",
        action="tasks_generated",
        reasoning_summary="Generated up to three tasks while respecting available daily time and confidence-adaptive difficulty.",
    )
    return state


def _find_task(state: dict[str, Any], task_id: int) -> dict[str, Any] | None:
    for task in state.get("tasks", []):
        if int(task.get("task_id", -1)) == int(task_id):
            return task
    return None


def _adjust_pending_difficulty(state: dict[str, Any]) -> None:
    next_level = {"hard": "medium", "medium": "easy", "easy": "easy"}
    for task in state.get("tasks", []):
        if task.get("status") != "pending":
            continue
        task["difficulty"] = next_level.get(task.get("difficulty", "medium"), "easy")
        task["estimated_time"] = max(15, int(task.get("estimated_time", 30)) - 10)


def _update_skill_confidence_from_completed(state: dict[str, Any], completed_tasks: list[dict[str, Any]]) -> None:
    if not completed_tasks:
        return

    skill_map = {skill["name"]: skill for skill in state.get("skills", [])}
    if not skill_map:
        return

    for task in completed_tasks:
        task_title = task.get("title", "").lower()
        updated = False
        for skill_name, skill_obj in skill_map.items():
            if skill_name.lower() in task_title:
                skill_obj["confidence"] = round(min(1.0, float(skill_obj.get("confidence", 0.5)) + 0.06), 2)
                updated = True
        if not updated:
            first_skill = next(iter(skill_map.values()))
            first_skill["confidence"] = round(min(1.0, float(first_skill.get("confidence", 0.5)) + 0.03), 2)


def _advance_stage_if_ready(state: dict[str, Any]) -> None:
    current = _active_stage(state)
    if not current:
        return

    stage_id = current["stage_id"]
    stage_tasks = [t for t in state.get("tasks", []) if int(t.get("stage_id", -1)) == int(stage_id)]
    completed = [t for t in stage_tasks if t.get("status") == "completed"]
    pending = [t for t in stage_tasks if t.get("status") == "pending"]

    if len(completed) < 2 or pending:
        return

    current["status"] = "completed"
    for stage in state.get("roadmap", []):
        if stage["stage_id"] == stage_id + 1:
            stage["status"] = "in_progress"
            state["current_stage"] = stage["stage_id"]
            break


def evolve_resume(state: dict[str, Any], completed_count: int) -> None:
    resume = state.setdefault(
        "resume",
        {"version": 0, "summary": "", "projects": [], "highlights": [], "last_updated": utc_now_iso(), "raw_text": ""},
    )
    if completed_count <= 0:
        return

    resume["version"] = int(resume.get("version", 0)) + 1
    goal = state.get("goal") or "target role"
    resume["projects"].append(
        {
            "name": f"Execution Sprint {resume['version']}",
            "impact": f"Completed {completed_count} tracked tasks aligned to {goal}.",
            "timestamp": utc_now_iso(),
        }
    )

    avg_conf = 0.0
    if state.get("skills"):
        avg_conf = sum(float(s.get("confidence", 0.5)) for s in state["skills"]) / len(state["skills"])

    resume["highlights"].append(
        f"Average skill confidence reached {avg_conf:.2f} after execution cycle {resume['version']}."
    )
    resume["summary"] = (
        "Execution-driven candidate with measurable evidence of growth through continuous task completion, "
        "feedback loops, and project delivery."
    )
    resume["last_updated"] = utc_now_iso()

    log_change(
        state,
        reason="Task completion triggered measurable profile growth.",
        action="resume_evolved",
        reasoning_summary="Resume version was incremented using completed task evidence and updated confidence trends.",
    )


def _recalculate_module_progress(state: dict[str, Any], module: str) -> None:
    module_data = state["module_roadmaps"].get(module, {"tasks": [], "progress": 0})
    tasks = module_data.get("tasks", [])
    done = sum(1 for t in tasks if t.get("completed"))
    module_data["progress"] = _safe_progress(done, len(tasks))


def mark_module_task(
    state: dict[str, Any], module: str, task_id: int, completed: bool = True
) -> dict[str, Any]:
    _ensure_state_shapes(state)
    module = module.lower().strip()
    if module not in VALID_MODULES:
        return state

    module_data = state["module_roadmaps"].get(module)
    if not module_data:
        return state

    for task in module_data.get("tasks", []):
        if int(task.get("task_id", -1)) == int(task_id):
            task["completed"] = completed
            break

    _recalculate_module_progress(state, module)
    touch_last_active(state)
    log_change(
        state,
        reason=f"{module} module task status was updated.",
        action="module_progress_updated",
        reasoning_summary="Visual roadmap progression is synchronized with module checklist completion.",
    )
    return state


def regenerate_resume(state: dict[str, Any], from_scratch: bool = False) -> dict[str, Any]:
    _ensure_state_shapes(state)
    if from_scratch:
        state["resume"] = {
            "version": 1,
            "summary": "Fresh resume drafted by AGENT GURU based on current goal and roadmap.",
            "projects": [],
            "highlights": ["New resume generated from current profile state."],
            "last_updated": utc_now_iso(),
            "raw_text": "",
        }
        action = "resume_created"
    else:
        state["resume"]["version"] = int(state["resume"].get("version", 0)) + 1
        state["resume"]["summary"] = f"Updated resume for goal: {state.get('goal') or 'Career Transition'}"
        state["resume"].setdefault("highlights", []).append("Resume updated using latest roadmap progress and achievements.")
        state["resume"]["last_updated"] = utc_now_iso()
        action = "resume_updated"

    touch_last_active(state)
    log_change(
        state,
        reason="AGENT GURU performed a resume generation action.",
        action=action,
        reasoning_summary="Resume content was regenerated to match current roadmap and growth evidence.",
    )
    return state


def remove_module(state: dict[str, Any], module: str) -> dict[str, Any]:
    _ensure_state_shapes(state)
    module = module.lower().strip()
    if module not in VALID_MODULES:
        return state
    state["module_roadmaps"].pop(module, None)
    touch_last_active(state)
    log_change(
        state,
        reason=f"User requested to remove {module} module.",
        action="module_removed",
        reasoning_summary="Module was removed from the personalized roadmap as requested.",
    )
    return state


def add_goal(state: dict[str, Any], goal: str) -> dict[str, Any]:
    _ensure_state_shapes(state)
    state["goal"] = goal.strip()
    refresh_module_roadmaps(state)
    touch_last_active(state)
    log_change(
        state,
        reason="User requested a new career goal.",
        action="goal_updated",
        reasoning_summary="Roadmaps were regenerated around the newly provided target goal.",
    )
    return state


def process_feedback(state: dict[str, Any], updates: list[dict[str, Any]]) -> dict[str, Any]:
    _ensure_state_shapes(state)

    completed_tasks: list[dict[str, Any]] = []
    saw_friction = False

    for update in updates:
        task = _find_task(state, int(update["task_id"]))
        if not task:
            continue

        status = update.get("status")
        if status not in VALID_TASK_STATUSES:
            continue

        task["status"] = status
        if status == "completed":
            completed_tasks.append(task)
        if status in {"stuck", "skipped"}:
            saw_friction = True
            state["disputes"].append(
                {
                    "dispute_type": "difficulty" if status == "stuck" else "priority",
                    "task_id": task["task_id"],
                    "timestamp": utc_now_iso(),
                }
            )

    if completed_tasks:
        _update_skill_confidence_from_completed(state, completed_tasks)

    if saw_friction:
        _adjust_pending_difficulty(state)

    _advance_stage_if_ready(state)
    generate_daily_tasks(state)
    evolve_resume(state, completed_count=len(completed_tasks))

    touch_last_active(state)
    log_change(
        state,
        reason="Daily feedback received; plan adapted to outcomes and friction.",
        action="feedback_processed",
        reasoning_summary="Updated task statuses, adjusted future difficulty, and refreshed tasks for the next execution cycle.",
    )
    return state


def register_dispute(
    state: dict[str, Any],
    dispute_type: str,
    task_id: int | None,
    details: str | None = None,
) -> dict[str, Any]:
    _ensure_state_shapes(state)

    entry = {
        "dispute_type": dispute_type,
        "task_id": task_id,
        "timestamp": utc_now_iso(),
    }
    if details:
        entry["details"] = details
    state["disputes"].append(entry)

    if task_id is not None:
        task = _find_task(state, task_id)
        if task and task.get("status") in {"pending", "stuck"}:
            task["difficulty"] = "easy" if dispute_type in {"difficulty", "time"} else task.get("difficulty", "medium")
            task["estimated_time"] = max(15, int(task.get("estimated_time", 30)) - 10)

    generate_daily_tasks(state)
    touch_last_active(state)
    log_change(
        state,
        reason=f"User raised a {dispute_type} dispute.",
        action="dispute_logged_and_replanned",
        reasoning_summary="Dispute was logged and execution plan was softened where needed while preserving roadmap intent.",
    )
    return state


def new_user_state() -> dict[str, Any]:
    return default_user_state(user_id=str(uuid.uuid4()))
