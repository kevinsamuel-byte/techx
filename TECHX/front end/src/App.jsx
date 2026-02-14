import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const urgencyOptions = ["low", "medium", "high"];

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const result = await api.login(email);
      onLogin(result.session_token);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="panel">
      <h1>Agentic Career Execution System</h1>
      <p>Email login creates or restores your longitudinal state.</p>
      <form onSubmit={submit}>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        <button type="submit">Continue</button>
      </form>
      {error && <div className="error">{error}</div>}
    </section>
  );
}

function Onboarding({ token, onState }) {
  const [option, setOption] = useState("start_from_scratch");
  const [resumeText, setResumeText] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [manualSkills, setManualSkills] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const state = await api.onboarding(token, {
        option,
        resume_text: resumeText || null,
        github_url: githubUrl || null,
        manual_skills: manualSkills.split(",").map((s) => s.trim()).filter(Boolean),
      });
      onState(state);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="panel">
      <h2>Onboarding</h2>
      <form onSubmit={submit}>
        <label>
          Mode
          <select value={option} onChange={(e) => setOption(e.target.value)}>
            <option value="upload_resume">Upload resume text</option>
            <option value="connect_github">Connect GitHub</option>
            <option value="start_from_scratch">Start from scratch</option>
          </select>
        </label>
        <label>
          Resume text
          <textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)} rows={5} />
        </label>
        <label>
          GitHub URL
          <input value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)} placeholder="https://github.com/username" />
        </label>
        <label>
          Manual skills (comma-separated)
          <input value={manualSkills} onChange={(e) => setManualSkills(e.target.value)} placeholder="Python, FastAPI, SQL" />
        </label>
        <button type="submit">Complete onboarding</button>
      </form>
      {error && <div className="error">{error}</div>}
    </section>
  );
}

