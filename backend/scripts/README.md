# Scripts de Utilitários — Backend

Scripts para popular o banco e importar dados externos. **Nunca rodar em produção com dados reais.**

---

## seed_dev_user.py

Cria um único usuário de desenvolvimento com perfil completo e dados realistas dos últimos 30 dias (refeições, peso, hidratação, humor, lembretes). Ideal para desenvolvimento diário.

```bash
# Via Docker
docker compose -f docker-compose.dev.yml exec backend python scripts/seed_dev_user.py

# Via Make
make seed-user
```

---

## seed_all.py

Seed completo: múltiplos usuários de teste com histórico variado (60–90 dias). Útil para testar cenários de edge case (usuário sem dados, com muitos dados, etc.).

```bash
# Via Docker
docker compose -f docker-compose.dev.yml exec backend python scripts/seed_all.py

# Via Make
make seed
```

---

## seed_taco.py

Importa a tabela TACO (~600 alimentos brasileiros) para o banco. **Executar uma única vez** após criar o banco — as migrações do Alembic criam a tabela mas não populam.

```bash
docker compose -f docker-compose.dev.yml exec backend python scripts/seed_taco.py
```

---

## import_off.py

Importa produtos do **Open Food Facts** (OFF) para complementar o banco TACO com produtos processados/embalados brasileiros. Faz download paginado da API pública; pode demorar alguns minutos.

```bash
docker compose -f docker-compose.dev.yml exec backend python scripts/import_off.py
```

> **Nota:** o TACO já cobre a maioria dos alimentos in natura. O OFF é opcional e aumenta a base para alimentos industrializados.

---

## Ordem recomendada para setup inicial

```bash
make migrate       # 1. Cria as tabelas
make seed          # 2. Seed TACO (embutido no seed_all) + dados de dev
```
