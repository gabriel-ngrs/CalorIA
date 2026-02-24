import { cn } from "@/lib/utils";

describe("cn", () => {
  it("combina classes simples", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("ignora valores falsy", () => {
    expect(cn("foo", undefined, null, false, "bar")).toBe("foo bar");
  });

  it("resolve conflitos do Tailwind (tw-merge)", () => {
    // tw-merge remove classes conflitantes — a última vence
    expect(cn("p-4", "p-8")).toBe("p-8");
  });

  it("retorna string vazia quando sem argumentos", () => {
    expect(cn()).toBe("");
  });

  it("suporta objetos condicionais do clsx", () => {
    expect(cn({ "font-bold": true, italic: false })).toBe("font-bold");
  });
});
