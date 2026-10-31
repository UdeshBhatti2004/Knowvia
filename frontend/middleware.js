import { next } from "@vercel/edge";

export const config = {
  matcher: "/chat",
};

const API_URL = (
  process.env.VITE_API_URL || "https://knowvia-0jje.onrender.com"
).replace(/\/+$/, "");

function toOrigin(entry) {
  const v = String(entry).trim().replace(/\/+$/, "");
  if (!v) return "";
  return v.includes("://") ? v : `https://${v}`;
}

export default async function middleware(request) {
  let ancestors;
  try {
    const key = new URL(request.url).searchParams.get("key");
    const url = key
      ? `${API_URL}/widget/domains?key=${encodeURIComponent(key)}`
      : `${API_URL}/widget/domains`;

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(url, {
      signal: ctrl.signal,
      cache: "no-store",
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`status ${res.status}`);
    const data = await res.json();
    const domains = (data.domains || []).map(toOrigin).filter(Boolean);
    // Empty list = no restriction, no header
    if (domains.length === 0) return next();
    ancestors = ["'self'", ...domains];
  } catch {
    // Unknown key or backend unreachable: fail closed
    ancestors = ["'self'"];
  }
  return next({
    headers: {
      "Content-Security-Policy": `frame-ancestors ${ancestors.join(" ")}`,
    },
  });
}