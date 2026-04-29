"use client";

import { useState } from "react";
import { CheckCircle2, Send, Sparkles, RefreshCw, ChevronDown, ChevronUp, Utensils, TrendingUp, TrendingDown, Bell, Target, BarChart3, CalendarDays, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  useDailyInsight,
  useWeeklyInsight,
  useAskQuestion,
  useMealSuggestion,
  useEatingPatterns,
  useNutritionalAlerts,
  useGoalAdjustment,
  useMonthlyReport,
} from "@/lib/hooks/useAI";
import type { MonthlyReport, NutritionalAlertsResponse, EatingPattern, MealSuggestion, GoalAdjustmentSuggestion } from "@/types";

const MONTH_NAMES = [
  "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
  "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro",
];

const SEVERITY_CONFIG = {
  high:   { label: "Alta",   color: "text-red-500",    bg: "bg-red-500/10",    border: "border-red-500/30" },
  medium: { label: "Média",  color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30" },
  low:    { label: "Baixa",  color: "text-blue-400",   bg: "bg-blue-400/10",   border: "border-blue-400/30" },
};

function InsightText({ content }: { content: string }) {
  return (
    <p className="text-sm leading-relaxed whitespace-pre-line text-foreground/90">{content}</p>
  );
}

function LoadingLines({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4" style={{ width: `${100 - i * 12}%` }} />
      ))}
    </div>
  );
}

function SectionHeader({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <CardTitle className="text-sm flex items-center gap-2">
      {icon}
      <div>
        <span>{title}</span>
        <p className="text-xs text-muted-foreground font-normal mt-0.5">{description}</p>
      </div>
    </CardTitle>
  );
}

