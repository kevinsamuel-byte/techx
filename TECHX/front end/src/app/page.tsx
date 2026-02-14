"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("pcn_token");
    router.replace(token ? "/dashboard" : "/login");
  }, [router]);

  return <main className="center-screen">Loading Personal Career Navigator...</main>;
}
