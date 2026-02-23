"use client";

import { useState } from "react";
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
import { Trash2 } from "lucide-react";
import { useReminders, useCreateReminder, useDeleteReminder } from "@/lib/hooks/useReminders";
import type { ReminderChannel, ReminderType } from "@/types";

const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const TYPE_LABELS: Record<ReminderType, string> = {
  meal: "Refeição",
  water: "Água",
  weight: "Peso",
  daily_summary: "Resumo diário",
  custom: "Personalizado",
};
const CHANNEL_LABELS: Record<ReminderChannel, string> = {
  telegram: "Telegram",
  whatsapp: "WhatsApp",
};

export default function LembretesPage() {
  const { data: reminders } = useReminders();
  const createReminder = useCreateReminder();
  const deleteReminder = useDeleteReminder();

  const [type, setType] = useState<ReminderType>("meal");
  const [channel, setChannel] = useState<ReminderChannel>("telegram");
  const [time, setTime] = useState("08:00");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createReminder.mutateAsync({
      type,
      channel,
      time,
      days_of_week: [0, 1, 2, 3, 4, 5, 6],
    });
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-2xl font-bold">⏰ Lembretes</h1>
        <p className="text-muted-foreground text-sm">Configure notificações nos seus canais</p>
      </div>

      {/* Lista */}
      {reminders && reminders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Ativos</CardTitle>
          </CardHeader>
          <CardContent className="divide-y">
            {reminders.map((r) => {
              const days =
                r.days_of_week.length === 7
                  ? "Todos os dias"
                  : r.days_of_week.map((d) => DAYS[d]).join(", ");
              return (
                <div key={r.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm font-medium flex items-center gap-1.5">
                      {r.active ? "✅" : "⏸️"} {TYPE_LABELS[r.type]}
                      <Badge variant="secondary" className="text-xs">
                        {CHANNEL_LABELS[r.channel]}
                      </Badge>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {r.time.slice(0, 5)} · {days}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => deleteReminder.mutate(r.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
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
            <div>
              <Label htmlFor="time">Horário</Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="mt-1"
              />
            </div>
            <Button type="submit" disabled={createReminder.isPending} className="w-full">
              {createReminder.isPending ? "Criando..." : "Criar lembrete"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
