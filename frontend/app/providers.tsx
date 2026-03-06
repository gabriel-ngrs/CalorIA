"use client";

import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { SessionProvider, useSession } from "next-auth/react";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { setApiToken } from "@/lib/api";

/** Sincroniza o token da sessão React com o cache do axios — sem chamadas HTTP extras */
function SessionSync() {
  const { data: session } = useSession();
  useEffect(() => {
    setApiToken(session?.accessToken ?? null, session?.error);
  }, [session?.accessToken, session?.error]);
  return null;
}

/** Mede o tempo entre mudanças de rota e loga no console */
function NavTimer() {
  const pathname = usePathname();
  const t0 = useRef<number>(0);
  const prev = useRef<string>("");

  useEffect(() => {
    if (prev.current && prev.current !== pathname) {
      const ms = (performance.now() - t0.current).toFixed(0);
      const slow = Number(ms) > 300 ? " ⚠️ LENTO" : "";
      console.log(`[NAV] ${prev.current} → ${pathname}  ${ms}ms${slow}`);
    }
    prev.current = pathname;
    t0.current = performance.now();
  }, [pathname]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onSuccess: (_data, query) => {
            const key = JSON.stringify(query.queryKey);
            console.log(`[QUERY✓] ${key}`);
          },
          onError: (error, query) => {
            const key = JSON.stringify(query.queryKey);
            console.error(`[QUERY✗] ${key}`, (error as Error).message);
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 3 * 60 * 1000,  // 3 minutos — não refetcha ao navegar
            gcTime: 10 * 60 * 1000,    // 10 minutos em cache depois de inativo
            retry: 1,
            refetchOnWindowFocus: false, // não refetcha ao trocar aba
          },
        },
      })
  );

  return (
    <SessionProvider refetchOnWindowFocus={false} refetchInterval={0}>
      <SessionSync />
      <QueryClientProvider client={queryClient}>
        <NavTimer />
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </SessionProvider>
  );
}
