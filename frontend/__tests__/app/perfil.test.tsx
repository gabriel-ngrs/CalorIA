import React from "react";
import { render, screen } from "@testing-library/react";
import PerfilPage from "@/app/(dashboard)/perfil/page";
import type { UserProfile } from "@/types";

const fullProfile: UserProfile = {
  height_cm: 175,
  current_weight: 70,
  birth_date: "1994-01-01",
  sex: "male",
  activity_level: "moderately_active",
  tdee_calculated: 2554,
  bmr: 1648,
  formula: "Mifflin-St Jeor",
};

// Prefixo `mock*` é a única forma permitida de referenciar variáveis externas
// dentro do factory de jest.mock (hoisting). A referência é mutável para que
// cada teste ajuste o perfil retornado.
let mockProfile: UserProfile = fullProfile;

jest.mock("@/lib/hooks/useProfile", () => {
  const user = {
    id: 1,
    name: "Teste",
    email: "teste@caloria.com",
    calorie_goal: 2000,
    weight_goal: null,
    water_goal_ml: null,
    goal_type: null,
    profile: null,
    created_at: "2024-01-01T00:00:00Z",
  };
  const noop = { mutateAsync: jest.fn(), isPending: false };
  return {
    useMe: () => ({ data: user }),
    useProfile: () => ({ data: mockProfile }),
    useUpdateProfile: () => noop,
    useUpdateMe: () => noop,
  };
});

describe("PerfilPage — data de nascimento + card TMB/TDEE (AC-A4)", () => {
  beforeEach(() => {
    mockProfile = fullProfile;
  });

  it("exibe seletor de data de nascimento, não campo de idade", () => {
    render(<PerfilPage />);
    const birth = screen.getByLabelText(/Data de nascimento/i) as HTMLInputElement;
    expect(birth).toBeInTheDocument();
    expect(birth.type).toBe("date");
    expect(birth.value).toBe("1994-01-01");
    expect(screen.queryByLabelText(/^Idade/i)).not.toBeInTheDocument();
  });

  it("exibe o card com TMB, TDEE e a fórmula", () => {
    render(<PerfilPage />);
    expect(screen.getByText("2554")).toBeInTheDocument(); // TDEE
    expect(screen.getByText(/1648 kcal\/dia/)).toBeInTheDocument(); // TMB
    expect(screen.getByText(/Mifflin-St Jeor/)).toBeInTheDocument();
  });

  it("mostra aviso quando o TDEE ainda não pôde ser calculado", () => {
    mockProfile = { ...fullProfile, tdee_calculated: null, bmr: null };
    render(<PerfilPage />);
    expect(
      screen.getByText(/TMB\/TDEE ainda indisponível/i),
    ).toBeInTheDocument();
  });
});
