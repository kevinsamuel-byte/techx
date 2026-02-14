import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///./test_career_agent.db"

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_user_flow() -> None:
    email = f"student-{uuid.uuid4().hex[:8]}@example.com"

    login = client.post("/api/auth/social-login", json={"email": email, "provider": "linkedin"})
    assert login.status_code == 200
    token = login.json()["session_token"]

    resume = client.post(
        "/api/auth/resume-text",
        data={
            "resume_text": (
                "Skills: Python, FastAPI, SQL, Communication\n"
                "Education: Bachelor of Engineering\n"
                "Experience: Backend Engineer Intern"
            )
        },
        headers=_auth_headers(token),
    )
    assert resume.status_code == 200
    body = resume.json()
    assert body["onboarding_complete"] is True
    assert len(body["skills"]) >= 1

    goal = client.post(
        "/api/goal-constraints",
        json={"target_role": "Backend Engineer", "daily_time_available": 120, "urgency_level": "medium"},
        headers=_auth_headers(token),
    )
    assert goal.status_code == 200
    assert goal.json()["goal"] == "Backend Engineer"

    roadmap = client.post("/api/roadmap/generate", headers=_auth_headers(token))
    assert roadmap.status_code == 200
    roadmap_body = roadmap.json()
    assert len(roadmap_body["roadmap"]) >= 1
    assert "education" in roadmap_body["module_roadmaps"]

    module_update = client.post(
        "/api/modules/progress",
        json={"module": "education", "task_id": 1, "completed": True},
        headers=_auth_headers(token),
    )
    assert module_update.status_code == 200
    assert module_update.json()["module_roadmaps"]["education"]["progress"] >= 0

    guru = client.post("/api/chat", json={"message": "update resume"}, headers=_auth_headers(token))
    assert guru.status_code == 200
    assert "AGENT GURU" in guru.json()["reply"]
