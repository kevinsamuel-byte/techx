"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [provider, setProvider] = useState<"linkedin" | "github">("linkedin");
  const [connected, setConnected] = useState<{ linkedin: boolean; github: boolean }>({
    linkedin: false,
    github: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const connectProvider = async () => {
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    try {
      const session = await api.socialLogin(email, provider);
      localStorage.setItem("pcn_token", session.session_token);
      setConnected((prev) => ({ ...prev, [provider]: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const continueToDashboard = async () => {
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    try {
      if (!localStorage.getItem("pcn_token")) {
        const session = await api.emailLogin(email);
        localStorage.setItem("pcn_token", session.session_token);
      }
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const resumeLogin = async (file: File) => {
    setLoading(true);
    setError("");
    try {
      const session = await api.emailLogin(email);
      localStorage.setItem("pcn_token", session.session_token);
      await api.uploadResume(file, session.session_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resume upload failed");
    } finally {
      setLoading(false);
    }
  };

  const openBuilder = async () => {
    const result = await api.getResumeBuilder();
    window.open(result.url, "_blank", "noopener,noreferrer");
  };

  return (
    <main className="center-screen">
      <section className="auth-card">
        <h1>Personal Career Navigator</h1>
        <p>Connect LinkedIn + GitHub, then upload your resume (or open AI resume builder).</p>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="you@example.com" />
        <div className="row">
          <button onClick={() => setProvider("linkedin")} className={provider === "linkedin" ? "active-provider" : ""}>LinkedIn</button>
          <button onClick={() => setProvider("github")} className={provider === "github" ? "active-provider" : ""}>GitHub</button>
        </div>
        <button onClick={connectProvider} disabled={loading}>{loading ? "Please wait..." : `Connect ${provider}`}</button>
        <p>Connected: LinkedIn {connected.linkedin ? "✓" : "•"} | GitHub {connected.github ? "✓" : "•"}</p>
        <label className="upload-box">
          Upload Resume (PDF/DOCX)
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) resumeLogin(file);
            }}
          />
        </label>
        <button className="ghost" onClick={openBuilder}>No resume? Use AI Resume Builder</button>
        <button onClick={continueToDashboard} disabled={loading}>Continue to Dashboard</button>
        {error && <p className="error-text">{error}</p>}
      </section>
    </main>
  );
}
