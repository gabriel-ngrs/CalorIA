# Frente K — DX e Documentação

**Plano:** ver `plano.md` § Frente K.

## Achados desta frente

- AUD-054 — Versões dessincronizadas: `pyproject.toml`, `app/main.py` e `package.json` em `0.1.0` vs CHANGELOG em `[0.7.0]` (🟢 baixa).

## Notas e contexto

### § K.4 Versionamento — dessincronia confirmada (de `artefatos/K1-versions.txt`)

| Fonte | Versão | Local |
|---|---|---|
| `backend/pyproject.toml:7` | `0.1.0` | metadado do pacote Python |
| `backend/app/main.py:36` | `0.1.0` | `FastAPI(version="0.1.0")` → reportado no OpenAPI/Swagger |
| `backend/app/main.py:74` (health) | `0.1.0` | `/health` retorna no body (cross-ref AUD-050) |
| `frontend/package.json:version` | `0.1.0` | metadado do pacote Node |
| `CHANGELOG.md:14` | **`[0.7.0]` (2026-05-10)** | release mais recente |
| `CHANGELOG.md:10` | `[Não lançado]` | seção de WIP atual |

**Análise**: os 4 metadados de pacote/runtime estão **6 minor versions** atrás do CHANGELOG. O projeto operou com bumps narrativos (CHANGELOG cresce a cada release menor) mas nunca propagou para os arquivos canônicos. Comum em projetos cedo no ciclo, e **ninguém quebrou** porque:

1. Não há publicação em PyPI/npm (pacotes internos, deploy via SSH).
2. Nenhum cliente externo lê o `pyproject.toml` para checar versão (não há SDK consumido por terceiros).
3. O `/health` (AUD-050) reporta `0.1.0`, mas nenhum monitoring estava ligado mesmo (AUD-051).

Mas vira problema no momento que:

- **Sentry/APM é ativado** (AUD-051): eventos vão chegar com `release="0.1.0"`, todas as regressões agrupadas como se fossem da mesma versão; reverte para um deploy anterior fica impossível identificar onde quebrou.
- **`/health` é monitorado** por UptimeRobot/CloudWatch (AUD-050): rollback automático baseado em versão impossível.
- **Bug report do usuário**: "tô vendo erro X" — qual deploy? Sem versão real, log/issue não correlaciona com o commit que introduziu.

**Recomendação consolidada (AUD-054)** — Esforço S (<1h):

1. **Fonte única de verdade**: escolher um dos formatos abaixo e propagar:
    - **Opção A (preferida)**: manter versão em `pyproject.toml` e ler dinamicamente em runtime via `importlib.metadata.version("caloria-backend")` (já recomendado em AUD-050). Frontend espelha em `package.json`, idealmente sincronizado por script em release.
    - **Opção B**: usar uma git tag (`v0.7.0`) como fonte de verdade e derivar via `setuptools-scm` (Python) e `git describe` (Node). Mais robusto para deploy mas exige mais setup.
2. **Bump release atual**: atualizar `pyproject.toml` e `package.json` para `0.7.0` agora (alinhar com `CHANGELOG.md:14`).
3. **Substituir hardcode** em `app/main.py:36,74` por leitura dinâmica (combina com AUD-050).
4. **Workflow de release**: documentar em `CONTRIBUTING.md` ou ADR — "antes de mergear para main, abrir PR de release que atualiza CHANGELOG, pyproject e package.json em sincronia". Cross-ref com AUD-049 (release como tag de log estruturado) e AUD-051 (release como tag do Sentry).
