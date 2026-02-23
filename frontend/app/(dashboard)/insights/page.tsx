"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import api from "@/lib/api";
import type { InsightResponse } from "@/types";

export default function InsightsPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<InsightResponse | null>(null);

  const dailyInsight = useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "daily" });
      return data as InsightResponse;
    },
  });

  const weeklyInsight = useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/api/v1/ai/insights", { type: "weekly" });
      return data as InsightResponse;
    },
  });

  const askQuestion = useMutation({
    mutationFn: async (q: string) => {
      const { data } = await api.post("/api/v1/ai/insights", {
        type: "question",
        question: q,
      });
      return data as InsightResponse;
    },
    onSuccess: (data) => {
      setAnswer(data);
      setQuestion("");
    },
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          Insights IA
        </h1>
        <p className="text-muted-foreground text-sm">Análises personalizadas sobre sua alimentação</p>
      </div>

      {/* Insight diário */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">🌟 Insight do dia</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {dailyInsight.isPending && (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          )}
          {dailyInsight.data && (
            <div className="prose prose-sm max-w-none">
              <p className="text-sm leading-relaxed whitespace-pre-line">{dailyInsight.data.content}</p>
              <p className="text-xs text-muted-foreground mt-2">
                Gerado em {new Date(dailyInsight.data.generated_at).toLocaleString("pt-BR")}
              </p>
            </div>
          )}
          {dailyInsight.isError && (
            <p className="text-sm text-destructive">Não foi possível gerar o insight. Tente novamente.</p>
          )}
          <Button
            onClick={() => dailyInsight.mutate()}
            disabled={dailyInsight.isPending}
            variant={dailyInsight.data ? "outline" : "default"}
            size="sm"
          >
            {dailyInsight.isPending ? "Gerando..." : dailyInsight.data ? "Regenerar" : "Gerar insight"}
          </Button>
        </CardContent>
      </Card>

      {/* Insight semanal */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">📅 Análise semanal</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {weeklyInsight.isPending && (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
              <Skeleton className="h-4 w-3/6" />
            </div>
          )}
          {weeklyInsight.data && (
            <div>
              <p className="text-sm leading-relaxed whitespace-pre-line">{weeklyInsight.data.content}</p>
              <p className="text-xs text-muted-foreground mt-2">
                Gerado em {new Date(weeklyInsight.data.generated_at).toLocaleString("pt-BR")}
              </p>
            </div>
          )}
          {weeklyInsight.isError && (
            <p className="text-sm text-destructive">Erro ao gerar. Tente novamente.</p>
          )}
          <Button
            onClick={() => weeklyInsight.mutate()}
            disabled={weeklyInsight.isPending}
            variant={weeklyInsight.data ? "outline" : "default"}
            size="sm"
          >
            {weeklyInsight.isPending ? "Gerando..." : weeklyInsight.data ? "Regenerar" : "Gerar análise"}
          </Button>
        </CardContent>
      </Card>

      {/* Pergunta livre */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">💬 Pergunte à IA</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {answer && (
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-sm leading-relaxed whitespace-pre-line">{answer.content}</p>
            </div>
          )}
          {askQuestion.isPending && (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (question.trim()) askQuestion.mutate(question.trim());
            }}
            className="flex gap-2"
          >
            <Input
              placeholder="Ex: posso comer pizza hoje? quais alimentos tenho evitado?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" size="icon" disabled={!question.trim() || askQuestion.isPending}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
