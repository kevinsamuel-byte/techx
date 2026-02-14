from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


TaskStatus = Literal["pending", "completed", "skipped", "stuck"]
OnboardingOption = Literal["upload_resume", "connect_github", "start_from_scratch"]
UrgencyLevel = Literal["low", "medium", "high"]
Provider = Literal["linkedin", "github"]
ModuleName = Literal["education", "softskills", "certification"]


class LoginRequest(BaseModel):
    email: EmailStr


class SocialLoginRequest(BaseModel):
    email: EmailStr
    provider: Provider
    provider_user_id: str | None = None


class LoginResponse(BaseModel):
    session_token: str
    user_id: str
    onboarding_complete: bool


class SkillItem(BaseModel):
    name: str
    level: str
    confidence: float = Field(ge=0.0, le=1.0)


class RoadmapStage(BaseModel):
    stage_id: int
    title: str
    required_skills: list[str] = Field(default_factory=list)
    measurable_outcome: str
    status: str


class TaskItem(BaseModel):
    task_id: int
    stage_id: int
    title: str
    estimated_time: int
    difficulty: str
    status: TaskStatus


class DisputeItem(BaseModel):
    dispute_type: str
    task_id: int | None = None
    timestamp: str
    details: str | None = None


class ChangeLogItem(BaseModel):
    change_id: int
    reason: str
    action: str
    timestamp: str


class UserConstraints(BaseModel):
    daily_time_available: int | None = None
    urgency_level: str | None = None


class ResumeData(BaseModel):
    version: int
    summary: str
    projects: list[dict[str, Any]] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    last_updated: str
    raw_text: str | None = None


class ModuleTask(BaseModel):
    task_id: int
    title: str
    completed: bool


class ModuleRoadmap(BaseModel):
    tasks: list[ModuleTask] = Field(default_factory=list)
    progress: int = 0
    recommendations: list[dict[str, Any]] = Field(default_factory=list)


class ProfileData(BaseModel):
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    softskills: list[str] = Field(default_factory=list)


class AuthProviderItem(BaseModel):
    provider: str
    provider_user_id: str | None = None
    connected_at: str


class AuthState(BaseModel):
    providers: list[AuthProviderItem] = Field(default_factory=list)
    resume_uploaded: bool = False
    resume_source: str | None = None


class UserStateResponse(BaseModel):
    user_id: str
    created_at: str
    last_active: str
    onboarding_complete: bool
    goal: str | None = None
    constraints: UserConstraints
    auth: AuthState = Field(default_factory=AuthState)
    current_stage: int | None = None
    skills: list[SkillItem] = Field(default_factory=list)
    roadmap: list[RoadmapStage] = Field(default_factory=list)
    module_roadmaps: dict[str, ModuleRoadmap] = Field(default_factory=dict)
    resources: list[dict[str, str]] = Field(default_factory=list)
    profile: ProfileData = Field(default_factory=ProfileData)
    tasks: list[TaskItem] = Field(default_factory=list)
    disputes: list[DisputeItem] = Field(default_factory=list)
    change_log: list[ChangeLogItem] = Field(default_factory=list)
    reasoning_log: list[dict[str, Any]] = Field(default_factory=list)
    resume: ResumeData
    chat_history: list[dict[str, str]] = Field(default_factory=list)


class OnboardingRequest(BaseModel):
    option: OnboardingOption
    resume_text: str | None = None
    github_url: str | None = None
    manual_skills: list[str] = Field(default_factory=list)


class GoalConstraintsRequest(BaseModel):
    target_role: str
    daily_time_available: int = Field(ge=15, le=480)
    urgency_level: UrgencyLevel


class FeedbackUpdate(BaseModel):
    task_id: int
    status: TaskStatus
    notes: str | None = None


class FeedbackRequest(BaseModel):
    updates: list[FeedbackUpdate]


class DisputeRequest(BaseModel):
    dispute_type: str
    task_id: int | None = None
    details: str | None = None


class ModuleProgressRequest(BaseModel):
    module: ModuleName
    task_id: int
    completed: bool = True


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str


class ResumeBuilderResponse(BaseModel):
    url: str


class Envelope(BaseModel):
    ok: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
