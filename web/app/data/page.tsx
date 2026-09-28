import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { DataWorkspace } from "@/app/components/DataWorkspace";

export const metadata: Metadata = { title: "Data Studio" };
export const dynamic = "force-dynamic";

function isLocalHost(host: string) {
  return /^(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i.test(host);
}

export default async function DataPage() {
  const requestHeaders = await headers();
  if (!isLocalHost(requestHeaders.get("host") || "")) notFound();
  return <DataWorkspace />;
}
