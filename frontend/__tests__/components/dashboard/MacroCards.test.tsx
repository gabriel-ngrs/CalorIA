import React from "react";
import { render, screen } from "@testing-library/react";
import { MacroCards } from "@/components/dashboard/MacroCards";
import type { NutritionSummary, User } from "@/types";

const mockNutrition: NutritionSummary = {
  total_calories: 1500,
  total_protein: 80,
  total_carbs: 200,
  total_fat: 50,
  meals_count: 3,
  meals: [],
};

const mockUser: User = {
  id: 1,
  name: "Teste",
  email: "teste@caloria.com",
  calorie_goal: 2000,
  weight_goal: null,
  water_goal_ml: null,
  goal_type: null,
  telegram_chat_id: null,
  whatsapp_number: null,
  profile: null,
  created_at: "2024-01-01T00:00:00Z",
};

describe("MacroCards", () => {
  it("renderiza os 4 cartões de macros", () => {
    render(<MacroCards nutrition={mockNutrition} user={mockUser} />);
    // Cada label é renderizado em dois <span> (mobile/desktop) — getAllByText é necessário
    expect(screen.getAllByText("Calorias").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Proteína").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Carboidrato").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Gordura").length).toBeGreaterThan(0);
  });

  it("exibe o valor de calorias correto", () => {
    render(<MacroCards nutrition={mockNutrition} user={mockUser} />);
    expect(screen.getByText("1500")).toBeInTheDocument();
  });

  it("exibe o percentual da meta calórica", () => {
    render(<MacroCards nutrition={mockNutrition} user={mockUser} />);
    // 1500/2000 = 75%
    expect(screen.getByText(/75%/)).toBeInTheDocument();
    expect(screen.getByText(/2000 kcal/)).toBeInTheDocument();
  });

  it("usa meta padrão de 2000 kcal quando usuário é undefined", () => {
    render(<MacroCards nutrition={mockNutrition} user={undefined} />);
    expect(screen.getByText(/2000 kcal/)).toBeInTheDocument();
  });

  it("exibe proteína com uma casa decimal", () => {
    render(<MacroCards nutrition={mockNutrition} user={mockUser} />);
    expect(screen.getByText("80.0")).toBeInTheDocument();
  });
});
