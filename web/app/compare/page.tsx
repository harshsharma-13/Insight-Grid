import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Compare" };
export default function ComparePage() { return <Workspace mode="compare" />; }
