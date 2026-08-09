/**
 * Data `date-only` renderizada sem deslocar o dia (AC-23).
 *
 * `new Date("2026-08-02")` é interpretado como MEIA-NOITE UTC. Em fuso
 * negativo (Brasil, UTC-3) isso vira 21h do dia anterior, e o histórico de peso
 * exibia 01/08 para um registro de 02/08. O resto do código já resolvia com o
 * sufixo `"T12:00"`, que ancora a data no meio-dia local; o histórico de peso
 * era o único ponto que não usava.
 */

/** Reproduz o que a página fazia antes da correção. */
const semSufixo = (data: string) =>
  new Date(data).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "America/Sao_Paulo",
  });

/** Reproduz o que a página faz depois da correção. */
const comSufixo = (data: string) =>
  new Date(data + "T12:00").toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "America/Sao_Paulo",
  });

describe("data do histórico de peso", () => {
  it("a data exibida confere com a data registrada", () => {
    expect(comSufixo("2026-08-02")).toBe("02/08/2026");
  });

  it("sem o sufixo, o dia anterior era exibido em fuso negativo", () => {
    expect(semSufixo("2026-08-02")).toBe("01/08/2026");
  });

  it("a correção também vale na virada de mês", () => {
    expect(comSufixo("2026-09-01")).toBe("01/09/2026");
    expect(semSufixo("2026-09-01")).toBe("31/08/2026");
  });

  it("a correção também vale na virada de ano", () => {
    expect(comSufixo("2026-01-01")).toBe("01/01/2026");
  });
});
