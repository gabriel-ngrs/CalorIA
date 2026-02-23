# CHANGELOG — CalorIA

Todas as mudanças significativas do projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versões seguem [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado
- Documentação inicial do projeto: CLAUDE.md, Roadmap.md, Prompt.md, README.md, CHANGELOG.md
- Plano completo de desenvolvimento em 9 fases no Roadmap.md
- Estrutura completa de pastas do projeto (backend/, frontend/, docs/)
- `.gitignore` cobrindo Python, Node.js/Next.js, Docker, IDEs e variáveis de ambiente
- `.env.example` com todas as variáveis necessárias documentadas
- `docker-compose.yml` com todos os serviços para produção local
- `docker-compose.dev.yml` com hot reload para backend e frontend, portas expostas para desenvolvimento
- Projeto base do backend: pyproject.toml, Dockerfile multi-stage, Alembic, ruff, mypy
- Módulos core: config (Settings), database (engine async), security (JWT + bcrypt), deps (get_db)
- Projeto base do frontend: Next.js 14, shadcn/ui, TanStack Query v5, next-auth v4, Recharts, axios
- Providers com QueryClientProvider e SessionProvider, cliente axios com interceptor de autenticação

---

<!-- Template para novas entradas:

## [X.Y.Z] - AAAA-MM-DD

### Adicionado
- Nova funcionalidade ou arquivo

### Alterado
- Mudança em funcionalidade existente

### Corrigido
- Bug corrigido

### Removido
- Funcionalidade ou arquivo removido

### Segurança
- Correção de vulnerabilidade

-->
