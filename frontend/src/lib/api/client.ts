/**
 * Cliente HTTP del navegador. Habla con las rutas de servidor de Next (`/api/...`),
 * que añaden la credencial desde la cookie httpOnly (Docs/10-api.md §2).
 */
import { config } from "@/lib/config";

export class ApiError extends Error {
  constructor(public status: number, public key: string, public body: Record<string, unknown> = {}) {
    super(key);
  }
}

function clientKind(): string {
  if (typeof window === "undefined") return "";
  return window.matchMedia("(max-width: 767px)").matches ? "mobile_web" : "desktop_web";
}

export async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers: { "Content-Type": "application/json", "X-Client": clientKind(), "X-App-Version": config.appVersion },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "network");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, typeof data?.error === "string" ? data.error : "generic", data);
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", `/api/v1${path}`),
  post: <T>(path: string, body?: unknown) => request<T>("POST", `/api/v1${path}`, body ?? {}),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", `/api/v1${path}`, body ?? {}),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", `/api/v1${path}`, body ?? {}),
  del: <T>(path: string, body?: unknown) => request<T>("DELETE", `/api/v1${path}`, body ?? {}),
  auth: (action: "login" | "register" | "logout", body?: unknown) => request<{ ok: true }>("POST", `/api/auth/${action}`, body ?? {}),
};
