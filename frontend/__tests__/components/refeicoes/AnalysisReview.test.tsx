import { fireEvent, render, screen } from "@testing-library/react";
import { AnalysisReview } from "@/components/refeicoes/AnalysisReview";
import type { ParsedFoodItem } from "@/types";

/**
 * O bug 001 aponta que "o erro é silencioso": o usuário não tem como saber que
 * uma porção foi mal convertida nem de onde veio o número. Estes testes travam
 * a transparência que a tela passou a oferecer.
 */

function item(over: Partial<ParsedFoodItem> = {}): ParsedFoodItem {
  return {
    food_name: "pizza de calabresa",
    quantity: 800,
    unit: "g",
    calories: 2160,
    protein: 96,
    carbs: 240,
    fat: 88,
    fiber: 16,
    confidence: 0.9,
    food_id: 1,
    data_source: "taco",
    sodium: null,
    sugar: null,
    saturated_fat: null,
    portion_text: "8 fatia",
    portion_source: "tabela",
    matched_food_name: "Pizza calabresa",
    needs_review: false,
    review_reason: null,
    ...over,
  };
}

function setup(items: ParsedFoodItem[], onChange = jest.fn(), onSave = jest.fn()) {
  render(
    <AnalysisReview
      items={items}
      onChange={onChange}
      onSave={onSave}
      onReanalyze={jest.fn()}
    />
  );
  return { onChange, onSave };
}

describe("AnalysisReview", () => {
  it("mostra a origem do valor nutricional por item", () => {
    setup([item()]);
    expect(screen.getByText("Tabela nutricional")).toBeInTheDocument();
  });

  it("distingue valor estimado pela IA de valor do banco", () => {
    setup([item({ data_source: "ai_estimated", matched_food_name: null })]);
    expect(screen.getByText("Estimado pela IA")).toBeInTheDocument();
    expect(screen.queryByText("Tabela nutricional")).not.toBeInTheDocument();
  });

  it("mostra a porção que o usuário descreveu junto da massa normalizada", () => {
    setup([item()]);
    expect(screen.getByText(/8 fatia/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Quantidade de pizza de calabresa/)).toHaveValue(800);
  });

  it("informa quantos itens vieram do banco", () => {
    setup([item(), item({ data_source: "ai_estimated" })]);
    expect(screen.getByText(/1 de 2/)).toBeInTheDocument();
  });

  it("bloqueia o salvamento enquanto houver item pendente de confirmação", () => {
    const { onSave } = setup([
      item({ needs_review: true, review_reason: "porção não ancorada" }),
    ]);
    const salvar = screen.getByRole("button", { name: /salvar/i });
    expect(salvar).toBeDisabled();
    expect(screen.getByText("porção não ancorada")).toBeInTheDocument();
    fireEvent.click(salvar);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("libera o salvamento depois da confirmação do item", () => {
    setup([item({ needs_review: true, review_reason: "porção não ancorada" })]);
    fireEvent.click(screen.getByRole("button", { name: /está certo/i }));
    expect(screen.getByRole("button", { name: /salvar/i })).toBeEnabled();
  });

  it("recalcula os macros por proporção ao editar a quantidade, sem chamar a IA", () => {
    const { onChange } = setup([item()]);
    const campo = screen.getByLabelText(/Quantidade de pizza de calabresa/);
    fireEvent.blur(campo, { target: { value: "400" } });

    expect(onChange).toHaveBeenCalledTimes(1);
    const [atualizado] = onChange.mock.calls[0][0] as ParsedFoodItem[];
    // Metade da massa → metade de tudo. É o mesmo cálculo do banco
    // (valor_100g × gramas/100), então não há nova chamada de IA.
    expect(atualizado.quantity).toBe(400);
    expect(atualizado.calories).toBe(1080);
    expect(atualizado.protein).toBe(48);
    expect(atualizado.carbs).toBe(120);
    expect(atualizado.fat).toBe(44);
  });

  it("some com a pendência de revisão quando o usuário corrige a quantidade", () => {
    const { onChange } = setup([item({ needs_review: true, review_reason: "incerta" })]);
    fireEvent.blur(screen.getByLabelText(/Quantidade de pizza de calabresa/), {
      target: { value: "500" },
    });
    const [atualizado] = onChange.mock.calls[0][0] as ParsedFoodItem[];
    expect(atualizado.needs_review).toBe(false);
  });

  it("mostra o alimento casado quando o nome difere do que o usuário disse", () => {
    setup([item()]);
    expect(screen.getByText("Pizza calabresa")).toBeInTheDocument();
  });

  it("soma o total de calorias", () => {
    setup([item({ calories: 2160 }), item({ calories: 140 })]);
    expect(screen.getByText("2300 kcal")).toBeInTheDocument();
  });
});
