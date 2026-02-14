import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import UserStateRecord, utc_now
from .schemas import (
    ChatRequest,
    ChatResponse,
    DisputeRequest,
    FeedbackRequest,
    GoalConstraintsRequest,
    LoginRequest,
    LoginResponse,
    ModuleProgressRequest,
    OnboardingRequest,
    ResumeBuilderResponse,
    SocialLoginRequest,
    UserStateResponse,
)
from .services.agent_layer import (
    complete_onboarding,
    generate_daily_tasks,
    generate_roadmap,
    ingest_resume_text,
    mark_module_task,
    new_user_state,
    register_auth_provider,
    register_dispute,
    set_goal_and_constraints,
    touch_last_active,
)
from .services.chat_layer import respond_to_message

app = FastAPI(title="Personal Career Navigator API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def _state_from_record(record: UserStateRecord) -> dict[str, Any]:
    return json.loads(record.user_state_json)


def _save_state(record: UserStateRecord, state: dict[str, Any], db: Session) -> None:
    record.user_state_json = json.dumps(state)
    record.last_active = utc_now()
    db.add(record)
    db.commit()
    db.refresh(record)


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected Bearer token")
    return parts[1]


def _session_expired(record: UserStateRecord) -> bool:
    ttl = timedelta(hours=settings.session_ttl_hours)
    last_active = record.last_active
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last_active) > ttl


def get_record_from_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserStateRecord:
    token = _extract_bearer_token(authorization)
    record = db.scalar(select(UserStateRecord).where(UserStateRecord.session_token == token))
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if _session_expired(record):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return record


def _read_upload_text(filename: str, file_bytes: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".docx"):
            from docx import Document  # type: ignore
            from io import BytesIO

            doc = Document(BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text).strip()
        if name.endswith(".pdf"):
            from io import BytesIO
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
    except Exception:
        pass

    return file_bytes.decode("utf-8", errors="ignore")


def _login_response(record: UserStateRecord) -> LoginResponse:
    state = _state_from_record(record)
    return LoginResponse(
        session_token=record.session_token,
        user_id=state["user_id"],
        onboarding_complete=bool(state.get("onboarding_complete", False)),
    )


def _upsert_user(email: str, db: Session) -> UserStateRecord:
    normalized_email = email.lower().strip()
    record = db.scalar(select(UserStateRecord).where(UserStateRecord.email == normalized_email))

    if not record:
        state = new_user_state()
        record = UserStateRecord(
            email=normalized_email,
            session_token=secrets.token_urlsafe(32),
            user_state_json=json.dumps(state),
            last_active=utc_now(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    else:
        state = _state_from_record(record)
        touch_last_active(state)
        record.session_token = secrets.token_urlsafe(32)
        _save_state(record, state, db)

    return record


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return _login_response(_upsert_user(payload.email, db))


@app.post("/api/auth/social-login", response_model=LoginResponse)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    record = _upsert_user(payload.email, db)
    state = _state_from_record(record)
    register_auth_provider(state, payload.provider, payload.provider_user_id)
    _save_state(record, state, db)
    return _login_response(record)


@app.get("/api/auth/resume-builder", response_model=ResumeBuilderResponse)
def resume_builder() -> ResumeBuilderResponse:
    return ResumeBuilderResponse(url="https://www.canva.com/resumes/templates/ai-resume-builder/")


@app.post("/api/auth/resume-upload", response_model=UserStateResponse)
async def upload_resume(
    resume: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    record = get_record_from_auth(authorization=authorization, db=db)
    file_bytes = await resume.read()
    text = _read_upload_text(resume.filename or "resume.txt", file_bytes)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume file")

    state = _state_from_record(record)
    ingest_resume_text(state, text, source="upload")
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/auth/resume-text", response_model=UserStateResponse)
def upload_resume_text(
    resume_text: str = Form(...),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    record = get_record_from_auth(authorization=authorization, db=db)
    state = _state_from_record(record)
    ingest_resume_text(state, resume_text, source="builder")
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.get("/api/state", response_model=UserStateResponse)
def get_state(record: UserStateRecord = Depends(get_record_from_auth), db: Session = Depends(get_db)) -> UserStateResponse:
    state = _state_from_record(record)
    touch_last_active(state)
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/onboarding", response_model=UserStateResponse)
def onboarding(
    payload: OnboardingRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    state = complete_onboarding(state, payload.model_dump())
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/goal-constraints", response_model=UserStateResponse)
def goal_constraints(
    payload: GoalConstraintsRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    state = set_goal_and_constraints(
        state,
        target_role=payload.target_role,
        daily_time_available=payload.daily_time_available,
        urgency_level=payload.urgency_level,
    )
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/roadmap/generate", response_model=UserStateResponse)
def roadmap_generate(
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    if not state.get("onboarding_complete"):
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    state = generate_roadmap(state)
    state = generate_daily_tasks(state)
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/tasks/generate", response_model=UserStateResponse)
def tasks_generate(
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    state = generate_daily_tasks(state)
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/modules/progress", response_model=UserStateResponse)
def module_progress(
    payload: ModuleProgressRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    state = mark_module_task(state, payload.module, payload.task_id, payload.completed)
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/feedback", response_model=UserStateResponse)
def feedback(
    payload: FeedbackRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    from .services.agent_layer import process_feedback

    state = _state_from_record(record)
    state = process_feedback(state, updates=[u.model_dump() for u in payload.updates])
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/disputes", response_model=UserStateResponse)
def dispute(
    payload: DisputeRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> UserStateResponse:
    state = _state_from_record(record)
    state = register_dispute(
        state,
        dispute_type=payload.dispute_type,
        task_id=payload.task_id,
        details=payload.details,
    )
    _save_state(record, state, db)
    return UserStateResponse(**state)


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    record: UserStateRecord = Depends(get_record_from_auth),
    db: Session = Depends(get_db),
) -> ChatResponse:
    state = _state_from_record(record)
    result = respond_to_message(state, payload.message)
    state.setdefault("chat_history", []).append({"role": "user", "message": payload.message})
    state["chat_history"].append({"role": "assistant", "message": result["reply"]})
    touch_last_active(state)
    _save_state(record, state, db)
    return ChatResponse(reply=result["reply"])
