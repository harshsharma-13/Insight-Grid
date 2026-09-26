import type { Metadata } from "next";
import { DataWorkspace } from "@/app/components/DataWorkspace";

export const metadata: Metadata = { title: "Data Studio" };
export default function DataPage() { return <DataWorkspace />; }
