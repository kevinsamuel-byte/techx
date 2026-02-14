const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

async function request(path, method = "GET", token = null, body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }

  return res.json();
}

export const api = {
  login: (email) => request("/auth/login", "POST", null, { email }),
  state: (token) => request("/state", "GET", token),
  onboarding: (token, payload) => request("/onboarding", "POST", token, payload),
  goalConstraints: (token, payload) => request("/goal-constraints", "POST", token, payload),
  generateRoadmap: (token) => request("/roadmap/generate", "POST", token),
  generateTasks: (token) => request("/tasks/generate", "POST", token),
  feedback: (token, updates) => request("/feedback", "POST", token, { updates }),
  dispute: (token, payload) => request("/disputes", "POST", token, payload),
  chat: (token, message) => request("/chat", "POST", token, { message }),
};
