import axios from "axios";
import type { AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";
import { getSession, signOut } from "next-auth/react";

interface TimedRequestConfig extends InternalAxiosRequestConfig {
  _t0?: number;
}

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// ─── Cache do token em memória ────────────────────────────────────────────────
// Evita N chamadas HTTP para /api/auth/session por navegação.
let _cache: { token: string | null; error?: string; until: number; accessTokenExpires?: number } | null = null;

// Deduplicação: uma única Promise para getSession() quando múltiplas requests
// disparam simultaneamente sem cache. Evita N×HTTP paralelos para /api/auth/session.
let _pendingSession: Promise<{ token: string | null; error?: string }> | null = null;

// Buffer de renovação proativa: 2 minutos antes do token expirar, força refresh
const PROACTIVE_REFRESH_BUFFER_MS = 2 * 60 * 1000;

/** Chamado pelo SessionSync quando a sessão muda — atualiza o cache sem HTTP */
export function setApiToken(token: string | null, error?: string, accessTokenExpires?: number) {
  _cache = { token, error, until: Date.now() + 90 * 1000, accessTokenExpires };
  _pendingSession = null; // cancela qualquer pending para usar o cache fresco
}

/** Resolve o token: usa cache se fresco e não prestes a expirar, senão faz UMA chamada getSession() compartilhada */
async function resolveToken(): Promise<{ token: string | null; error?: string }> {
  if (_cache && Date.now() < _cache.until) {
    // Refresh proativo: se o access token expira em menos de 2 min, ignora cache
    const expiresAt = _cache.accessTokenExpires;
    if (!expiresAt || Date.now() < expiresAt - PROACTIVE_REFRESH_BUFFER_MS) {
      return { token: _cache.token, error: _cache.error };
    }
    _cache = null; // força refresh
  }
  // Deduplicação: reutiliza Promise em voo se já existir
  if (!_pendingSession) {
    _pendingSession = getSession()
      .then((session) => {
        const result = { token: session?.accessToken ?? null, error: session?.error };
        _cache = { ...result, until: Date.now() + 90 * 1000, accessTokenExpires: session?.accessTokenExpires };
        return result;
      })
      .finally(() => { _pendingSession = null; });
  }
  return _pendingSession;
}

// ─── Interceptor de REQUEST: injeta token + marca timestamp ──────────────────
api.interceptors.request.use(async (config) => {
  const t0 = performance.now();
  const hadCache = _cache && Date.now() < _cache.until;

  const { token, error } = await resolveToken();

  const authMs = (performance.now() - t0).toFixed(0);
  console.log(`[API→] ${config.method?.toUpperCase()} ${config.url}  (auth: ${authMs}ms via ${hadCache ? "cache" : "getSession()"})`);

  (config as TimedRequestConfig)._t0 = performance.now();

  if (error === "RefreshAccessTokenError") {
    await signOut({ redirect: true, callbackUrl: "/login" });
    return config;
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Interceptor de RESPONSE: loga + retry transparente em 401 ───────────────
// Quando o backend retorna 401, invalida o cache e tenta uma vez com token fresco.
// Isso elimina o ciclo "401 → React Query aguarda 1s → retry" que duplicava latência.
api.interceptors.response.use(
  (response) => {
    const timedConfig = response.config as TimedRequestConfig;
    const ms = timedConfig._t0
      ? (performance.now() - timedConfig._t0).toFixed(0)
      : "?";
    const slow = Number(ms) > 500 ? " ⚠️ LENTO" : "";
    console.log(
      `[API←] ${response.config.method?.toUpperCase()} ${response.config.url}  ${response.status}  ${ms}ms${slow}`
    );
    return response;
  },
  async (error) => {
    const ms = error.config?._t0
      ? (performance.now() - error.config._t0).toFixed(0)
      : "?";
    console.error(
      `[API✗] ${error.config?.method?.toUpperCase()} ${error.config?.url}  ERR  ${ms}ms  —  ${error.message}`
    );

    // Retry transparente para 401: invalida cache, busca token fresco, reenvia
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      _cache = null; // invalida cache para forçar novo getSession()
      const { token, error: sessionError } = await resolveToken();
      if (sessionError === "RefreshAccessTokenError") {
        await signOut({ redirect: true, callbackUrl: "/login" });
        return Promise.reject(error);
      }
      if (token) {
        original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
        console.log(`[API↺] 401 → retry com token fresco: ${original.method?.toUpperCase()} ${original.url}`);
        return api(original);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
