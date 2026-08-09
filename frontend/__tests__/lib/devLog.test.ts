/**
 * Logs de diagnóstico não podem aparecer em produção (AC-23).
 *
 * `devLog`/`devError` leem `NODE_ENV` no import do módulo, então cada cenário
 * precisa reimportar com o ambiente já definido.
 */

const ambienteOriginal = process.env.NODE_ENV;

function comAmbiente(valor: string) {
  jest.resetModules();
  Object.defineProperty(process.env, "NODE_ENV", {
    value: valor,
    configurable: true,
  });
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require("@/lib/dev-log") as typeof import("@/lib/dev-log");
}

afterEach(() => {
  Object.defineProperty(process.env, "NODE_ENV", {
    value: ambienteOriginal,
    configurable: true,
  });
  jest.restoreAllMocks();
});

describe("devLog", () => {
  it("não escreve no console em produção", () => {
    const spy = jest.spyOn(console, "log").mockImplementation(() => {});
    comAmbiente("production").devLog("[API→] GET /meals");
    expect(spy).not.toHaveBeenCalled();
  });

  it("escreve no console em desenvolvimento", () => {
    const spy = jest.spyOn(console, "log").mockImplementation(() => {});
    comAmbiente("development").devLog("[API→] GET /meals");
    expect(spy).toHaveBeenCalledWith("[API→] GET /meals");
  });

  it("não escreve durante os testes", () => {
    const spy = jest.spyOn(console, "log").mockImplementation(() => {});
    comAmbiente("test").devLog("ruído");
    expect(spy).not.toHaveBeenCalled();
  });
});

describe("devError", () => {
  it("não escreve no console em produção", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    comAmbiente("production").devError("[API✗] 500");
    expect(spy).not.toHaveBeenCalled();
  });

  it("escreve no console em desenvolvimento", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    comAmbiente("development").devError("[API✗] 500");
    expect(spy).toHaveBeenCalledWith("[API✗] 500");
  });
});
