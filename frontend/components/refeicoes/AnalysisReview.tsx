"use client";

/**
 * Revisão da análise de refeição — mostra DE ONDE veio cada número.
 *
 * Antes, todos os itens eram rotulados "✨ Analisado por IA", inclusive os que
 * vinham da tabela nutricional curada, e o usuário não tinha como perceber que
 * uma porção fora convertida errado (bug 001 — "o erro é silencioso").
 *
 * Aqui cada item declara a fonte do valor nutricional, a massa normalizada e a
 * porção original. Itens sem âncora determinística de porção ficam destacados e
 * exigem confirmação antes de salvar.
 *
 * A edição de quantidade recalcula localmente por proporção — que é exatamente o
 * cálculo do banco (`valor_100g × gramas/100`), sem nova chamada à IA.
 */

import { useMemo, useState } from "react";
import { AlertTriangle, Check, Database, Info, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { ParsedFoodItem } from "@/types";

/** Rótulo e estilo por origem do valor nutricional. */
const SOURCE_META: Record<
  string,
  { label: string; title: string; className: string; confiavel: boolean }
> = {
  taco: {
    label: "Tabela nutricional",
    title: "Valor da tabela nutricional brasileira curada",
    className: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30",
    confiavel: true,
  },
  usda: {
    label: "USDA",
    title: "Valor da base nutricional do USDA",
    className: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30",
    confiavel: true,
  },
  fatsecret: {
    label: "FatSecret",
    title: "Valor da base FatSecret",
    className: "text-sky-500 bg-sky-500/10 border-sky-500/30",
    confiavel: true,
  },
  openfoodfacts: {
    label: "Open Food Facts",
    title: "Valor de produto do Open Food Facts (colaborativo)",
    className: "text-sky-500 bg-sky-500/10 border-sky-500/30",
    confiavel: true,
  },
  ai_estimated: {
    label: "Estimado pela IA",
    title: "Sem correspondência no banco nutricional — valor estimado",
    className: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    confiavel: false,
  },
};

const PORTION_LABEL: Record<string, string> = {
  direta: "quantidade informada em gramas",
  volume: "convertida de volume (densidade ~1 g/ml)",
  tabela: "convertida pela tabela de porções",
  sem_ancora: "quantidade estimada, sem referência de porção",
};

function SourceBadge({ item }: { item: ParsedFoodItem }) {
  const meta = item.data_source ? SOURCE_META[item.data_source] : undefined;
  const Icon = meta?.confiavel ? Database : Sparkles;
  return (
    <span
      title={meta?.title ?? "Origem do valor não registrada"}
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border shrink-0",
        meta?.className ?? "text-muted-foreground bg-muted/40 border-border"
      )}
    >
      <Icon className="h-2.5 w-2.5" />
      {meta?.label ?? "Origem desconhecida"}
    </span>
  );
}

export interface AnalysisReviewProps {
  items: ParsedFoodItem[];
  onChange: (items: ParsedFoodItem[]) => void;
  onReanalyze: () => void;
  onSave: () => void;
  saving?: boolean;
}

