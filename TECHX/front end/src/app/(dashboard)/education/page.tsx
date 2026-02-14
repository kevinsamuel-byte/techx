"use client";

import { DashboardFrame } from "@/components/DashboardFrame";
import { useCareerState } from "@/components/useCareerState";

export default function EducationPage() {
  const { state, loading } = useCareerState();

  if (loading || !state) return <main className="center-screen">Loading education roadmap...</main>;

  return (
    <DashboardFrame>
      <section className="panel large">
        <h2>Education Roadmap</h2>
        <p>Generated from resume + goal: <strong>{state.goal || "Not set"}</strong></p>
        <div className="mindmap">
          {state.module_roadmaps.education?.tasks?.map((task) => (
            <div key={task.task_id} className={`mind-node ${task.completed ? "done" : ""}`}>{task.title}</div>
          ))}
        </div>
      </section>
    </DashboardFrame>
  );
}
