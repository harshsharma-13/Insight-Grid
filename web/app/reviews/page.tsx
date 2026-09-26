import type { Metadata } from "next";
import { Workspace } from "@/app/components/Workspace";
export const metadata: Metadata = { title: "Reviews" };
export default function ReviewsPage() { return <Workspace mode="reviews" />; }
