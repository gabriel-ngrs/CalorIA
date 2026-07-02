import { render, screen } from "@testing-library/react";
import { MarkdownLite } from "@/components/MarkdownLite";

describe("MarkdownLite (regressão B18)", () => {
  it("renderiza **negrito** como <strong>, sem asteriscos crus", () => {
    const { container } = render(
      <MarkdownLite content="Peso **estável** esta semana" />,
    );
    expect(container.querySelector("strong")?.textContent).toBe("estável");
    expect(container.textContent).not.toContain("**");
  });

  it("título '**Análise dos Hábitos**' vira negrito sem asteriscos", () => {
    const { container } = render(
      <MarkdownLite content="**Análise dos Hábitos Alimentares**" />,
    );
    expect(container.textContent).not.toContain("*");
    expect(screen.getByText("Análise dos Hábitos Alimentares").tagName).toBe(
      "STRONG",
    );
  });

  it("item numerado '**1)** ...' não mostra asteriscos", () => {
    const { container } = render(
      <MarkdownLite content={"**1)** Comer mais fibras\n**2)** Beber água"} />,
    );
    expect(container.textContent).not.toContain("*");
    expect(container.textContent).toContain("Comer mais fibras");
  });

  it("títulos markdown com # são exibidos sem o marcador", () => {
    const { container } = render(<MarkdownLite content="## Resumo do mês" />);
    expect(container.textContent).toBe("Resumo do mês");
  });
});
