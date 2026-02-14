"use client";

import { DashboardFrame } from "@/components/DashboardFrame";
import { useCareerState } from "@/components/useCareerState";

export default function SoftskillsPage() {
  const { state, loading } = useCareerState();

  if (loading || !state) return <main className="center-screen">Loading softskills roadmap...</main>;

  return (
    <DashboardFrame>
      <section className="panel large">
        <h2>Softskills Roadmap</h2>
        <p>
          Build communication, leadership, and interview confidence to unlock your goal:
          {" "}
          <strong>{state.goal || "Not set"}</strong>
        </p>
        <div className="mindmap">
          {state.module_roadmaps.softskills?.tasks.map((task) => (
            <div key={task.task_id} className={`mind-node ${task.completed ? "done" : ""}`}>{task.title}</div>
          ))}
        </div>
      </section>
    </DashboardFrame>
  );
}
