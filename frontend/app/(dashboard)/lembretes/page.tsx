"use client";

import { useState } from "react";
import {
  Bell,
  BellOff,
  Pause,
  Play,
  Plus,
  Trash2,
  X,
  Clock,
  Repeat,
  CalendarDays,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  useReminders,
  useCreateRemindersBatch,
  useToggleReminder,
  useDeleteReminder,
  type ReminderPayload,
} from "@/lib/hooks/useReminders";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { ReminderType } from "@/types";

const DAYS_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

const TYPE_LABELS: Record<ReminderType, string> = {
  meal: "Refeição",
  water: "Água",
  weight: "Peso",
  daily_summary: "Resumo diário",
  custom: "Personalizado",
};

const TYPE_COLORS: Record<ReminderType, { dot: string; badge: string }> = {
  meal:          { dot: "bg-orange-500",  badge: "text-orange-400 border-orange-500/30 bg-orange-500/10" },
  water:         { dot: "bg-blue-500",    badge: "text-blue-400 border-blue-500/30 bg-blue-500/10" },
  weight:        { dot: "bg-green-500",   badge: "text-green-400 border-green-500/30 bg-green-500/10" },
  daily_summary: { dot: "bg-purple-500",  badge: "text-purple-400 border-purple-500/30 bg-purple-500/10" },
  custom:        { dot: "bg-yellow-500",  badge: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10" },
};

function generateIntervalTimes(start: string, end: string, intervalHours: number): string[] {
  const times: string[] = [];
  const [startH, startM] = start.split(":").map(Number);
  const [endH, endM] = end.split(":").map(Number);
  const startMin = startH * 60 + startM;
  const endMin = endH * 60 + endM;
  for (let m = startMin; m <= endMin; m += intervalHours * 60) {
    const h = Math.floor(m / 60);
    const min = m % 60;
    times.push(`${String(h).padStart(2, "0")}:${String(min).padStart(2, "0")}`);
  }
  return times;
}

export default function LembretesPage() {
  const { data: reminders } = useReminders();
  const createBatch = useCreateRemindersBatch();
  const toggleReminder = useToggleReminder();
  const deleteReminder = useDeleteReminder();

  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
  const [type, setType] = useState<ReminderType>("meal");
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4, 5, 6]);

  const [mode, setMode] = useState<"manual" | "interval">("manual");
  const [times, setTimes] = useState<string[]>(["08:00"]);
  const [intervalStart, setIntervalStart] = useState("08:00");
  const [intervalEnd, setIntervalEnd] = useState("22:00");
  const [intervalHours, setIntervalHours] = useState(2);
  const [message, setMessage] = useState("");

  function toggleDay(d: number) {
    setDays((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort()
    );
  }

  function addTime() {
    setTimes((prev) => [...prev, "12:00"]);
  }

  function removeTime(i: number) {
    setTimes((prev) => prev.filter((_, idx) => idx !== i));
  }

  function updateTime(i: number, val: string) {
    setTimes((prev) => prev.map((t, idx) => (idx === i ? val : t)));
  }

  const previewTimes =
    mode === "interval"
      ? generateIntervalTimes(intervalStart, intervalEnd, intervalHours)
      : times;

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (days.length === 0 || previewTimes.length === 0) return;

    const payloads: ReminderPayload[] = previewTimes.map((t) => ({
      type,
      time: t,
      days_of_week: days,
      message: message || undefined,
    }));

    await createBatch.mutateAsync(payloads);
    setTimes(["08:00"]);
    setMessage("");
  }

  const activeCount = (reminders ?? []).filter((r) => r.active).length;
  const totalCount = (reminders ?? []).length;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
          <Bell className="h-6 w-6 text-primary" />
          Lembretes
        </h1>
        <p className="text-gray-400 text-sm">Configure notificações via web push</p>
      </div>

      {/* Stat chips */}
      {totalCount > 0 && (
        <div className="flex gap-3 flex-wrap">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-green-500/20 bg-green-500/5 text-sm">
            <Play className="h-3.5 w-3.5 text-green-500 fill-green-500" />
            <span className="font-semibold text-green-400">{activeCount}</span>
            <span className="text-muted-foreground text-xs">ativos</span>
          </div>
          {totalCount - activeCount > 0 && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-muted/30 bg-muted/5 text-sm">
              <BellOff className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="font-semibold">{totalCount - activeCount}</span>
              <span className="text-muted-foreground text-xs">pausados</span>
            </div>
          )}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-primary/20 bg-primary/5 text-sm">
            <Bell className="h-3.5 w-3.5 text-primary" />
            <span className="font-semibold text-primary">{totalCount}</span>
            <span className="text-muted-foreground text-xs">no total</span>
          </div>
        </div>
      )}

      {/* Layout 2 colunas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Coluna esquerda — criar lembrete (2/3) */}
        <Card className="lg:col-span-2 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-1.5">
              <Plus className="h-4 w-4 text-primary" />
              Criar lembrete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-5">

              {/* Tipo */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground uppercase tracking-wide">Tipo</Label>
                <Select value={type} onValueChange={(v) => setType(v as ReminderType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TYPE_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>
                        <span className="flex items-center gap-2">
                          <span className={`inline-block w-2 h-2 rounded-full ${TYPE_COLORS[v as ReminderType].dot}`} />
                          {label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Dias da semana */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <CalendarDays className="h-3 w-3" />
                  Dias da semana
                </Label>
                <div className="flex gap-1.5 flex-wrap">
                  {DAYS_LABELS.map((label, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => toggleDay(i)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-150 cursor-pointer ${
                        days.includes(i)
                          ? "bg-primary/20 text-primary border-primary/50 ring-1 ring-primary/30"
                          : "bg-transparent text-muted-foreground border-border hover:border-primary/40 hover:text-foreground"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setDays(days.length === 7 ? [] : [0, 1, 2, 3, 4, 5, 6])}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium border border-border text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors cursor-pointer"
                  >
                    {days.length === 7 ? "Nenhum" : "Todos"}
                  </button>
                </div>
              </div>

              {/* Modo de horários */}
              <div className="space-y-3">
                <Label className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <Clock className="h-3 w-3" />
                  Horários
                </Label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setMode("manual")}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-all duration-150 cursor-pointer flex items-center justify-center gap-1.5 ${
                      mode === "manual"
                        ? "bg-primary/20 text-primary border-primary/50 ring-1 ring-primary/30"
                        : "bg-transparent text-muted-foreground border-border hover:border-primary/40"
                    }`}
                  >
                    <Clock className="h-3.5 w-3.5" />
                    Horários específicos
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode("interval")}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-all duration-150 cursor-pointer flex items-center justify-center gap-1.5 ${
                      mode === "interval"
                        ? "bg-primary/20 text-primary border-primary/50 ring-1 ring-primary/30"
                        : "bg-transparent text-muted-foreground border-border hover:border-primary/40"
                    }`}
                  >
                    <Repeat className="h-3.5 w-3.5" />
                    Repetir de X em X horas
                  </button>
                </div>

                {mode === "manual" && (
                  <div className="space-y-2">
                    {times.map((t, i) => (
                      <div key={i} className="flex gap-2 items-center">
                        <Input
                          type="time"
                          value={t}
                          onChange={(e) => updateTime(i, e.target.value)}
                          className="flex-1"
                        />
                        {times.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-9 w-9 shrink-0 text-muted-foreground hover:text-destructive"
                            onClick={() => removeTime(i)}
                          >
                            <X className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1.5 w-full"
                      onClick={addTime}
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Adicionar horário
                    </Button>
                  </div>
                )}

                {mode === "interval" && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="space-y-1.5">
                        <Label className="text-xs">Das</Label>
                        <Input
                          type="time"
                          value={intervalStart}
                          onChange={(e) => setIntervalStart(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-xs">Até</Label>
                        <Input
                          type="time"
                          value={intervalEnd}
                          onChange={(e) => setIntervalEnd(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-xs">A cada (h)</Label>
                        <Input
                          type="number"
                          min="1"
                          max="12"
                          value={intervalHours}
                          onChange={(e) => setIntervalHours(Math.max(1, Math.min(12, Number(e.target.value))))}
                        />
                      </div>
                    </div>
                    {previewTimes.length > 0 && (
                      <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
                        <p className="text-xs text-muted-foreground mb-1">
                          {previewTimes.length} lembrete{previewTimes.length > 1 ? "s" : ""} serão criados:
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {previewTimes.map((t) => (
                            <span key={t} className="text-xs font-mono text-primary bg-primary/10 border border-primary/20 rounded px-1.5 py-0.5">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Mensagem personalizada */}
              <div className="space-y-1.5">
                <Label htmlFor="msg" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <MessageSquare className="h-3 w-3" />
                  Mensagem personalizada (opcional)
                </Label>
                <Input
                  id="msg"
                  placeholder="Ex: Hora de beber água!"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={createBatch.isPending || days.length === 0 || previewTimes.length === 0}
              >
                {createBatch.isPending
                  ? "Criando..."
                  : previewTimes.length > 1
                  ? `Criar ${previewTimes.length} lembretes`
                  : "Criar lembrete"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Coluna direita — lista de lembretes ativos (1/3) */}
        <div className="space-y-3">
          {reminders && reminders.length > 0 ? (
            <>
              <p className="text-xs text-muted-foreground uppercase tracking-wide px-1">
                Configurados ({totalCount})
              </p>
              {reminders.map((r) => {
                const daysLabel =
                  r.days_of_week.length === 7
                    ? "Todos os dias"
                    : r.days_of_week.map((d) => DAYS_LABELS[d]).join(", ");
                const colors = TYPE_COLORS[r.type];
                return (
                  <Card
                    key={r.id}
                    className={`transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${
                      r.active ? "hover:border-green-500/30" : "hover:border-muted/50 opacity-60"
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap mb-1">
                            <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${colors.dot}`} />
                            <span className="text-sm font-medium">{TYPE_LABELS[r.type]}</span>
                            <Badge
                              variant="outline"
                              className={`text-[10px] px-1.5 py-0 h-4 border ${colors.badge}`}
                            >
                              {TYPE_LABELS[r.type]}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                            <Clock className="h-3 w-3 shrink-0" />
                            <span className="font-mono font-medium">{r.time.slice(0, 5)}</span>
                            <span>·</span>
                            <span className="truncate">{daysLabel}</span>
                          </div>
                          {r.message && (
                            <p className="text-xs text-muted-foreground italic mt-1 truncate">
                              &ldquo;{r.message}&rdquo;
                            </p>
                          )}
                        </div>
                        <div className="flex flex-col gap-1 shrink-0">
                          <button
                            onClick={() => toggleReminder.mutate(r.id)}
                            className="cursor-pointer p-1.5 rounded-md hover:bg-muted/50 transition-colors"
                            title={r.active ? "Pausar" : "Ativar"}
                          >
                            {r.active
                              ? <Play className="h-3.5 w-3.5 text-green-500 fill-green-500" />
                              : <Pause className="h-3.5 w-3.5 text-muted-foreground" />
                            }
                          </button>
                          <button
                            onClick={() => setPendingDeleteId(r.id)}
                            className="cursor-pointer p-1.5 rounded-md hover:bg-destructive/10 transition-colors text-muted-foreground hover:text-destructive"
                            title="Excluir"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </>
          ) : (
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
              <CardContent className="pt-10 pb-10 flex flex-col items-center gap-3 text-center">
                <span className="flex items-center justify-center w-12 h-12 rounded-full bg-muted/30">
                  <BellOff className="h-6 w-6 text-muted-foreground/50" />
                </span>
                <p className="text-sm text-muted-foreground">Nenhum lembrete configurado</p>
                <p className="text-xs text-muted-foreground/70">Crie seu primeiro lembrete ao lado</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      <AlertDialog open={pendingDeleteId !== null} onOpenChange={(open: boolean) => { if (!open) setPendingDeleteId(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir lembrete?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={() => { if (pendingDeleteId !== null) { deleteReminder.mutate(pendingDeleteId); setPendingDeleteId(null); } }}>
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
