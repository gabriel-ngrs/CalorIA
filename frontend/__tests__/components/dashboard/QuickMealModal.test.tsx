/**
 * O modal de refeição abre no modo pedido pelo atalho (AC-23).
 *
 * Os três atalhos do dashboard (Foto, Texto, Áudio) apontavam para o mesmo
 * modal sem dizer qual modo queriam, e ele abria sempre em texto.
 */

import { render, screen } from "@testing-library/react";
import { QuickMealModal } from "@/components/dashboard/QuickAddModals";

jest.mock("@/lib/hooks/useMeals", () => ({
  useAnalyzeMeal: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useAnalyzePhoto: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateMeal: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

jest.mock("@/lib/hooks/useLogs", () => ({
  useLogHydration: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useLogMood: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useLogWeight: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

/** O botão de modo ativo é o que ganha o fundo destacado. */
function modoAtivo(): string | undefined {
  return ["Texto", "Foto", "Áudio"].find((label) =>
    screen
      .getByRole("button", { name: new RegExp(label) })
      .className.includes("bg-background"),
  );
}

describe("QuickMealModal — modo inicial", () => {
  it.each([
    ["text", "Texto"],
    ["photo", "Foto"],
    ["audio", "Áudio"],
  ] as const)("initialMode=%s abre em %s", (modo, rotulo) => {
    render(
      <QuickMealModal open onOpenChange={() => {}} initialMode={modo} />,
    );
    expect(modoAtivo()).toBe(rotulo);
  });

  it("sem initialMode o padrão continua sendo texto", () => {
    render(<QuickMealModal open onOpenChange={() => {}} />);
    expect(modoAtivo()).toBe("Texto");
  });

  it("reabrir com outro modo troca o modo exibido", () => {
    const { rerender } = render(
      <QuickMealModal open={false} onOpenChange={() => {}} initialMode="text" />,
    );
    rerender(
      <QuickMealModal open onOpenChange={() => {}} initialMode="photo" />,
    );
    expect(modoAtivo()).toBe("Foto");
  });
});
