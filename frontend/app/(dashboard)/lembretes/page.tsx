"use client";

import { useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
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
import { Trash2 as TrashIcon } from "lucide-react";
import {
  useReminders,
  useCreateRemindersBatch,
  useToggleReminder,
  useDeleteReminder,
  type ReminderPayload,
} from "@/lib/hooks/useReminders";
import type { ReminderChannel, ReminderType } from "@/types";

const DAYS_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

const TYPE_LABELS: Record<ReminderType, string> = {
  meal: "🍽️ Refeição",
  water: "💧 Água",
  weight: "⚖️ Peso",
  daily_summary: "📊 Resumo diário",
  custom: "✏️ Personalizado",
};

const CHANNEL_LABELS: Record<ReminderChannel, string> = {
  telegram: "Telegram",
  whatsapp: "WhatsApp",
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

  const [type, setType] = useState<ReminderType>("meal");
  const [channel, setChannel] = useState<ReminderChannel>("telegram");
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4, 5, 6]);

  // Modo: "manual" = lista de horários | "interval" = repetir de X em X horas
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
      channel,
      time: t,
      days_of_week: days,
      message: message || undefined,
    }));

    await createBatch.mutateAsync(payloads);
    setTimes(["08:00"]);
    setMessage("");
  }

  // Agrupa lembretes por tipo+canal para exibição
  const grouped = (reminders ?? []).reduce<Record<string, typeof reminders>>((acc, r) => {
    const key = `${r!.type}-${r!.channel}`;
    if (!acc[key]) acc[key] = [];
    acc[key]!.push(r);
    return acc;
  }, {});

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold">⏰ Lembretes</h1>
        <p className="text-muted-foreground text-sm">Configure notificações nos seus canais</p>
      </div>

      {/* Lista de lembretes */}
      {reminders && reminders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Ativos ({reminders.length})</CardTitle>
          </CardHeader>
          <CardContent className="divide-y">
            {(reminders ?? []).map((r) => {
              const daysLabel =
                r.days_of_week.length === 7
                  ? "Todos os dias"
                  : r.days_of_week.map((d) => DAYS_LABELS[d]).join(", ");
              return (
                <div key={r.id} className="flex items-center justify-between py-2.5 gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-medium flex items-center gap-1.5 flex-wrap">
                      <button
                        onClick={() => toggleReminder.mutate(r.id)}
                        className="text-base leading-none"
                        title={r.active ? "Clique para pausar" : "Clique para ativar"}
                      >
                        {r.active ? "✅" : "⏸️"}
                      </button>
                      {TYPE_LABELS[r.type]}
                      <Badge variant="secondary" className="text-xs">{CHANNEL_LABELS[r.channel]}</Badge>
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {r.time.slice(0, 5)} · {daysLabel}
                    </p>
                    {r.message && (
                      <p className="text-xs text-muted-foreground italic mt-0.5">"{r.message}"</p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => deleteReminder.mutate(r.id)}
                  >
                    <TrashIcon className="h-3.5 w-3.5" />
                  </Button>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Criar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Criar lembrete</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            {/* Tipo e canal */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Tipo</Label>
                <Select value={type} onValueChange={(v) => setType(v as ReminderType)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TYPE_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Canal</Label>
                <Select value={channel} onValueChange={(v) => setChannel(v as ReminderChannel)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="telegram">Telegram</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Dias da semana */}
            <div>
              <Label className="mb-2 block">Dias da semana</Label>
              <div className="flex gap-1 flex-wrap">
                {DAYS_LABELS.map((label, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggleDay(i)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                      days.includes(i)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-transparent text-muted-foreground border-border hover:border-primary/50"
                    }`}
                  >
                    {label}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setDays(days.length === 7 ? [] : [0,1,2,3,4,5,6])}
                  className="px-2.5 py-1 rounded-md text-xs font-medium border border-border text-muted-foreground hover:border-primary/50 transition-colors"
                >
                  {days.length === 7 ? "Nenhum" : "Todos"}
                </button>
              </div>
            </div>

            {/* Modo de horários */}
            <div>
              <Label className="mb-2 block">Horários</Label>
              <div className="flex gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setMode("manual")}
                  className={`flex-1 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                    mode === "manual"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-transparent text-muted-foreground border-border"
                  }`}
                >
                  Horários específicos
                </button>
                <button
                  type="button"
                  onClick={() => setMode("interval")}
                  className={`flex-1 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                    mode === "interval"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-transparent text-muted-foreground border-border"
                  }`}
                >
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
                    <div>
                      <Label className="text-xs">Das</Label>
                      <Input
                        type="time"
                        value={intervalStart}
                        onChange={(e) => setIntervalStart(e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Até</Label>
                      <Input
                        type="time"
                        value={intervalEnd}
                        onChange={(e) => setIntervalEnd(e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">A cada (horas)</Label>
                      <Input
                        type="number"
                        min="1"
                        max="12"
                        value={intervalHours}
                        onChange={(e) => setIntervalHours(Math.max(1, Math.min(12, Number(e.target.value))))}
                        className="mt-1"
                      />
                    </div>
                  </div>
                  {previewTimes.length > 0 && (
                    <p className="text-xs text-muted-foreground">
                      Serão criados {previewTimes.length} lembretes: {previewTimes.join(", ")}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Mensagem personalizada */}
            <div>
              <Label htmlFor="msg">Mensagem personalizada (opcional)</Label>
              <Input
                id="msg"
                placeholder="Ex: Hora de beber água!"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="mt-1"
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
    </div>
  );
}
