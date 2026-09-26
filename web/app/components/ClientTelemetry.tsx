"use client";

import { useEffect } from "react";

type Telemetry = { eventType: string; route: string; value?: number; detail?: Record<string, string | number | boolean> };

function report(event: Telemetry) {
  const body = JSON.stringify(event);
  if (navigator.sendBeacon) navigator.sendBeacon("/api/telemetry", new Blob([body], { type: "application/json" }));
  else fetch("/api/telemetry", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => undefined);
}

export function ClientTelemetry() {
  useEffect(() => {
    const route = window.location.pathname;
    report({ eventType: "page_view", route });
    const onLoad = () => {
      const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
      if (navigation) report({ eventType: "navigation_timing", route, value: Math.round(navigation.duration), detail: { responseMs: Math.round(navigation.responseEnd - navigation.requestStart), domMs: Math.round(navigation.domContentLoadedEventEnd - navigation.startTime) } });
    };
    const onError = (event: ErrorEvent) => report({ eventType: "client_error", route, detail: { message: String(event.message || "Unknown client error").slice(0, 300), source: String(event.filename || "browser").split("/").pop() || "browser" } });
    const onRejection = (event: PromiseRejectionEvent) => report({ eventType: "unhandled_rejection", route, detail: { message: String(event.reason instanceof Error ? event.reason.message : event.reason || "Unhandled promise rejection").slice(0, 300) } });
    if (document.readyState === "complete") onLoad(); else window.addEventListener("load", onLoad, { once: true });
    window.addEventListener("error", onError); window.addEventListener("unhandledrejection", onRejection);
    return () => { window.removeEventListener("load", onLoad); window.removeEventListener("error", onError); window.removeEventListener("unhandledrejection", onRejection); };
  }, []);
  return null;
}
