"use client";

import { DashboardFrame } from "@/components/DashboardFrame";
import { useCareerState } from "@/components/useCareerState";

export default function CertificationsPage() {
  const { state, loading } = useCareerState();

  if (loading || !state) return <main className="center-screen">Loading certification roadmap...</main>;

  const recommendations = state.module_roadmaps.certification?.recommendations || [];

  return (
    <DashboardFrame>
      <section className="panel large">
        <h2>Certification Programs</h2>
        <p>Roadmap progress: {state.module_roadmaps.certification?.progress || 0}%</p>
        <div className="cert-list">
          {recommendations.map((cert) => (
            <article key={cert.id} className="cert-card">
              <h4>{cert.title}</h4>
              <p>{cert.provider} • Stage: {cert.stage}</p>
              <a href={cert.url} target="_blank" rel="noreferrer">Open Program</a>
            </article>
          ))}
        </div>
      </section>
    </DashboardFrame>
  );
}
