"use client";

import { FormEvent, useState } from "react";
import { DashboardFrame } from "@/components/DashboardFrame";
import { GuruChat } from "@/components/GuruChat";
import { RoadmapOrbit } from "@/components/RoadmapOrbit";
import { useCareerState } from "@/components/useCareerState";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const { token, state, loading, refresh } = useCareerState();
  const [goal, setGoal] = useState("");
  const [dailyTime, setDailyTime] = useState(90);
  const [urgency, setUrgency] = useState<"low" | "medium" | "high">("medium");
  const [goalSaving, setGoalSaving] = useState(false);
  const [goalError, setGoalError] = useState("");

  if (loading || !state) {
    return <main className="center-screen">Loading dashboard...</main>;
  }

  const saveGoal = async (e: FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setGoalSaving(true);
    setGoalError("");
    try {
      await api.saveGoal(token, goal.trim(), dailyTime, urgency);
      await api.generateRoadmap(token);
      setGoal("");
      await refresh();
    } catch (err) {
      setGoalError(err instanceof Error ? err.message : "Failed to update goal");
    } finally {
      setGoalSaving(false);
    }
  };

  const updateTask = async (module: "education" | "softskills" | "certification", taskId: number, completed: boolean) => {
    await api.updateModuleProgress(token, module, taskId, completed);
    await refresh();
  };

  return (
    <DashboardFrame>
      <div className="grid-panels">
        <RoadmapOrbit state={state} />
        <section className="panel">
          <h3>Career Guidance Resources</h3>
          <ul>
            {state.resources.map((resource) => (
              <li key={resource.url}><a href={resource.url} target="_blank" rel="noreferrer">{resource.title}</a></li>
            ))}
          </ul>
        </section>
        <section className="panel">
          <h3>Set Your Goal</h3>
          <form className="goal-form" onSubmit={saveGoal}>
            <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Ex: AI Product Manager" required />
            <div className="goal-grid">
              <label>
                Daily Minutes
                <input type="number" min={15} max={480} value={dailyTime} onChange={(e) => setDailyTime(Number(e.target.value))} />
              </label>
              <label>
                Urgency
                <select value={urgency} onChange={(e) => setUrgency(e.target.value as "low" | "medium" | "high")}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
            </div>
            <button type="submit" disabled={goalSaving}>{goalSaving ? "Updating..." : "Generate New Roadmap"}</button>
            {goalError ? <p className="error-text">{goalError}</p> : null}
          </form>
        </section>
        <section className="panel">
          <h3>Goal Tracking</h3>
          <p><strong>Goal:</strong> {state.goal || "Not set"}</p>
          <p><strong>Education Progress:</strong> {state.module_roadmaps.education?.progress || 0}%</p>
          <p><strong>Softskills Progress:</strong> {state.module_roadmaps.softskills?.progress || 0}%</p>
          <p><strong>Certification Progress:</strong> {state.module_roadmaps.certification?.progress || 0}%</p>
        </section>
        {(["education", "softskills", "certification"] as const).map((module) => (
          <section className="panel" key={module}>
            <h3>{module[0].toUpperCase() + module.slice(1)} Path</h3>
            {!state.module_roadmaps[module] ? (
              <p>Module removed by AGENT GURU. Ask to add it back if needed.</p>
            ) : (
              <ul>
                {state.module_roadmaps[module]?.tasks?.map((task) => (
                <li key={`${module}-${task.task_id}`}>
                  <label className="task-check">
                    <input type="checkbox" checked={task.completed} onChange={(e) => updateTask(module, task.task_id, e.target.checked)} />
                    {task.title}
                  </label>
                </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
      <GuruChat token={token} onAfterAction={() => refresh()} />
    </DashboardFrame>
  );
}
