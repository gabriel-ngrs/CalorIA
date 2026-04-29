"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { PullToRefresh } from "./PullToRefresh";

export function PullToRefreshWrapper({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();

  // useCallback estabiliza a referência — PullToRefresh.useEffect não re-executa
  const handleRefresh = useCallback(async () => {
    await qc.invalidateQueries();
  }, [qc]);

  return <PullToRefresh onRefresh={handleRefresh}>{children}</PullToRefresh>;
}