export function AnalysisReview({
  items,
  onChange,
  onReanalyze,
  onSave,
  saving = false,
}: AnalysisReviewProps) {
  // Itens que o usuário já confirmou explicitamente (índices).
  const [confirmados, setConfirmados] = useState<Set<number>>(new Set());

  const pendentes = useMemo(
    () => items.map((it, i) => (it.needs_review && !confirmados.has(i) ? i : -1)).filter((i) => i >= 0),
    [items, confirmados]
  );

  const total = items.reduce((s, it) => s + it.calories, 0);
  const doBanco = items.filter(
    (it) => it.data_source && it.data_source !== "ai_estimated"
  ).length;

  /**
   * Reescala os macros do item proporcionalmente à nova massa.
   * É o mesmo cálculo que o banco faz (`valor_100g × gramas/100`), então não há
   * motivo para uma nova chamada de IA.
   */
  function ajustarQuantidade(indice: number, novaQtd: number) {
    const item = items[indice];
    if (!item || item.quantity <= 0 || novaQtd <= 0) return;
    const k = novaQtd / item.quantity;
    const esc = (v: number | null) => (v === null ? null : Number((v * k).toFixed(2)));
    const proximos = [...items];
    proximos[indice] = {
      ...item,
      quantity: novaQtd,
      calories: Number((item.calories * k).toFixed(1)),
      protein: Number((item.protein * k).toFixed(2)),
      carbs: Number((item.carbs * k).toFixed(2)),
      fat: Number((item.fat * k).toFixed(2)),
      fiber: Number((item.fiber * k).toFixed(2)),
      sodium: esc(item.sodium),
      sugar: esc(item.sugar),
      saturated_fat: esc(item.saturated_fat),
      // Quantidade editada à mão é uma âncora melhor que a estimada.
      needs_review: false,
      review_reason: null,
      portion_source: "direta",
      portion_text: `${novaQtd} g (ajustado)`,
    };
    onChange(proximos);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Itens identificados
        </p>
        <span className="text-[11px] text-muted-foreground">
          {doBanco} de {items.length}{" "}
          {doBanco === 1 ? "veio" : "vieram"} do banco nutricional
        </span>
      </div>

      <div className="rounded-lg border border-border overflow-hidden divide-y divide-border/50">
        {items.map((item, i) => {
          const precisaConfirmar = Boolean(item.needs_review) && !confirmados.has(i);
          return (
            <div
              key={i}
              className={cn(
                "px-3 py-2.5 text-sm",
                precisaConfirmar && "bg-amber-500/5 border-l-2 border-l-amber-500"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-medium">{item.food_name}</span>
                    <SourceBadge item={item} />
                  </div>

                  {item.matched_food_name &&
                    item.matched_food_name.toLowerCase() !==
                      item.food_name.toLowerCase() && (
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        casado com <span className="italic">{item.matched_food_name}</span>
                      </p>
                    )}

                  <div className="flex items-center gap-1.5 mt-1.5">
                    <Input
                      type="number"
                      min={1}
                      step={1}
                      defaultValue={Math.round(item.quantity)}
                      onBlur={(e) => {
                        const v = Number(e.target.value);
                        if (Number.isFinite(v) && v > 0 && v !== item.quantity) {
                          ajustarQuantidade(i, v);
                        }
                      }}
                      aria-label={`Quantidade de ${item.food_name} em gramas`}
                      className="h-7 w-20 text-xs"
                    />
                    <span className="text-xs text-muted-foreground">g</span>
                    {item.portion_text && (
                      <span
                        className="text-[11px] text-muted-foreground truncate"
                        title={
                          item.portion_source
                            ? PORTION_LABEL[item.portion_source] ?? item.portion_source
                            : undefined
                        }
                      >
                        · você disse &ldquo;{item.portion_text}&rdquo;
                      </span>
                    )}
                  </div>
                </div>

                <span className="text-orange-400 font-semibold shrink-0">
                  {item.calories.toFixed(0)} kcal
                </span>
              </div>

              {precisaConfirmar && (
                <div className="mt-2 flex items-start gap-2 rounded bg-amber-500/10 px-2 py-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-amber-600 dark:text-amber-400">
                      {item.review_reason ?? "Porção incerta — confira a quantidade."}
                    </p>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 mt-1 px-2 text-[11px]"
                      onClick={() =>
                        setConfirmados((s) => new Set(s).add(i))
                      }
                    >
                      <Check className="h-3 w-3 mr-1" />
                      Está certo
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex justify-between text-sm font-semibold px-1">
        <span className="text-muted-foreground">Total</span>
        <span className="text-orange-400">{total.toFixed(0)} kcal</span>
      </div>

      {pendentes.length > 0 && (
        <p className="flex items-start gap-1.5 text-[11px] text-amber-600 dark:text-amber-400 px-1">
          <Info className="h-3.5 w-3.5 shrink-0 mt-px" />
          {pendentes.length === 1
            ? "1 item precisa de confirmação antes de salvar."
            : `${pendentes.length} itens precisam de confirmação antes de salvar.`}
        </p>
      )}

      <div className="flex gap-2 pt-1">
        <Button variant="outline" onClick={onReanalyze} className="flex-1">
          Reanalisar
        </Button>
        <Button
          onClick={onSave}
          disabled={saving || pendentes.length > 0}
          className="flex-1"
        >
          {!saving && <Check className="h-3.5 w-3.5 mr-1.5" />}
          {saving ? "Salvando..." : "Salvar"}
        </Button>
      </div>
    </div>
  );
}
