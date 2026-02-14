import { LoginResponse, UserState } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }

  return response.json() as Promise<T>;
}

export const api = {
  socialLogin: (email: string, provider: "linkedin" | "github", provider_user_id?: string) =>
    request<LoginResponse>("/auth/social-login", {
      method: "POST",
      body: JSON.stringify({ email, provider, provider_user_id: provider_user_id || null }),
    }),

  emailLogin: (email: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  getResumeBuilder: () => request<{ url: string }>("/auth/resume-builder"),

  uploadResume: (file: File, token: string) => {
    const formData = new FormData();
    formData.append("resume", file);
    return request<UserState>("/auth/resume-upload", { method: "POST", body: formData }, token);
  },

  getState: (token: string) => request<UserState>("/state", {}, token),

  saveGoal: (token: string, target_role: string, daily_time_available: number, urgency_level: "low" | "medium" | "high") =>
    request<UserState>(
      "/goal-constraints",
      {
        method: "POST",
        body: JSON.stringify({ target_role, daily_time_available, urgency_level }),
      },
      token
    ),

  generateRoadmap: (token: string) => request<UserState>("/roadmap/generate", { method: "POST" }, token),

  updateModuleProgress: (token: string, module: "education" | "softskills" | "certification", task_id: number, completed: boolean) =>
    request<UserState>(
      "/modules/progress",
      { method: "POST", body: JSON.stringify({ module, task_id, completed }) },
      token
    ),

  chatGuru: (token: string, message: string) => request<{ reply: string }>("/chat", { method: "POST", body: JSON.stringify({ message }) }, token),
};
