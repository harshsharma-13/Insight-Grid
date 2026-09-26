import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Finder" };
export default function FinderPage() { return <Workspace mode="finder" />; }
