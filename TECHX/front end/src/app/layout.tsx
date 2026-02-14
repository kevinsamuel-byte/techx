import type { Metadata } from "next";
import { Nunito, Sora } from "next/font/google";
import "./globals.css";

const sora = Sora({ subsets: ["latin"], variable: "--font-title" });
const nunito = Nunito({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "Personal Career Navigator",
  description: "Agentic AI career guidance platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${sora.variable} ${nunito.variable}`}>{children}</body>
    </html>
  );
}
