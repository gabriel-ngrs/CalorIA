"use client";

import { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Bot,
  CalendarIcon,
  Check,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  Droplets,
  Flame,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  UtensilsCrossed,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import dynamic from "next/dynamic";
// Import direto do arquivo de locale — não carrega o barrel inteiro de date-fns
import ptBR from "date-fns/locale/pt-BR";

// Calendar (react-day-picker) carregado sob demanda — não entra no bundle inicial da página
const Calendar = dynamic(
  () => import("@/components/ui/calendar").then((m) => m.Calendar),
  { ssr: false, loading: () => <Skeleton className="h-[280px] w-full" /> }
);
import { useAnalyzeMeal, useCreateMeal, useDeleteMeal, useMeals, useUpdateMeal } from "@/lib/hooks/useMeals";
import type { Meal, MealItemCreate, MealType, ParsedFoodItem } from "@/types";

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: "Café da manhã",
  morning_snack: "Lanche da manhã",
  lunch: "Almoço",
  afternoon_snack: "Lanche da tarde",
  dinner: "Jantar",
  supper: "Ceia",
  snack: "Lanche",
  pre_workout: "Pré-treino",
  post_workout: "Pós-treino",
  supplement: "Suplemento",
  dessert: "Sobremesa",
};

// Color accent classes for left border + icon bg
const MEAL_ACCENT: Record<MealType, { border: string; bg: string; text: string }> = {
  breakfast:       { border: "border-l-amber-500",  bg: "bg-amber-500/15",  text: "text-amber-400" },
  morning_snack:   { border: "border-l-yellow-400", bg: "bg-yellow-400/15", text: "text-yellow-400" },
  lunch:           { border: "border-l-orange-500", bg: "bg-orange-500/15", text: "text-orange-400" },
  afternoon_snack: { border: "border-l-green-500",  bg: "bg-green-500/15",  text: "text-green-400" },
  dinner:          { border: "border-l-indigo-400", bg: "bg-indigo-400/15", text: "text-indigo-400" },
  supper:          { border: "border-l-violet-400", bg: "bg-violet-400/15", text: "text-violet-400" },
  snack:           { border: "border-l-teal-400",   bg: "bg-teal-400/15",   text: "text-teal-400" },
  pre_workout:     { border: "border-l-red-500",    bg: "bg-red-500/15",    text: "text-red-400" },
  post_workout:    { border: "border-l-blue-500",   bg: "bg-blue-500/15",   text: "text-blue-400" },
  supplement:      { border: "border-l-purple-400", bg: "bg-purple-400/15", text: "text-purple-400" },
  dessert:         { border: "border-l-pink-400",   bg: "bg-pink-400/15",   text: "text-pink-400" },
};

const SOURCE_LABELS: Record<string, { label: string; icon: React.ReactNode }> = {
  manual:   { label: "Manual",   icon: <Pencil className="h-3 w-3" /> },
  telegram: { label: "Telegram", icon: <Bot className="h-3 w-3" /> },
  whatsapp: { label: "WhatsApp", icon: <Bot className="h-3 w-3" /> },
};

/** Retorna a data local do sistema no formato YYYY-MM-DD (sem depender de UTC). */
function getLocalToday(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr + "T12:00");
  d.setDate(d.getDate() + n);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatDateDisplay(dateStr: string): string {
  return new Date(dateStr + "T12:00").toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });
}

function isToday(dateStr: string): boolean {
  return dateStr === getLocalToday();
}

// ── Macro pill ────────────────────────────────────────────────────────────────

function MacroPill({ icon, value, unit, color }: {
  icon: React.ReactNode;
  value: number;
  unit: string;
  color: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", color)}>
      {icon}
      {value.toFixed(0)}{unit}
    </span>
  );
}

// ── Day stats sidebar ─────────────────────────────────────────────────────────

