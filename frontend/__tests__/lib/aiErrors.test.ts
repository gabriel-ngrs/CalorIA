import { AxiosError, AxiosHeaders } from "axios";
import { describeAnalyzeError } from "@/lib/aiErrors";

function axiosErrorWithStatus(status: number): AxiosError {
  const err = new AxiosError("falha", "ERR_BAD_RESPONSE");
  err.response = {
    status,
    statusText: "",
    data: {},
    headers: {},
    config: { headers: new AxiosHeaders() },
  };
  return err;
}

function axiosNetworkError(): AxiosError {
  // Sem `response` = falha de rede real.
  return new AxiosError("Network Error", "ERR_NETWORK");
}

describe("describeAnalyzeError", () => {
  it("503 → mensagem de IA indisponível (não fala em conexão)", () => {
    const msg = describeAnalyzeError(axiosErrorWithStatus(503));
    expect(msg).toMatch(/indisponível/i);
    expect(msg).not.toMatch(/conex|internet/i);
  });

  it("erro de rede (sem response) → mensagem de conexão", () => {
    expect(describeAnalyzeError(axiosNetworkError())).toMatch(/conex|internet/i);
  });

  it("500 genérico → erro de servidor, não de conexão", () => {
    const msg = describeAnalyzeError(axiosErrorWithStatus(500));
    expect(msg).toMatch(/servidor/i);
    expect(msg).not.toMatch(/internet/i);
  });

  it("422 → mensagem de dados inválidos", () => {
    expect(describeAnalyzeError(axiosErrorWithStatus(422))).toMatch(/revise/i);
  });

  it("erro desconhecido → fallback genérico", () => {
    expect(describeAnalyzeError(new Error("boom"))).toBe(
      "Erro ao analisar. Tente novamente.",
    );
  });
});
