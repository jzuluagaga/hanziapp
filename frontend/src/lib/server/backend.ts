/**
 * Puente entre Next y la API de Django (Docs/10-api.md §2). Solo corre en el servidor.
 * El navegador nunca ve la credencial: vive en cookies httpOnly (Q-11).
 */
import type { NextRequest, NextResponse } from "next/server";

export const API_URL = (process.env.HANZI_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
export const ACCESS_COOKIE = "hz_access";
export const REFRESH_COOKIE = "hz_refresh";
const ACCESS_MAX_AGE = 15 * 60; // igual que ACCESS_TOKEN_LIFETIME en Django
const REFRESH_MAX_AGE = 30 * 24 * 3600;

const cookie = (maxAge: number) => ({
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge,
});

export function setTokens(res: NextResponse, tokens: { access?: string; refresh?: string }) {
  if (tokens.access) res.cookies.set(ACCESS_COOKIE, tokens.access, cookie(ACCESS_MAX_AGE));
  if (tokens.refresh) res.cookies.set(REFRESH_COOKIE, tokens.refresh, cookie(REFRESH_MAX_AGE));
}

export function clearTokens(res: NextResponse) {
  res.cookies.set(ACCESS_COOKIE, "", { ...cookie(0), maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, "", { ...cookie(0), maxAge: 0 });
}

/** Cabeceras que viajan a Django: cliente, versión y dirección real del estudiante. */
export function forwardHeaders(req: NextRequest, access?: string): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", Accept: "application/json" };
  const client = req.headers.get("x-client");
  if (client) h["X-Client"] = client;
  const version = req.headers.get("x-app-version");
  if (version) h["X-App-Version"] = version;
  const ip = req.headers.get("x-forwarded-for") ?? req.headers.get("x-real-ip");
  if (ip) h["X-Forwarded-For"] = ip;
  if (access) h.Authorization = `Bearer ${access}`;
  return h;
}

export async function refreshTokens(refresh: string): Promise<{ access: string; refresh?: string } | null> {
  try {
    const r = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
    return r.ok ? await r.json() : null;
  } catch {
    return null;
  }
}

export const unreachable = () =>
  new Response(JSON.stringify({ error: "network", detail: {} }), { status: 502, headers: { "Content-Type": "application/json" } });
