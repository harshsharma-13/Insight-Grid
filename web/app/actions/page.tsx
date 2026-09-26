import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Actions" };
export default function ActionsPage() { return <Workspace mode="actions" />; }
