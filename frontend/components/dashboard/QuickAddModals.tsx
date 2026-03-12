"use client";

import { useRef, useState } from "react";
import {
  AlertCircle,
  Camera,
  Check,
  Droplets,
  Mic,
  MicOff,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Smile,
  Type,
  UtensilsCrossed,
  X,
  Zap,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useAnalyzeMeal, useAnalyzePhoto, useCreateMeal } from "@/lib/hooks/useMeals";
import { useLogHydration, useLogMood, useLogWeight } from "@/lib/hooks/useLogs";
import type { MealItemCreate, MealType, ParsedFoodItem } from "@/types";

// ── Shared helpers ────────────────────────────────────────────────────────────

function getLocalToday(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

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

const MOOD_LEVELS = [
  { value: 1, label: "Muito baixo" },
  { value: 2, label: "Baixo" },
  { value: 3, label: "Médio" },
  { value: 4, label: "Alto" },
  { value: 5, label: "Muito alto" },
];

const LEVEL_COLORS: Record<number, string> = {
  1: "border-red-500/50 bg-red-500/10 text-red-400 hover:bg-red-500/20",
  2: "border-orange-500/50 bg-orange-500/10 text-orange-400 hover:bg-orange-500/20",
  3: "border-yellow-500/50 bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20",
  4: "border-blue-500/50 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20",
  5: "border-green-500/50 bg-green-500/10 text-green-400 hover:bg-green-500/20",
};

const LEVEL_SELECTED: Record<number, string> = {
  1: "border-red-500 bg-red-500/25 text-red-300 ring-1 ring-red-500/50",
  2: "border-orange-500 bg-orange-500/25 text-orange-300 ring-1 ring-orange-500/50",
  3: "border-yellow-500 bg-yellow-500/25 text-yellow-300 ring-1 ring-yellow-500/50",
  4: "border-blue-500 bg-blue-500/25 text-blue-300 ring-1 ring-blue-500/50",
  5: "border-green-500 bg-green-500/25 text-green-300 ring-1 ring-green-500/50",
};

const QUICK_WATER = [
  { ml: 200, label: "Copo" },
  { ml: 300, label: "Garr. P" },
  { ml: 500, label: "Garr. M" },
  { ml: 750, label: "Garr. G" },
];

// ── Level selector (for mood modal) ──────────────────────────────────────────

function LevelSelector({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex gap-1.5">
      {MOOD_LEVELS.map((l) => {
        const isSelected = value === l.value;
        return (
          <button
            key={l.value}
            type="button"
            onClick={() => onChange(l.value)}
            title={l.label}
            className={cn(
              "flex-1 flex flex-col items-center gap-1 py-3 rounded-xl border transition-all duration-150 cursor-pointer",
              isSelected ? LEVEL_SELECTED[l.value] : LEVEL_COLORS[l.value]
            )}
          >
            <span className="text-base font-bold leading-none">{l.value}</span>
            <span className="text-[9px] font-medium leading-tight text-center px-0.5">{l.label}</span>
          </button>
        );
      })}
    </div>
  );
}

// ── Quick Meal Modal ──────────────────────────────────────────────────────────

type InputMode = "text" | "photo" | "audio";

export function QuickMealModal({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const today = getLocalToday();
  const analyzeMeal = useAnalyzeMeal();
  const analyzePhoto = useAnalyzePhoto();
  const createMeal = useCreateMeal();

  const [mealType, setMealType] = useState<MealType>("lunch");
  const [parsedItems, setParsedItems] = useState<ParsedFoodItem[] | null>(null);
  const [inputMode, setInputMode] = useState<InputMode>("text");
  const [description, setDescription] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [speechError, setSpeechError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const speechRef = useRef<any>(null);

  function reset() {
    setParsedItems(null);
    setDescription("");
    setMealType("lunch");
    setInputMode("text");
    setImageFile(null);
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setImagePreviewUrl(null);
    setTranscript("");
    setSpeechError(null);
    speechRef.current?.stop();
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    e.target.value = "";
  }

  function startRecording() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSpeechError("Reconhecimento de voz não suportado. Use Chrome ou Edge."); return; }
    const rec = new SR();
    rec.lang = "pt-BR";
    rec.continuous = true;
    rec.interimResults = false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rec.onresult = (e: any) => {
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
      }
      if (final) setTranscript((prev) => (prev + " " + final).trim());
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rec.onerror = (e: any) => { setIsRecording(false); if (e.error !== "aborted") setSpeechError("Erro no microfone. Verifique as permissões."); };
    rec.onend = () => setIsRecording(false);
    speechRef.current = rec;
    rec.start();
    setIsRecording(true);
    setSpeechError(null);
  }

  function stopRecording() { speechRef.current?.stop(); setIsRecording(false); }

  async function handleAnalyze() {
    try {
      if (inputMode === "text") {
        const res = await analyzeMeal.mutateAsync(description);
        setParsedItems(res.items);
      } else if (inputMode === "photo" && imageFile) {
        const base64 = await fileToBase64(imageFile);
        const res = await analyzePhoto.mutateAsync({ image_base64: base64, mime_type: imageFile.type || "image/jpeg" });
        setParsedItems(res.items);
      } else if (inputMode === "audio" && transcript.trim()) {
        const res = await analyzeMeal.mutateAsync(transcript);
        setParsedItems(res.items);
      }
    } catch { /* shown via isError */ }
  }

  async function handleSave() {
    if (!parsedItems) return;
    await createMeal.mutateAsync({
      meal_type: mealType,
      date: today,
      items: parsedItems.map((it): MealItemCreate => ({
        food_name: it.food_name,
        quantity: it.quantity,
        unit: it.unit,
        calories: it.calories,
        protein: it.protein,
        carbs: it.carbs,
        fat: it.fat,
        fiber: it.fiber,
      })),
    });
    onOpenChange(false);
    reset();
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
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
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Tipo de refeição</Label>
            <Select value={mealType} onValueChange={(v) => setMealType(v as MealType)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.entries(MEAL_LABELS).map(([v, label]) => (
                  <SelectItem key={v} value={v}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Mode selector */}
          {!parsedItems && (
            <div className="flex gap-1 p-1 rounded-lg bg-muted/40 border border-border/50">
              {([
                { mode: "text", Icon: Type, label: "Texto" },
                { mode: "photo", Icon: Camera, label: "Foto" },
                { mode: "audio", Icon: Mic, label: "Áudio" },
              ] as const).map(({ mode, Icon, label }) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setInputMode(mode)}
                  className={cn(
                    "flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-md text-xs font-medium transition-all cursor-pointer",
                    inputMode === mode ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />{label}
                </button>
              ))}
            </div>
          )}

          {/* Text mode */}
          {inputMode === "text" && !parsedItems && (
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Descreva o que comeu</Label>
              <Textarea
                placeholder="Ex: 200g de arroz com 150g de frango grelhado e salada"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="resize-none"
                rows={3}
              />
            </div>
          )}

          {/* Photo mode */}
          {inputMode === "photo" && !parsedItems && (
            <div className="space-y-3">
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageSelect} />
              {imagePreviewUrl ? (
                <div className="relative">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={imagePreviewUrl} alt="Preview" className="w-full rounded-lg object-cover max-h-48" />
                  <button
                    type="button"
                    onClick={() => { setImageFile(null); setImagePreviewUrl(null); }}
                    className="absolute top-2 right-2 bg-background/80 backdrop-blur-sm rounded-full p-1 hover:bg-background transition-colors cursor-pointer"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-border rounded-lg p-8 flex flex-col items-center gap-2 text-muted-foreground hover:border-primary/40 hover:text-primary transition-colors cursor-pointer"
                >
                  <Camera className="h-8 w-8" />
                  <span className="text-sm font-medium">Tirar foto ou escolher da galeria</span>
                  <span className="text-xs">JPEG ou PNG</span>
                </button>
              )}
            </div>
          )}

          {/* Audio mode */}
          {inputMode === "audio" && !parsedItems && (
            <div className="space-y-3">
              <div className="flex flex-col items-center gap-3 py-3">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={cn(
                    "w-16 h-16 rounded-full flex items-center justify-center transition-all cursor-pointer",
                    isRecording
                      ? "bg-red-500/20 border-2 border-red-500 text-red-400 animate-pulse"
                      : "bg-primary/10 border-2 border-primary/30 text-primary hover:bg-primary/20"
                  )}
                >
                  {isRecording ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
                </button>
                <p className="text-xs text-muted-foreground text-center">
                  {isRecording ? "Gravando... clique para parar" : "Clique no microfone e fale o que comeu"}
                </p>
              </div>
              {transcript && (
                <div className="space-y-1.5">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Transcrição</Label>
                  <Textarea value={transcript} onChange={(e) => setTranscript(e.target.value)} className="resize-none" rows={3} />
                  <button type="button" onClick={() => setTranscript("")} className="text-xs text-muted-foreground hover:text-destructive transition-colors cursor-pointer">
                    Limpar transcrição
                  </button>
                </div>
              )}
              {speechError && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/8 border border-destructive/15 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />{speechError}
                </div>
              )}
            </div>
          )}

          {/* AI error */}
          {(analyzeMeal.isError || analyzePhoto.isError) && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/8 border border-destructive/15 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              Erro ao analisar. Verifique sua conexão e tente novamente.
            </div>
          )}

          {/* Analyze button */}
          {!parsedItems && (
            <Button
              onClick={handleAnalyze}
              disabled={
                analyzeMeal.isPending || analyzePhoto.isPending ||
                (inputMode === "text" && description.trim().length < 3) ||
                (inputMode === "photo" && !imageFile) ||
                (inputMode === "audio" && transcript.trim().length < 3)
              }
              className="w-full"
            >
              <Search className="h-4 w-4 mr-2" />
              {(analyzeMeal.isPending || analyzePhoto.isPending) ? "Analisando com IA..." : "Analisar com IA"}
            </Button>
          )}

          {/* Parsed results */}
          {parsedItems && (
            <div className="space-y-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Itens identificados</p>
              <div className="rounded-lg border border-border overflow-hidden">
                {parsedItems.map((item, i) => (
                  <div key={i} className={cn("flex items-center justify-between px-3 py-2.5 text-sm", i > 0 && "border-t border-border/50")}>
                    <div className="flex items-center gap-1.5 min-w-0">
                      {item.confidence < 0.6 && <AlertTriangle className="h-3.5 w-3.5 text-yellow-500 shrink-0" />}
                      <div className="min-w-0">
                        <span className="font-medium truncate block">{item.food_name}</span>
                        <span className="text-xs text-muted-foreground">{item.quantity}{item.unit}</span>
                      </div>
                    </div>
                    <span className="text-orange-400 font-semibold shrink-0 ml-2">{item.calories.toFixed(0)} kcal</span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-sm font-semibold px-1">
                <span className="text-muted-foreground">Total estimado</span>
                <span className="text-orange-400">{parsedItems.reduce((s, it) => s + it.calories, 0).toFixed(0)} kcal</span>
              </div>
              <div className="flex gap-2 pt-1">
                <Button variant="outline" onClick={() => setParsedItems(null)} className="flex-1">
                  <RefreshCw className="h-3.5 w-3.5 mr-1.5" />Reanalisar
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
  );
}

// ── Quick Water Modal ─────────────────────────────────────────────────────────

export function QuickWaterModal({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [custom, setCustom] = useState("");
  const logHydration = useLogHydration();

  function getTime() {
    const n = new Date();
    return `${String(n.getHours()).padStart(2, "0")}:${String(n.getMinutes()).padStart(2, "0")}`;
  }

  async function log(ml: number) {
    if (!Number.isFinite(ml) || ml <= 0) return;
    await logHydration.mutateAsync({ amount_ml: ml, date: getLocalToday(), time: getTime() });
    setCustom("");
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Droplets className="h-4 w-4 text-blue-500" />
            Registrar água
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-1">
          <div className="grid grid-cols-2 gap-2">
            {QUICK_WATER.map(({ ml, label }) => (
              <button
                key={ml}
                type="button"
                disabled={logHydration.isPending}
                onClick={() => log(ml)}
                className="flex flex-col items-center gap-1.5 py-5 rounded-xl border border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/15 hover:border-blue-500/50 transition-colors cursor-pointer disabled:opacity-50"
              >
                <Droplets className="h-5 w-5 text-blue-500" />
                <span className="text-sm font-bold text-blue-400">+{ml} ml</span>
                <span className="text-xs text-muted-foreground">{label}</span>
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Outro valor (ml)"
              type="number"
              inputMode="numeric"
              min="1"
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={() => log(parseInt(custom, 10))}
              disabled={!custom || logHydration.isPending}
              className="gap-1.5 shrink-0"
            >
              <Plus className="h-3.5 w-3.5" />
              Adicionar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Quick Weight Modal ────────────────────────────────────────────────────────

export function QuickWeightModal({
  open,
  onOpenChange,
  currentWeight,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  currentWeight?: number;
}) {
  const [weight, setWeight] = useState("");
  const logWeight = useLogWeight();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const kg = parseFloat(weight.replace(",", "."));
    if (isNaN(kg) || kg <= 0) return;
    await logWeight.mutateAsync({ weight_kg: kg, date: getLocalToday() });
    setWeight("");
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) setWeight(""); }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Scale className="h-4 w-4 text-primary" />
            Registrar peso
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-1">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              type="number"
              inputMode="decimal"
              placeholder="Ex: 80.5"
              step="0.1"
              min="1"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="flex-1"
              autoFocus
            />
            <Button type="submit" disabled={logWeight.isPending || !weight}>
              {logWeight.isPending ? "..." : "Salvar"}
            </Button>
          </form>

          {currentWeight && (
            <div className="grid grid-cols-6 gap-1.5">
              {[-1, -0.5, -0.1, +0.1, +0.5, +1].map((v) => {
                const val = parseFloat((currentWeight + v).toFixed(1));
                return (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setWeight(String(val))}
                    className={cn(
                      "py-3 rounded-lg text-xs font-medium border transition-colors cursor-pointer",
                      v < 0
                        ? "border-green-500/30 text-green-500 hover:bg-green-500/10"
                        : "border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                    )}
                  >
                    {v > 0 ? `+${v}` : v}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Quick Mood Modal ──────────────────────────────────────────────────────────

export function QuickMoodModal({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [energy, setEnergy] = useState(3);
  const [mood, setMood] = useState(3);
  const [notes, setNotes] = useState("");
  const logMood = useLogMood();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await logMood.mutateAsync({
      date: getLocalToday(),
      energy_level: energy,
      mood_level: mood,
      notes: notes || undefined,
    });
    setNotes("");
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) { setEnergy(3); setMood(3); setNotes(""); } }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Smile className="h-4 w-4 text-yellow-400" />
            Registrar humor
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-5 pt-1">
          <div className="space-y-2.5">
            <Label className="flex items-center gap-1.5 text-sm font-medium">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-orange-500/10">
                <Zap className="h-3 w-3 text-orange-500" />
              </span>
              Energia
              <span className="ml-auto text-xs text-muted-foreground">{MOOD_LEVELS[energy - 1].label}</span>
            </Label>
            <LevelSelector value={energy} onChange={setEnergy} />
          </div>

          <div className="space-y-2.5">
            <Label className="flex items-center gap-1.5 text-sm font-medium">
              <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                <Smile className="h-3 w-3 text-blue-400" />
              </span>
              Humor
              <span className="ml-auto text-xs text-muted-foreground">{MOOD_LEVELS[mood - 1].label}</span>
            </Label>
            <LevelSelector value={mood} onChange={setMood} />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Notas (opcional)</Label>
            <Input
              placeholder="Como foi seu dia?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <Button type="submit" disabled={logMood.isPending} className="w-full">
            {logMood.isPending ? "Salvando..." : "Registrar"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
