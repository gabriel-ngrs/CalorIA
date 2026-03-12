"use client";

import { useQueryClient } from "@tanstack/react-query";
import { PullToRefresh } from "./PullToRefresh";

export function PullToRefreshWrapper({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();

  async function handleRefresh() {
    await qc.invalidateQueries();
  }

  return <PullToRefresh onRefresh={handleRefresh}>{children}</PullToRefresh>;
}
