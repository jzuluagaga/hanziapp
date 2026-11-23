/**
 * Acceso: Django entrega las credenciales y aquí se guardan en cookies httpOnly.
 * El navegador solo recibe { ok: true } o la clave de error (Docs/10-api.md §2).
 */
import { NextResponse, type NextRequest } from "next/server";
import { API_URL, clearTokens, forwardHeaders, setTokens, unreachable } from "@/lib/server/backend";

type Ctx = { params: Promise<{ action: string }> };

export async function POST(req: NextRequest, { params }: Ctx) {
  const { action } = await params;
  if (action === "logout") {
    const out = NextResponse.json({ ok: true });
    clearTokens(out);
    return out;
  }
  if (action !== "login" && action !== "register") return NextResponse.json({ error: "not_found", detail: {} }, { status: 404 });

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1/auth/${action}`, {
      method: "POST",
      headers: forwardHeaders(req),
      body: await req.text(),
      cache: "no-store",
    });
  } catch {
    return unreachable();
  }
  const data = await res.json().catch(() => ({ error: "generic", detail: {} }));
  if (!res.ok) return NextResponse.json(data, { status: res.status });
  const out = NextResponse.json({ ok: true }, { status: res.status });
  setTokens(out, data);
  return out;
}
