export type SkillItem = {
  name: string;
  level: string;
  confidence: number;
};

export type RoadmapStage = {
  stage_id: number;
  title: string;
  required_skills: string[];
  measurable_outcome: string;
  status: string;
};

export type ModuleTask = {
  task_id: number;
  title: string;
  completed: boolean;
};

export type ModuleRoadmap = {
  tasks: ModuleTask[];
  progress: number;
  recommendations?: { id: number; provider: string; title: string; url: string; stage: string }[];
};

export type UserState = {
  user_id: string;
  onboarding_complete: boolean;
  goal: string | null;
  resources: { title: string; url: string; type: string }[];
  auth: {
    providers: { provider: string; provider_user_id: string | null; connected_at: string }[];
    resume_uploaded: boolean;
    resume_source: string | null;
  };
  constraints: { daily_time_available: number | null; urgency_level: string | null };
  skills: SkillItem[];
  roadmap: RoadmapStage[];
  module_roadmaps: Record<string, ModuleRoadmap>;
  tasks: { task_id: number; title: string; difficulty: string; estimated_time: number; status: string }[];
  resume: { version: number; summary: string; highlights: string[]; last_updated: string };
  profile: {
    education: string[];
    experience: string[];
    projects: string[];
    achievements: string[];
    softskills: string[];
  };
};

export type LoginResponse = {
  session_token: string;
  user_id: string;
  onboarding_complete: boolean;
};
