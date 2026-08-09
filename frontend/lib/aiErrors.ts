import axios from "axios";

/**
 * Traduz um erro da análise de refeição (IA) em mensagem adequada à causa.
 *
 * BUG 5: antes qualquer falha exibia "verifique sua conexão", inclusive quando
 * o servidor respondia 503 (IA indisponível). Agora diferenciamos erro de rede
 * (sem resposta) de erro de servidor (com status HTTP).
 */
export function describeAnalyzeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    // Sem resposta = falha de rede real (offline, timeout, DNS).
    if (!error.response) {
      return "Sem conexão com o servidor. Verifique sua internet e tente novamente.";
    }

    const status = error.response.status;

    if (status === 503 || status === 502 || status === 504) {
      return "Serviço de IA temporariamente indisponível. Tente novamente em instantes.";
    }
    if (status === 429) {
      return "Muitas análises em sequência. Aguarde um instante e tente novamente.";
    }
    if (status >= 500) {
      return "Erro no servidor ao analisar. Tente novamente em instantes.";
    }
    if (status >= 400) {
      return "Não foi possível analisar. Revise a descrição/foto e tente novamente.";
    }
  }

  return "Erro ao analisar. Tente novamente.";
}
