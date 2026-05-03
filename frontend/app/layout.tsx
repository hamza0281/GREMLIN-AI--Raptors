import type { Metadata } from "next";
import "./globals.css";
import AnimatedBackground from "./AnimatedBackground";

export const metadata: Metadata = {
  title: "GremlinAI | The AI That Breaks Your App Before Users Do",
  description: "Autonomous chaos testing powered by a 0.5B LLM. Gremlins break your app — before your users do.",
  keywords: "chaos testing, QA automation, AI testing, fuzzing, security testing, bug hunting, GremlinAI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* Premium Canvas Background */}
        <AnimatedBackground />
        {/* Main Content */}
        <div style={{ position: "relative", zIndex: 1 }}>
          {children}
        </div>
      </body>
    </html>
  );
}