export default function InsightsPage() {
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState<{ q: string; a: string }[]>([]);
  const [patternDays, setPatternDays] = useState(30);
  const [alertDays, setAlertDays] = useState(14);
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());

  const dailyInsight  = useDailyInsight();
  const weeklyInsight = useWeeklyInsight();
  const askQuestion   = useAskQuestion();
  const mealSuggestion = useMealSuggestion();
  const eatingPatterns = useEatingPatterns(patternDays);
  const nutritionalAlerts = useNutritionalAlerts(alertDays);
  const goalAdjustment = useGoalAdjustment();
  const monthlyReport  = useMonthlyReport();

  function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    const q = question.trim();
    setQuestion("");
    askQuestion.mutate(q, {
      onSuccess: (data) => {
        setChatHistory((prev) => [...prev, { q, a: data.content }]);
      },
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          Insights IA
        </h1>
        <p className="text-gray-400 text-sm">Análises personalizadas sobre sua alimentação</p>
      </div>

      {/* ── Seção: Hoje ─────────────────────────────────────────────────── */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-0.5">Hoje</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

      {/* ── Insight diário ─────────────────────────────────────────────── */}
      <Card className="border-l-4 border-emerald-400 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl">
        <CardHeader>
          <div className="flex items-start justify-between">
            <SectionHeader
              icon={<Sparkles className="h-4 w-4 text-yellow-400" />}
              title="Insight do dia"
              description="Análise rápida com base nos seus dados de hoje"
            />
            <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 shrink-0">
              ✨ Gerado por IA
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {dailyInsight.isPending && <LoadingLines />}
          {dailyInsight.data && <InsightText content={dailyInsight.data.content} />}
          {dailyInsight.isError && (
            <p className="text-sm text-destructive">Não foi possível gerar o insight. Tente novamente.</p>
          )}
          <Button
            onClick={() => dailyInsight.mutate()}
            disabled={dailyInsight.isPending}
            variant={dailyInsight.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {dailyInsight.isPending ? "Gerando..." : (
              <>{dailyInsight.data ? <RefreshCw className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}{dailyInsight.data ? "Regenerar" : "Gerar insight"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* ── Sugestão de refeição ───────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-400/30">
        <CardHeader>
          <SectionHeader
            icon={<Utensils className="h-4 w-4 text-orange-400" />}
            title="Sugestão de refeição"
            description="O que comer com base nas calorias restantes do dia"
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {mealSuggestion.isPending && <LoadingLines lines={4} />}
          {mealSuggestion.data && <MealSuggestionCard data={mealSuggestion.data} />}
          {mealSuggestion.isError && (
            <p className="text-sm text-destructive">Erro ao gerar sugestão. Tente novamente.</p>
          )}
          <Button
            onClick={() => mealSuggestion.mutate()}
            disabled={mealSuggestion.isPending}
            variant={mealSuggestion.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {mealSuggestion.isPending ? "Gerando..." : (
              <>{mealSuggestion.data ? <RefreshCw className="h-3.5 w-3.5" /> : <Utensils className="h-3.5 w-3.5" />}{mealSuggestion.data ? "Nova sugestão" : "Sugerir refeição"}</>
            )}
          </Button>
        </CardContent>
      </Card>

        </div>{/* fim grid 2 colunas */}
      </div>{/* fim seção Hoje */}

      {/* ── Seção: Análise de período ───────────────────────────────────── */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-0.5">Análise de período</p>

      {/* ── Alertas nutricionais ──────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-400/30">
        <CardHeader className="flex flex-row items-start justify-between gap-2">
          <SectionHeader
            icon={<Bell className="h-4 w-4 text-yellow-400" />}
            title="Alertas nutricionais"
            description="Deficiências recorrentes detectadas pela IA"
          />
          <PeriodSelector
            value={alertDays}
            options={[7, 14, 30]}
            onChange={setAlertDays}
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {nutritionalAlerts.isPending && <LoadingLines lines={4} />}
          {nutritionalAlerts.data && <NutritionalAlertsCard data={nutritionalAlerts.data} requestedDays={alertDays} />}
          {nutritionalAlerts.isError && (
            <p className="text-sm text-destructive">Erro ao verificar alertas. Tente novamente.</p>
          )}
          <Button
            onClick={() => nutritionalAlerts.mutate(alertDays)}
            disabled={nutritionalAlerts.isPending}
            variant={nutritionalAlerts.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {nutritionalAlerts.isPending ? "Analisando..." : (
              <>{nutritionalAlerts.data ? <RefreshCw className="h-3.5 w-3.5" /> : <Bell className="h-3.5 w-3.5" />}{nutritionalAlerts.data ? "Reanalisar" : "Verificar alertas"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* ── Padrões alimentares ───────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
        <CardHeader className="flex flex-row items-start justify-between gap-2">
          <SectionHeader
            icon={<TrendingUp className="h-4 w-4 text-primary" />}
            title="Padrões alimentares"
            description="Hábitos e alimentos mais frequentes no período"
          />
          <PeriodSelector
            value={patternDays}
            options={[7, 14, 30]}
            onChange={setPatternDays}
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {eatingPatterns.isPending && <LoadingLines lines={4} />}
          {eatingPatterns.data && <EatingPatternCard data={eatingPatterns.data} />}
          {eatingPatterns.isError && (
            <p className="text-sm text-destructive">Erro ao analisar padrões. Tente novamente.</p>
          )}
          <Button
            onClick={() => eatingPatterns.mutate(patternDays)}
            disabled={eatingPatterns.isPending}
            variant={eatingPatterns.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {eatingPatterns.isPending ? "Analisando..." : (
              <>{eatingPatterns.data ? <RefreshCw className="h-3.5 w-3.5" /> : <TrendingUp className="h-3.5 w-3.5" />}{eatingPatterns.data ? "Reanalisar" : "Analisar padrões"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      </div>{/* fim seção Análise de período */}

      {/* ── Seção: Relatórios ──────────────────────────────────────────── */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-0.5">Relatórios</p>

      {/* ── Análise semanal ───────────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-400/30">
        <CardHeader>
          <SectionHeader
            icon={<CalendarDays className="h-4 w-4 text-blue-400" />}
            title="Análise semanal"
            description="Resumo detalhado dos últimos 7 dias"
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {weeklyInsight.isPending && <LoadingLines lines={5} />}
          {weeklyInsight.data && <InsightText content={weeklyInsight.data.content} />}
          {weeklyInsight.isError && (
            <p className="text-sm text-destructive">Erro ao gerar. Tente novamente.</p>
          )}
          <Button
            onClick={() => weeklyInsight.mutate()}
            disabled={weeklyInsight.isPending}
            variant={weeklyInsight.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {weeklyInsight.isPending ? "Gerando..." : (
              <>{weeklyInsight.data ? <RefreshCw className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}{weeklyInsight.data ? "Regenerar" : "Gerar análise"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* ── Ajuste de metas ───────────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-emerald-400/30">
        <CardHeader>
          <SectionHeader
            icon={<Target className="h-4 w-4 text-emerald-400" />}
            title="Ajuste de metas"
            description="Avalia se suas metas estão alinhadas com a tendência real"
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {goalAdjustment.isPending && <LoadingLines lines={3} />}
          {goalAdjustment.data && <GoalAdjustmentCard data={goalAdjustment.data} />}
          {goalAdjustment.isError && (
            <p className="text-sm text-destructive">Erro ao avaliar metas. Tente novamente.</p>
          )}
          <Button
            onClick={() => goalAdjustment.mutate()}
            disabled={goalAdjustment.isPending}
            variant={goalAdjustment.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {goalAdjustment.isPending ? "Avaliando..." : (
              <>{goalAdjustment.data ? <RefreshCw className="h-3.5 w-3.5" /> : <Target className="h-3.5 w-3.5" />}{goalAdjustment.data ? "Reavaliar" : "Avaliar metas"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* ── Relatório mensal ──────────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-purple-400/30">
        <CardHeader className="flex flex-row items-start justify-between gap-2">
          <SectionHeader
            icon={<BarChart3 className="h-4 w-4 text-purple-400" />}
            title="Relatório mensal"
            description="Score de aderência e análise completa do mês"
          />
          <div className="flex gap-1 shrink-0">
            <select
              value={reportMonth}
              onChange={(e) => setReportMonth(Number(e.target.value))}
              className="text-xs bg-muted border border-border rounded px-1.5 py-1"
            >
              {MONTH_NAMES.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
            <select
              value={reportYear}
              onChange={(e) => setReportYear(Number(e.target.value))}
              className="text-xs bg-muted border border-border rounded px-1.5 py-1"
            >
              {[2024, 2025, 2026].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {monthlyReport.isPending && <LoadingLines lines={6} />}
          {monthlyReport.data && <MonthlyReportCard data={monthlyReport.data} />}
          {monthlyReport.isError && (
            <p className="text-sm text-destructive">Erro ao gerar relatório. Tente novamente.</p>
          )}
          <Button
            onClick={() => monthlyReport.mutate({ month: reportMonth, year: reportYear })}
            disabled={monthlyReport.isPending}
            variant={monthlyReport.data ? "outline" : "default"}
            size="sm"
            className="gap-1.5"
          >
            {monthlyReport.isPending ? "Gerando..." : (
              <>{monthlyReport.data ? <RefreshCw className="h-3.5 w-3.5" /> : <BarChart3 className="h-3.5 w-3.5" />}{monthlyReport.data ? "Regenerar" : "Gerar relatório"}</>
            )}
          </Button>
        </CardContent>
      </Card>

      </div>{/* fim seção Relatórios */}

      {/* ── Seção: Chat ────────────────────────────────────────────────── */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-0.5">Pergunte à IA</p>

      {/* ── Pergunte à IA ─────────────────────────────────────────────── */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
        <CardHeader>
          <SectionHeader
            icon={<Send className="h-4 w-4 text-primary" />}
            title="Pergunte à IA"
            description="Faça qualquer pergunta sobre sua alimentação"
          />
        </CardHeader>
        <CardContent className="space-y-3">
          {chatHistory.length > 0 && (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {chatHistory.map((item, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-end">
                    <div className="bg-primary/10 border border-primary/20 rounded-lg px-3 py-2 max-w-[85%]">
                      <p className="text-xs text-primary font-medium">{item.q}</p>
                    </div>
                  </div>
                  <div className="bg-muted/50 rounded-lg px-3 py-2">
                    <p className="text-sm leading-relaxed whitespace-pre-line">{item.a}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          {askQuestion.isPending && (
            <div className="bg-muted/50 rounded-lg px-3 py-2">
              <LoadingLines lines={2} />
            </div>
          )}
          {askQuestion.isError && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
              <p className="text-sm text-destructive">Não foi possível obter resposta da IA. Tente novamente.</p>
            </div>
          )}
          <form onSubmit={handleAsk} className="flex gap-2">
            <Input
              placeholder="Ex: posso comer pizza hoje? quais alimentos tenho evitado?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" size="icon" disabled={!question.trim() || askQuestion.isPending} aria-label="Enviar pergunta">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
      </div>{/* fim seção Chat */}
    </div>
  );
}

// ── Sub-componentes ────────────────────────────────────────────────────────

function PeriodSelector({
  value,
  options,
  onChange,
}: {
  value: number;
  options: number[];
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex gap-1 shrink-0">
      {options.map((d) => (
        <button
          key={d}
          type="button"
          onClick={() => onChange(d)}
          className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${
            value === d
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-transparent text-muted-foreground border-border hover:border-primary/50"
          }`}
        >
          {d}d
        </button>
      ))}
    </div>
  );
}

function MealSuggestionCard({ data }: { data: MealSuggestion }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-sm">{data.name}</p>
          <p className="text-xs text-muted-foreground">{data.description}</p>
        </div>
        <Badge variant="secondary" className="shrink-0 text-xs">{data.estimated_calories.toFixed(0)} kcal</Badge>
      </div>
      {data.items.length > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {expanded ? "Ocultar ingredientes" : `Ver ${data.items.length} ingredientes`}
        </button>
      )}
      {expanded && (
        <div className="space-y-1 pl-2 border-l border-border">
          {data.items.map((item, i) => (
            <div key={i} className="flex items-center justify-between text-xs">
              <span className="text-foreground/80">{item.food_name} — {item.quantity}{item.unit}</span>
              <span className="text-muted-foreground">{item.estimated_calories.toFixed(0)} kcal</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function NutritionalAlertsCard({ data, requestedDays }: { data: NutritionalAlertsResponse; requestedDays: number }) {
  const daysLabel = data.days_analyzed > 0 ? data.days_analyzed : requestedDays;
  return (
    <div className="space-y-3">
      {data.alerts.length === 0 ? (
        <p className="text-sm text-emerald-500 flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4" /> Nenhuma deficiência significativa detectada nos últimos {daysLabel} dias.</p>
      ) : (
        <div className="space-y-2">
          {data.alerts.map((alert, i) => {
            const cfg = SEVERITY_CONFIG[alert.severity];
            return (
              <div key={i} className={`rounded-lg border px-3 py-2 ${cfg.bg} ${cfg.border}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{alert.nutrient}</span>
                  <Badge className={`text-xs ${cfg.color} bg-transparent border ${cfg.border}`}>
                    {cfg.label}
                  </Badge>
                </div>
                <div className="flex gap-3 text-xs text-muted-foreground">
                  <span>Média: <strong className={cfg.color}>{alert.average_daily.toFixed(1)}{alert.unit}</strong></span>
                  <span>Mínimo: {alert.recommended_min.toFixed(1)}{alert.unit}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
      <p className="text-xs text-muted-foreground leading-relaxed">{data.analysis}</p>
    </div>
  );
}

function EatingPatternCard({ data }: { data: EatingPattern }) {
  return (
    <div className="space-y-3">
      <InsightText content={data.analysis} />
      {data.frequent_foods.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-1.5">Alimentos mais frequentes:</p>
          <div className="flex flex-wrap gap-1.5">
            {data.frequent_foods.map((food, i) => (
              <Badge key={i} variant="secondary" className="text-xs">{food}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GoalAdjustmentCard({ data }: { data: GoalAdjustmentSuggestion }) {
  const trend = data.weight_trend_kg_per_week;
  const trendLabel = trend === null
    ? "Sem dados de peso"
    : trend > 0
      ? `+${trend.toFixed(2)} kg/semana`
      : `${trend.toFixed(2)} kg/semana`;

  return (
    <div className="space-y-3">
      {data.adjustment_recommended && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg px-3 py-2">
          <p className="text-xs text-yellow-500 font-medium mb-1">Ajuste recomendado</p>
          {data.current_calorie_goal && data.suggested_calorie_goal && (
            <p className="text-sm">
              Meta atual: <strong>{data.current_calorie_goal} kcal</strong>
              {" → "}
              Sugestão: <strong className="text-primary">{data.suggested_calorie_goal} kcal</strong>
            </p>
          )}
        </div>
      )}
      {trend !== null && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Tendência de peso:</span>
          <span className={trend > 0 ? "text-orange-400" : trend < 0 ? "text-emerald-400" : "text-muted-foreground"}>
            {trendLabel}
          </span>
        </div>
      )}
      <InsightText content={data.suggestion} />
    </div>
  );
}

function MonthlyReportCard({ data }: { data: MonthlyReport }) {
  const score = data.adherence_score;
  const scoreColor = score >= 80 ? "text-emerald-400" : score >= 50 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="space-y-4">
      {/* Score principal */}
      <div className="flex items-center gap-4">
        <div className="text-center">
          <p className={`text-3xl font-bold ${scoreColor}`}>{score.toFixed(0)}%</p>
          <p className="text-xs text-muted-foreground">Aderência</p>
        </div>
        <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-muted-foreground">Dias registrados</span>
          <span className="font-medium">{data.total_days_logged}</span>
          <span className="text-muted-foreground">Média calorias</span>
          <span className="font-medium">{data.avg_daily_calories.toFixed(0)} kcal</span>
          <span className="text-muted-foreground">Média proteína</span>
          <span className="font-medium">{data.avg_daily_protein.toFixed(0)}g</span>
          <span className="text-muted-foreground">Média carbs</span>
          <span className="font-medium">{data.avg_daily_carbs.toFixed(0)}g</span>
        </div>
      </div>

      {/* Melhor e pior semana */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2.5">
          <p className="text-xs text-emerald-400 font-medium mb-1 flex items-center gap-1"><Trophy className="h-3 w-3" /> Melhor semana</p>
          <p className="text-xs text-muted-foreground">Semana {data.best_week.week_number}</p>
          <p className="text-xs"><strong>{data.best_week.adherence_pct.toFixed(0)}%</strong> aderência</p>
          <p className="text-xs">{data.best_week.days_logged} dias registrados</p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-2.5">
          <p className="text-xs text-red-400 font-medium mb-1 flex items-center gap-1"><TrendingDown className="h-3 w-3" /> Semana mais fraca</p>
          <p className="text-xs text-muted-foreground">Semana {data.worst_week.week_number}</p>
          <p className="text-xs"><strong>{data.worst_week.adherence_pct.toFixed(0)}%</strong> aderência</p>
          <p className="text-xs">{data.worst_week.days_logged} dias registrados</p>
        </div>
      </div>

      {/* Análise da IA */}
      <InsightText content={data.analysis} />
    </div>
  );
}
