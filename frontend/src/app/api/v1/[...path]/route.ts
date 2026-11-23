/**
 * Reenvío de /api/v1/* a Django con la credencial de la cookie (Docs/10-api.md §2).
 * Si el acceso caducó y hay refresco, renueva una vez y repite la petición.
 */
import { NextResponse, type NextRequest } from "next/server";
import { ACCESS_COOKIE, API_URL, REFRESH_COOKIE, clearTokens, forwardHeaders, refreshTokens, setTokens, unreachable } from "@/lib/server/backend";

type Ctx = { params: Promise<{ path: string[] }> };

async function handle(req: NextRequest, { params }: Ctx) {
  const { path } = await params;
  const url = `${API_URL}/api/v1/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`;
  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await req.text();
  const send = (access?: string) => fetch(url, { method: req.method, headers: forwardHeaders(req, access), body, cache: "no-store" });

  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  let renewed: { access: string; refresh?: string } | null = null;
  let res: Response;
  try {
    res = await send(req.cookies.get(ACCESS_COOKIE)?.value);
    if (res.status === 401 && refresh) {
      renewed = await refreshTokens(refresh);
      if (renewed) res = await send(renewed.access);
    }
  } catch {
    return unreachable();
  }

  const out = new NextResponse(res.status === 204 ? null : await res.arrayBuffer(), {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store" },
  });
  if (renewed) setTokens(out, renewed);
  else if (res.status === 401 && refresh) clearTokens(out);
  return out;
}

export { handle as GET, handle as POST, handle as PUT, handle as PATCH, handle as DELETE };
