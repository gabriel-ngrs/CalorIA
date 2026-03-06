import axios from "axios";
import { getSession, signOut } from "next-auth/react";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// Cache do token em memória — evita chamar /api/auth/session em cada requisição
let _cache: { token: string | null; error?: string; until: number } | null = null;
let _cacheHit = false;

/** Chamado pelo SessionSync quando a sessão muda — atualiza o cache sem HTTP */
export function setApiToken(token: string | null, error?: string) {
  _cache = { token, error, until: Date.now() + 90 * 1000 };
}

// ─── Interceptor de REQUEST: injeta token + marca timestamp ──────────────────
api.interceptors.request.use(async (config) => {
  const t0 = performance.now();

  let token: string | null = null;
  let error: string | undefined;

  if (_cache && Date.now() < _cache.until) {
    _cacheHit = true;
    token = _cache.token;
    error = _cache.error;
  } else {
    _cacheHit = false;
    const session = await getSession();
    token = session?.accessToken ?? null;
    error = session?.error;
    _cache = { token, error, until: Date.now() + 90 * 1000 };
  }

  const authMs = (performance.now() - t0).toFixed(0);
  const src = _cacheHit ? "cache" : "getSession()";
  console.log(`[API→] ${config.method?.toUpperCase()} ${config.url}  (auth: ${authMs}ms via ${src})`);

  // Guarda o timestamp para calcular duração na resposta
  (config as any)._t0 = performance.now();

  if (error === "RefreshAccessTokenError") {
    await signOut({ redirect: true, callbackUrl: "/login" });
    return config;
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Interceptor de RESPONSE: loga status + duração total ───────────────────
api.interceptors.response.use(
  (response) => {
    const ms = response.config._t0
      ? (performance.now() - (response.config as any)._t0).toFixed(0)
      : "?";
    const slow = Number(ms) > 500 ? " ⚠️ LENTO" : "";
    console.log(
      `[API←] ${response.config.method?.toUpperCase()} ${response.config.url}  ${response.status}  ${ms}ms${slow}`
    );
    return response;
  },
  (error) => {
    const ms = error.config?._t0
      ? (performance.now() - error.config._t0).toFixed(0)
      : "?";
    console.error(
      `[API✗] ${error.config?.method?.toUpperCase()} ${error.config?.url}  ERR  ${ms}ms  —  ${error.message}`
    );
    return Promise.reject(error);
  }
);

export default api;
