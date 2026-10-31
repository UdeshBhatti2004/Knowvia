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

export default async function middleware() {
  let ancestors;
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(`${API_URL}/widget/domains`, {
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
    // Backend unreachable: fail closed
    ancestors = ["'self'"];
  }
  return next({
    headers: {
      "Content-Security-Policy": `frame-ancestors ${ancestors.join(" ")}`,
    },
  });
}