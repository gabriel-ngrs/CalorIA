"use client";

import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
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
};

const MEAL_EMOJIS: Record<MealType, string> = {
  breakfast: "☀️",
  morning_snack: "🍌",
  lunch: "🍽️",
  afternoon_snack: "🍎",
  dinner: "🌙",
  supper: "🌛",
  snack: "🥨",
  pre_workout: "💪",
  post_workout: "🏋️",
  supplement: "💊",
};

export default function RefeicoesPage() {
  const today = new Date().toISOString().slice(0, 10);
  const [filterDate, setFilterDate] = useState(today);
  const { data: meals, isLoading } = useMeals(filterDate);
  const deleteMeal = useDeleteMeal();
  const analyzeMeal = useAnalyzeMeal();
  const createMeal = useCreateMeal();
  const updateMeal = useUpdateMeal();

  // Estado do dialog de nova refeição
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [mealType, setMealType] = useState<MealType>("lunch");
  const [parsedItems, setParsedItems] = useState<ParsedFoodItem[] | null>(null);

  // Estado do dialog de edição
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
      // analyzeMeal.isError fica true — exibido no JSX
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

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">🍽️ Refeições</h1>
          <p className="text-muted-foreground text-sm">Histórico e registro de refeições</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" />
              Adicionar
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Nova refeição</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Tipo</Label>
                <Select value={mealType} onValueChange={(v) => setMealType(v as MealType)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(MEAL_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>
                        {MEAL_EMOJIS[v as MealType]} {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="desc">Descreva o que comeu</Label>
                <Textarea
                  id="desc"
                  placeholder="Ex: 200g de arroz branco com 150g de frango grelhado e salada"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="mt-1 resize-none"
                  rows={3}
                />
              </div>

              {analyzeMeal.isError && (
                <p className="text-sm text-destructive">
                  ❌ Erro ao analisar. Verifique sua conexão e tente novamente.
                </p>
              )}

              {!parsedItems && (
                <Button onClick={handleAnalyze} disabled={!description.trim() || analyzeMeal.isPending} className="w-full">
                  {analyzeMeal.isPending ? "Analisando com IA..." : "🔍 Analisar com IA"}
                </Button>
              )}

              {parsedItems && (
                <div className="space-y-3">
                  <div className="border rounded-md divide-y text-sm">
                    {parsedItems.map((item, i) => (
                      <div key={i} className="flex justify-between px-3 py-2">
                        <span>
                          {item.confidence < 0.6 && "⚠️ "}
                          {item.food_name} ({item.quantity}{item.unit})
                        </span>
                        <span className="text-orange-600 font-medium">{item.calories.toFixed(0)} kcal</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setParsedItems(null)} className="flex-1">
                      Reanalisar
                    </Button>
                    <Button onClick={handleSave} disabled={createMeal.isPending} className="flex-1">
                      {createMeal.isPending ? "Salvando..." : "✅ Salvar"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Dialog de edição */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Editar refeição</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Tipo</Label>
              <Select value={editMealType} onValueChange={(v) => setEditMealType(v as MealType)}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MEAL_LABELS).map(([v, label]) => (
                    <SelectItem key={v} value={v}>
                      {MEAL_EMOJIS[v as MealType]} {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="edit-notes">Notas</Label>
              <Textarea
                id="edit-notes"
                placeholder="Observações sobre a refeição..."
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                className="mt-1 resize-none"
                rows={2}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setEditOpen(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleSaveEdit} disabled={updateMeal.isPending} className="flex-1">
                {updateMeal.isPending ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Filtro por data */}
      <div className="flex items-center gap-3">
        <Label htmlFor="date" className="shrink-0">Data</Label>
        <Input
          id="date"
          type="date"
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="w-44"
        />
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}

      {meals?.length === 0 && !isLoading && (
        <p className="text-center text-muted-foreground py-10">
          Nenhuma refeição em {new Date(filterDate + "T12:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "long" })}
        </p>
      )}

      <div className="space-y-3">
        {meals?.map((meal) => {
          const totalCal = meal.items.reduce((s, it) => s + it.calories, 0);
          return (
            <Card key={meal.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-1.5">
                    {MEAL_EMOJIS[meal.meal_type]} {MEAL_LABELS[meal.meal_type]}
                    <Badge variant="secondary" className="text-xs capitalize">{meal.source}</Badge>
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-orange-600">{totalCal.toFixed(0)} kcal</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-primary"
                      onClick={() => openEdit(meal)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      onClick={() => deleteMeal.mutate(meal.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="divide-y text-sm">
                  {meal.items.map((item) => (
                    <div key={item.id} className="flex justify-between py-1">
                      <span>{item.food_name} <span className="text-muted-foreground text-xs">({item.quantity}{item.unit})</span></span>
                      <span className="text-muted-foreground text-xs">
                        {item.calories.toFixed(0)} kcal · {item.protein.toFixed(0)}P · {item.carbs.toFixed(0)}C · {item.fat.toFixed(0)}G
                      </span>
                    </div>
                  ))}
                </div>
                {meal.notes && (
                  <p className="text-xs text-muted-foreground mt-2 italic">{meal.notes}</p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
