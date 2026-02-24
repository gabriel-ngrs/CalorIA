import React from "react";
import { render, screen } from "@testing-library/react";
import { MacroPieChart } from "@/components/dashboard/MacroPieChart";
import type { NutritionSummary } from "@/types";

const nutritionWithData: NutritionSummary = {
  total_calories: 1600,
  total_protein: 100,
  total_carbs: 180,
  total_fat: 55,
  meals_count: 3,
  meals: [],
};

const emptyNutrition: NutritionSummary = {
  total_calories: 0,
  total_protein: 0,
  total_carbs: 0,
  total_fat: 0,
  meals_count: 0,
  meals: [],
};

describe("MacroPieChart", () => {
  it("renderiza o título do gráfico", () => {
    render(<MacroPieChart nutrition={nutritionWithData} />);
    expect(screen.getByText("Distribuição de macros")).toBeInTheDocument();
  });

  it("exibe mensagem quando não há dados", () => {
    render(<MacroPieChart nutrition={emptyNutrition} />);
    expect(screen.getByText("Sem dados hoje")).toBeInTheDocument();
  });

  it("exibe gráfico quando há dados", () => {
    render(<MacroPieChart nutrition={nutritionWithData} />);
    expect(screen.queryByText("Sem dados hoje")).not.toBeInTheDocument();
  });

  it("exibe legenda com os macros", () => {
    render(<MacroPieChart nutrition={nutritionWithData} />);
    expect(screen.getByText("Proteína")).toBeInTheDocument();
    expect(screen.getByText("Carboidrato")).toBeInTheDocument();
    expect(screen.getByText("Gordura")).toBeInTheDocument();
  });
});
