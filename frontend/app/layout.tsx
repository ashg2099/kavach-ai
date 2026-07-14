import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kavach AI — Protect. Recover. Rebuild.",
  description:
    "India's first AI platform that helps farmers recover crop insurance claims and transition to climate-resilient crops. Powered by LangGraph, RAG, and real government data.",
  keywords: "PMFBY, crop insurance, farmer, AI, India, KrishiShift, agriculture",
  openGraph: {
    title: "Kavach AI",
    description: "Recover what you've lost. Prevent the next loss.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        {children}
      </body>
    </html>
  );
}