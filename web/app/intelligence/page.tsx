import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Intelligence" };
export default function IntelligencePage() { return <Workspace mode="intelligence" />; }