function DayStats({ meals }: { meals: Meal[] }) {
  const totalCal  = meals.reduce((s, m) => s + m.items.reduce((a, it) => a + it.calories, 0), 0);
  const totalProt = meals.reduce((s, m) => s + m.items.reduce((a, it) => a + it.protein, 0), 0);
  const totalCarb = meals.reduce((s, m) => s + m.items.reduce((a, it) => a + it.carbs, 0), 0);
  const totalFat  = meals.reduce((s, m) => s + m.items.reduce((a, it) => a + it.fat, 0), 0);
  const totalFiber = meals.reduce((s, m) => s + m.items.reduce((a, it) => a + (it.fiber ?? 0), 0), 0);

  return (
    <div className="space-y-3">
      {/* Calorias */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/40">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Flame className="h-3 w-3 text-orange-400" /> Calorias
          </p>
          <p className="text-3xl font-bold text-orange-400">
            {totalCal.toFixed(0)}
            <span className="text-sm font-normal text-muted-foreground ml-1">kcal</span>
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {meals.length} {meals.length === 1 ? "refeição" : "refeições"} ·{" "}
            {meals.reduce((s, m) => s + m.items.length, 0)} itens
          </p>
        </CardContent>
      </Card>

      {/* Proteína */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/40">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Dumbbell className="h-3 w-3 text-green-400" /> Proteína
          </p>
          <p className="text-2xl font-bold text-green-400">
            {totalProt.toFixed(0)}
            <span className="text-sm font-normal text-muted-foreground ml-1">g</span>
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {totalCal > 0 ? ((totalProt * 4 / totalCal) * 100).toFixed(0) : 0}% das kcal
          </p>
        </CardContent>
      </Card>

      {/* Carbs */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-yellow-500/40">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Zap className="h-3 w-3 text-yellow-400" /> Carboidratos
          </p>
          <p className="text-2xl font-bold text-yellow-400">
            {totalCarb.toFixed(0)}
            <span className="text-sm font-normal text-muted-foreground ml-1">g</span>
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {totalCal > 0 ? ((totalCarb * 4 / totalCal) * 100).toFixed(0) : 0}% das kcal
          </p>
        </CardContent>
      </Card>

      {/* Gordura */}
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-sky-400/40">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Droplets className="h-3 w-3 text-sky-400" /> Gordura
          </p>
          <p className="text-2xl font-bold text-sky-400">
            {totalFat.toFixed(0)}
            <span className="text-sm font-normal text-muted-foreground ml-1">g</span>
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {totalCal > 0 ? ((totalFat * 9 / totalCal) * 100).toFixed(0) : 0}% das kcal
          </p>
        </CardContent>
      </Card>

      {/* Fibra — só mostra se houver dados */}
      {totalFiber > 0 && (
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-emerald-500/40">
          <CardContent className="pt-4 pb-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-1">
              <Flame className="h-3 w-3 text-emerald-400" /> Fibra
            </p>
            <p className="text-2xl font-bold text-emerald-400">
              {totalFiber.toFixed(0)}
              <span className="text-sm font-normal text-muted-foreground ml-1">g</span>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Meal card ─────────────────────────────────────────────────────────────────

function MealCard({ meal, onEdit, onDelete, deleting }: {
  meal: Meal;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  const accent = MEAL_ACCENT[meal.meal_type];
  const totalCal  = meal.items.reduce((s, it) => s + it.calories, 0);
  const totalProt = meal.items.reduce((s, it) => s + it.protein, 0);
  const totalCarb = meal.items.reduce((s, it) => s + it.carbs, 0);
  const totalFat  = meal.items.reduce((s, it) => s + it.fat, 0);
  const src = SOURCE_LABELS[meal.source] ?? { label: meal.source, icon: null };

  return (
    <Card className={cn(
      "border-l-4 transition-all duration-200",
      "hover:shadow-md hover:translate-y-[-1px]",
      accent.border
    )}>
      <CardContent className="pt-4 pb-3 px-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className={cn("flex items-center justify-center h-7 w-7 rounded-lg shrink-0", accent.bg)}>
              <UtensilsCrossed className={cn("h-3.5 w-3.5", accent.text)} />
            </span>
            <div className="min-w-0">
              <p className="font-semibold text-sm leading-tight">{MEAL_LABELS[meal.meal_type]}</p>
              <Badge
                variant="secondary"
                className="text-[10px] px-1.5 py-0 h-4 mt-0.5 gap-1 font-normal"
              >
                {src.icon}
                {src.label}
              </Badge>
            </div>
          </div>

          {/* Calories + Actions */}
          <div className="flex items-center gap-1 shrink-0">
            <span className="text-base font-bold text-orange-400 mr-1">
              {totalCal.toFixed(0)} <span className="text-xs font-normal text-muted-foreground">kcal</span>
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 cursor-pointer"
              onClick={onEdit}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 cursor-pointer"
              onClick={onDelete}
              disabled={deleting}
            >
              {deleting
                ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                : <Trash2 className="h-3.5 w-3.5" />}
            </Button>
          </div>
        </div>

        {/* Macro pills */}
        <div className="flex gap-1.5 flex-wrap mb-3">
          <MacroPill icon={<Dumbbell className="h-3 w-3" />} value={totalProt} unit="g P" color="bg-green-500/10 text-green-400" />
          <MacroPill icon={<Zap className="h-3 w-3" />} value={totalCarb} unit="g C" color="bg-yellow-500/10 text-yellow-400" />
          <MacroPill icon={<Droplets className="h-3 w-3" />} value={totalFat} unit="g G" color="bg-sky-400/10 text-sky-400" />
        </div>

        {/* Food items */}
        <div className="divide-y divide-border/50">
          {meal.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between py-1.5 gap-2">
              <div className="min-w-0">
                <span className="text-sm text-foreground/90 truncate block">{item.food_name}</span>
                <span className="text-xs text-muted-foreground">{item.quantity}{item.unit}</span>
              </div>
              <div className="text-right shrink-0">
                <span className="text-xs font-medium text-foreground/80">{item.calories.toFixed(0)} kcal</span>
                <div className="text-[10px] text-muted-foreground">
                  {item.protein.toFixed(0)}P · {item.carbs.toFixed(0)}C · {item.fat.toFixed(0)}G
                </div>
              </div>
            </div>
          ))}
        </div>

        {meal.notes && (
          <p className="text-xs text-muted-foreground mt-2 pt-2 border-t border-border/50 italic">
            {meal.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function RefeicoesPage() {
  const today = getLocalToday();
  const [filterDate, setFilterDate] = useState(today);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const { data: meals, isLoading } = useMeals(filterDate);
  const deleteMeal = useDeleteMeal();
  const analyzeMeal = useAnalyzeMeal();
  const createMeal = useCreateMeal();
  const updateMeal = useUpdateMeal();

  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Nova refeição
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [mealType, setMealType] = useState<MealType>("lunch");
  const [parsedItems, setParsedItems] = useState<ParsedFoodItem[] | null>(null);

  // Edição
  const [editOpen, setEditOpen] = useState(false);
  const [editMeal, setEditMeal] = useState<Meal | null>(null);
  const [editMealType, setEditMealType] = useState<MealType>("lunch");
  const [editNotes, setEditNotes] = useState("");

  function openEdit(meal: Meal) {
    setEditMeal(meal);
    setEditMealType(meal.meal_type);
    setEditNotes(meal.notes ?? "");
    setEditOpen(true);
  }

  async function handleSaveEdit() {
    if (!editMeal) return;
    await updateMeal.mutateAsync({
      id: editMeal.id,
      data: { meal_type: editMealType, notes: editNotes || undefined },
    });
    setEditOpen(false);
    setEditMeal(null);
  }

  async function handleAnalyze() {
    try {
      const res = await analyzeMeal.mutateAsync(description);
      setParsedItems(res.items);
    } catch {
      // error shown via analyzeMeal.isError
    }
  }

  async function handleSave() {
    if (!parsedItems) return;
    await createMeal.mutateAsync({
      meal_type: mealType,
      date: filterDate,
      items: parsedItems.map(
        (it): MealItemCreate => ({
          food_name: it.food_name,
          quantity: it.quantity,
          unit: it.unit,
          calories: it.calories,
          protein: it.protein,
          carbs: it.carbs,
          fat: it.fat,
          fiber: it.fiber,
        })
      ),
    });
    setOpen(false);
    setParsedItems(null);
    setDescription("");
  }

  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteMeal.mutateAsync(id);
    } finally {
      setDeletingId(null);
    }
  }

  function resetDialog() {
    setParsedItems(null);
    setDescription("");
    setMealType("lunch");
  }

  const dateLabel = formatDateDisplay(filterDate);
  const isTodaySelected = isToday(filterDate);

  return (
    <div className="space-y-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <UtensilsCrossed className="h-6 w-6 text-primary" />
            Refeições
          </h1>
          <p className="text-muted-foreground text-sm">Registro e histórico alimentar</p>
        </div>

        <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetDialog(); }}>
          <DialogTrigger asChild>
            <Button className="gap-1.5 shrink-0">
              <Plus className="h-4 w-4" />
              Adicionar
            </Button>
          </DialogTrigger>

          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UtensilsCrossed className="h-4 w-4 text-primary" />
                Nova refeição
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-4 pt-1">
              {/* Tipo */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Tipo de refeição
                </Label>
                <Select value={mealType} onValueChange={(v) => setMealType(v as MealType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(MEAL_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Descrição — só exibe se ainda não analisou */}
              {!parsedItems && (
                <div className="space-y-1.5">
                  <Label htmlFor="desc" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Descreva o que comeu
                  </Label>
                  <Textarea
                    id="desc"
                    placeholder="Ex: 200g de arroz branco com 150g de frango grelhado e salada verde"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="resize-none"
                    rows={3}
                  />
                </div>
              )}

              {/* Erro IA */}
              {analyzeMeal.isError && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/8 border border-destructive/15 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  Erro ao analisar. Verifique sua conexão e tente novamente.
                </div>
              )}

              {/* Analisar */}
              {!parsedItems && (
                <Button
                  onClick={handleAnalyze}
                  disabled={!description.trim() || analyzeMeal.isPending}
                  className="w-full"
                >
                  <Search className="h-4 w-4 mr-2" />
                  {analyzeMeal.isPending ? "Analisando com IA..." : "Analisar com IA"}
                </Button>
              )}

              {/* Resultado da análise */}
              {parsedItems && (
                <div className="space-y-3">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Itens identificados
                  </p>

                  <div className="rounded-lg border border-border overflow-hidden">
                    {parsedItems.map((item, i) => (
                      <div
                        key={i}
                        className={cn(
                          "flex items-center justify-between px-3 py-2.5 text-sm",
                          i > 0 && "border-t border-border/50"
                        )}
                      >
                        <div className="flex items-center gap-1.5 min-w-0">
                          {item.confidence < 0.6 && (
                            <AlertTriangle className="h-3.5 w-3.5 text-yellow-500 shrink-0" />
                          )}
                          <div className="min-w-0">
                            <span className="font-medium truncate block">{item.food_name}</span>
                            <span className="text-xs text-muted-foreground">{item.quantity}{item.unit}</span>
                          </div>
                        </div>
                        <span className="text-orange-400 font-semibold shrink-0 ml-2">
                          {item.calories.toFixed(0)} kcal
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Total */}
                  <div className="flex justify-between text-sm font-semibold px-1">
                    <span className="text-muted-foreground">Total estimado</span>
                    <span className="text-orange-400">
                      {parsedItems.reduce((s, it) => s + it.calories, 0).toFixed(0)} kcal
                    </span>
                  </div>

                  <div className="flex gap-2 pt-1">
                    <Button variant="outline" onClick={() => setParsedItems(null)} className="flex-1">
                      <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                      Reanalisar
                    </Button>
                    <Button onClick={handleSave} disabled={createMeal.isPending} className="flex-1">
                      {!createMeal.isPending && <Check className="h-3.5 w-3.5 mr-1.5" />}
                      {createMeal.isPending ? "Salvando..." : "Salvar"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* ── Dialog de edição ───────────────────────────────────────────────── */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pencil className="h-4 w-4 text-primary" />
              Editar refeição
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-1">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Tipo de refeição
              </Label>
              <Select value={editMealType} onValueChange={(v) => setEditMealType(v as MealType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MEAL_LABELS).map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-notes" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Notas (opcional)
              </Label>
              <Textarea
                id="edit-notes"
                placeholder="Observações sobre a refeição..."
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                className="resize-none"
                rows={2}
              />
            </div>
            <div className="flex gap-2 pt-1">
              <Button variant="outline" onClick={() => setEditOpen(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleSaveEdit} disabled={updateMeal.isPending} className="flex-1">
                {!updateMeal.isPending && <Check className="h-3.5 w-3.5 mr-1.5" />}
                {updateMeal.isPending ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Layout 2 colunas: refeições (esq) + stats (dir) ───────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 space-y-4">

      {/* ── Date navigator ─────────────────────────────────────────────────── */}
      <div className="glass-card rounded-xl px-3 py-2.5 flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0 cursor-pointer"
          onClick={() => setFilterDate(addDays(filterDate, -1))}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <div className="flex-1 text-center">
          <p className="text-sm font-medium capitalize" suppressHydrationWarning>{dateLabel}</p>
        </div>

        <div className="flex items-center gap-1">
          {!isTodaySelected && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs text-primary cursor-pointer"
              onClick={() => setFilterDate(today)}
            >
              Hoje
            </Button>
          )}

          {/* Calendar picker — Popover customizado */}
          <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 cursor-pointer"
              >
                <CalendarIcon className="h-4 w-4 text-muted-foreground" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-auto p-0">
              <Calendar
                mode="single"
                selected={new Date(filterDate + "T12:00")}
                onSelect={(date) => {
                  if (!date) return;
                  const y = date.getFullYear();
                  const m = String(date.getMonth() + 1).padStart(2, "0");
                  const d = String(date.getDate()).padStart(2, "0");
                  setFilterDate(`${y}-${m}-${d}`);
                  setCalendarOpen(false);
                }}
                disabled={(date) => date > new Date()}
                locale={ptBR}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0 cursor-pointer"
          onClick={() => setFilterDate(addDays(filterDate, 1))}
          disabled={isTodaySelected}
        >
          <ChevronRight className={cn("h-4 w-4", isTodaySelected && "opacity-30")} />
        </Button>
      </div>

      {/* ── Loading ────────────────────────────────────────────────────────── */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      )}

      {/* ── Empty state ────────────────────────────────────────────────────── */}
      {meals?.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="flex items-center justify-center h-16 w-16 rounded-2xl bg-muted/50">
            <UtensilsCrossed className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <div>
            <p className="font-semibold text-foreground/80">Nenhuma refeição registrada</p>
            <p className="text-sm text-muted-foreground mt-1">
              {isTodaySelected
                ? "Adicione sua primeira refeição do dia"
                : `Sem registros em ${new Date(filterDate + "T12:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "long" })}`}
            </p>
          </div>
          {isTodaySelected && (
            <Button
              size="sm"
              className="gap-1.5 mt-1"
              onClick={() => setOpen(true)}
            >
              <Plus className="h-4 w-4" />
              Adicionar refeição
            </Button>
          )}
        </div>
      )}

      {/* ── Meal cards ─────────────────────────────────────────────────────── */}
      <div className="space-y-3">
        {meals?.map((meal) => (
          <MealCard
            key={meal.id}
            meal={meal}
            onEdit={() => openEdit(meal)}
            onDelete={() => handleDelete(meal.id)}
            deleting={deletingId === meal.id}
          />
        ))}
      </div>

      </div>{/* fim col-span-2 */}

      {/* ── Coluna direita: stats do dia ────────────────────────────────────── */}
      <div>
        {meals && meals.length > 0
          ? <DayStats meals={meals} />
          : (
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
              <CardContent className="pt-10 pb-10 flex flex-col items-center gap-3 text-center">
                <span className="flex items-center justify-center w-12 h-12 rounded-full bg-muted/30">
                  <Flame className="h-6 w-6 text-muted-foreground/40" />
                </span>
                <p className="text-sm text-muted-foreground">Sem dados nutricionais</p>
                <p className="text-xs text-muted-foreground/70">Os totais do dia aparecerão aqui</p>
              </CardContent>
            </Card>
          )
        }
      </div>

      </div>{/* fim grid */}
    </div>
  );
}
