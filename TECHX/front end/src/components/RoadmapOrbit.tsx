"use client";

import { UserState } from "@/lib/types";

type Props = {
  state: UserState;
};

function progress(module: any) {
  return module?.progress || 0;
}

export function RoadmapOrbit({ state }: Props) {
  const goalComplete = ["education", "softskills", "certification"].every(
    (name) => (state.module_roadmaps?.[name]?.progress || 0) >= 100
  );

  return (
    <section className="orbit-card">
      <h2>Interactive Goal Roadmap</h2>
      <div className="orbit-map">
        <div className={`goal-core ${goalComplete ? "goal-complete" : ""}`}>
          <span>{state.goal || "Set Your Goal"}</span>
          {goalComplete && <b>⭐ ⭐ ⭐</b>}
        </div>
        <div className="module-node education">
          <h4>Education</h4>
          <p>{progress(state.module_roadmaps.education)}%</p>
        </div>
        <div className="module-node softskills">
          <h4>Softskills</h4>
          <p>{progress(state.module_roadmaps.softskills)}%</p>
        </div>
        <div className="module-node certification">
          <h4>Certification</h4>
          <p>{progress(state.module_roadmaps.certification)}%</p>
        </div>
        <div className="support-node mentorship">Mentorship</div>
        <div className="support-node mocktest">Mock Test</div>
        <div className="support-node mockinterview">Mock Interview</div>
        <svg viewBox="0 0 100 100" className="orbit-lines" aria-hidden="true">
          <path d="M20 20 C40 35, 45 40, 50 50" />
          <path d="M80 20 C65 34, 58 42, 50 50" />
          <path d="M50 85 C50 75, 50 62, 50 50" />
          <path d="M11 55 C25 52, 33 51, 50 50" />
          <path d="M88 56 C73 52, 64 51, 50 50" />
          <path d="M50 11 C50 24, 50 34, 50 50" />
        </svg>
      </div>
    </section>
  );
}
