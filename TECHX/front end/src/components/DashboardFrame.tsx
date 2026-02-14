"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

export function DashboardFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("pcn_token");
    router.push("/login");
  };

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <h1>Personal Career Navigator</h1>
        <button onClick={logout}>Logout</button>
      </header>
      <div className="content-wrap">
        <aside className="sidebar">
          <Link className={pathname === "/dashboard" ? "active" : ""} href="/dashboard">Dashboard</Link>
          <Link className={pathname === "/education" ? "active" : ""} href="/education">Education</Link>
          <Link className={pathname === "/softskills" ? "active" : ""} href="/softskills">Softskills</Link>
          <Link className={pathname === "/certifications" ? "active" : ""} href="/certifications">Certifications</Link>
        </aside>
        <section className="page-content">{children}</section>
      </div>
    </main>
  );
}
