# `runs/` — histórico de execuções do eval

`history.jsonl` é **append-only**. Uma linha por execução completa, amarrando a
métrica ao commit, à versão e ao `sha` de cada prompt, ao modelo, aos parâmetros
de amostragem e ao `sha` do dataset.

Regras:

- **Não reescrever linha histórica.** Uma medição antiga continua verdadeira
  sobre o commit em que foi feita; corrigi-la apaga a série.
- **Não colocar credencial, PII nem conteúdo de `.env`** aqui. O registro guarda
  identificadores e números, nunca segredo.
- O arquivo nasce vazio: `evals/report.py serie` reporta "histórico vazio" até a
  primeira execução agendada real.

`ultimo-relatorio.json` e `ultima-invariancia.json` são artefatos de uma execução
e ficam fora do git (ver `.gitignore`).
