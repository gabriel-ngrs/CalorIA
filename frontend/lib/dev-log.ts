/**
 * Log de diagnóstico que só existe em desenvolvimento.
 *
 * Os interceptors de `lib/api.ts` e o `NavTimer`/`QueryCache` de
 * `app/providers.tsx` produziam uma linha por request, navegação e query — em
 * produção também. O padrão de guardar por `NODE_ENV` já existia no arquivo,
 * aplicado ao ReactQueryDevtools; aqui ele vira uma função só.
 *
 * O bundler elimina as chamadas em build de produção, porque `NODE_ENV` é
 * substituído por literal e o `if` vira código morto.
 */
const isDev = process.env.NODE_ENV === "development";

export function devLog(...args: unknown[]): void {
  if (isDev) console.log(...args);
}

/**
 * Erro de diagnóstico. Também só em desenvolvimento: erro que o usuário precisa
 * ver vira toast, não linha de console.
 */
export function devError(...args: unknown[]): void {
  if (isDev) console.error(...args);
}
