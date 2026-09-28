import type { Metadata } from "next";
import "./globals.css";
import { PlatformShell } from "@/app/components/PlatformShell";

export const metadata: Metadata = {
  metadataBase: new URL("https://insight-grid.sharmaharsh0328.chatgpt.site"),
  title: { default: "Insight Grid · Consumer Intelligence", template: "%s · Insight Grid" },
  description: "An evidence-backed smartphone research platform for exploring customer reviews, product trade-offs, competitive signals and action priorities.",
  openGraph: {
    title: "Insight Grid · Consumer Intelligence",
    description: "Explore 2,813 usable customer reviews across 57 smartphones with traceable competitive intelligence and transparent decision tools.",
    images: [{ url: "/og-v3.png", width: 1733, height: 908, alt: "Insight Grid consumer intelligence platform" }],
  },
  twitter: { card: "summary_large_image", title: "Insight Grid · Consumer Intelligence", description: "Evidence-backed smartphone intelligence you can interrogate.", images: ["/og-v3.png"] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><PlatformShell>{children}</PlatformShell></body>
    </html>
  );
}
