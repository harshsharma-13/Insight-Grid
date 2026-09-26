import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Phones" };
export default function PhonesPage() { return <Workspace mode="phones" />; }