function GoalSetup({ token, onState }) {
  const [targetRole, setTargetRole] = useState("");
  const [dailyTime, setDailyTime] = useState(90);
  const [urgency, setUrgency] = useState("medium");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.goalConstraints(token, {
        target_role: targetRole,
        daily_time_available: Number(dailyTime),
        urgency_level: urgency,
      });
      const state = await api.generateRoadmap(token);
      onState(state);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="panel">
      <h2>Goal and Constraints</h2>
      <form onSubmit={submit}>
        <label>
          Target role
          <input required value={targetRole} onChange={(e) => setTargetRole(e.target.value)} placeholder="Backend Engineer" />
        </label>
        <label>
          Daily available time (minutes)
          <input type="number" min={15} max={480} value={dailyTime} onChange={(e) => setDailyTime(e.target.value)} />
        </label>
        <label>
          Urgency
          <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
            {urgencyOptions.map((u) => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
        </label>
        <button type="submit">Generate roadmap and daily tasks</button>
      </form>
      {error && <div className="error">{error}</div>}
    </section>
  );
}

function Dashboard({ token, state, setState }) {
  const [chatInput, setChatInput] = useState("");
  const [chatReply, setChatReply] = useState("");
  const [chatError, setChatError] = useState("");

  const pendingTasks = useMemo(() => state.tasks.filter((t) => t.status === "pending"), [state]);

  const updateTaskStatus = async (taskId, status) => {
    const next = await api.feedback(token, [{ task_id: taskId, status }]);
    setState(next);
  };

  const sendDispute = async (taskId) => {
    const next = await api.dispute(token, {
      dispute_type: "difficulty",
      task_id: taskId,
      details: `Task ${taskId} marked as too hard by user`,
    });
    setState(next);
  };

  const sendChat = async (e) => {
    e.preventDefault();
    setChatError("");
    try {
      const result = await api.chat(token, chatInput);
      setChatReply(result.reply);
      setChatInput("");
      const next = await api.state(token);
      setState(next);
    } catch (err) {
      setChatError(err.message);
    }
  };

  return (
    <div className="grid">
      <section className="panel">
        <h2>Execution Snapshot</h2>
        <p><strong>Goal:</strong> {state.goal}</p>
        <p><strong>Stage:</strong> {state.current_stage || "Not started"}</p>
        <p><strong>Constraints:</strong> {state.constraints.daily_time_available} min/day, {state.constraints.urgency_level} urgency</p>
      </section>

      <section className="panel">
        <h2>Roadmap</h2>
        <ul>
          {state.roadmap.map((s) => (
            <li key={s.stage_id}>
              <strong>{s.stage_id}. {s.title}</strong> [{s.status}]<br />
              Skills: {s.required_skills.join(", ")}<br />
              Outcome: {s.measurable_outcome}
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Tasks (max 3/day)</h2>
        <ul>
          {state.tasks.map((t) => (
            <li key={t.task_id}>
              <strong>#{t.task_id}</strong> {t.title} ({t.difficulty}, {t.estimated_time}m) - {t.status}
              {t.status === "pending" && (
                <div className="inline-actions">
                  <button onClick={() => updateTaskStatus(t.task_id, "completed")}>Complete</button>
                  <button onClick={() => updateTaskStatus(t.task_id, "skipped")}>Skip</button>
                  <button onClick={() => updateTaskStatus(t.task_id, "stuck")}>Stuck</button>
                  <button onClick={() => sendDispute(t.task_id)}>Dispute</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Reasoning Chat</h2>
        <form onSubmit={sendChat}>
          <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask why the plan changed, request breakdown, or dispute" />
          <button type="submit">Send</button>
        </form>
        {chatReply && <p className="reply">{chatReply}</p>}
        {chatError && <div className="error">{chatError}</div>}
      </section>

      <section className="panel">
        <h2>Resume Evolution</h2>
        <p><strong>Version:</strong> {state.resume.version}</p>
        <p><strong>Summary:</strong> {state.resume.summary}</p>
        <p><strong>Last Updated:</strong> {state.resume.last_updated}</p>
      </section>

      <section className="panel">
        <h2>Transparency Log</h2>
        <ul>
          {state.change_log.slice().reverse().slice(0, 10).map((c) => (
            <li key={c.change_id}>#{c.change_id} {c.action} - {c.reason}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Skill Confidence</h2>
        <ul>
          {state.skills.map((s) => (
            <li key={s.name}>{s.name}: {s.level} ({Math.round(s.confidence * 100)}%)</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Friction Signals</h2>
        <p>Pending tasks: {pendingTasks.length}</p>
        <p>Logged disputes: {state.disputes.length}</p>
      </section>
    </div>
  );
}

export function App() {
  const [token, setToken] = useState(localStorage.getItem("aces_token") || "");
  const [state, setState] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    (async () => {
      try {
        const snapshot = await api.state(token);
        if (!cancelled) {
          setState(snapshot);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const onLogin = async (sessionToken) => {
    localStorage.setItem("aces_token", sessionToken);
    setToken(sessionToken);
  };

  const refresh = async () => {
    const snapshot = await api.state(token);
    setState(snapshot);
  };

  if (!token) return <main className="app"><Login onLogin={onLogin} /></main>;
  if (!state) {
    return <main className="app"><section className="panel">Loading state...</section>{error && <section className="panel error">{error}</section>}</main>;
  }

  if (!state.onboarding_complete) {
    return <main className="app"><Onboarding token={token} onState={setState} /></main>;
  }

  if (!state.goal || !state.constraints?.daily_time_available || !state.constraints?.urgency_level) {
    return <main className="app"><GoalSetup token={token} onState={setState} /></main>;
  }

  return (
    <main className="app">
      <header className="panel">
        <h1>Agentic Career Execution Dashboard</h1>
        <button onClick={refresh}>Refresh State</button>
      </header>
      <Dashboard token={token} state={state} setState={setState} />
    </main>
  );
}
