"""Teste da migração age → birth_date (AC-A1, fase A.1).

Exercita a conversão de dados real da migração `…_profile_birthdate` contra
Postgres: leva `user_profiles` ao estado pré-migração (coluna `age`), semeia um
perfil com `age=30`, aplica o `upgrade` e confere que `birth_date` deriva para
01/01/(ano_atual−30) e que `age` deixa de existir; depois aplica o `downgrade` e
confere que `age` volta a 30. Tudo dentro de uma transação revertida ao final —
DDL no Postgres é transacional, então a tabela compartilhada não é alterada.

As SQLs de conversão são importadas da própria migração (fonte única), de modo
que o cast `::int` obrigatório em `EXTRACT` é o mesmo testado aqui e aplicado em
produção.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260702_b8c9d0e1f2a3_profile_birthdate.py"
)


def _load_migration_sql() -> tuple[str, str]:
    spec = importlib.util.spec_from_file_location("_mig_birthdate", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.UPGRADE_SET_BIRTHDATE, module.DOWNGRADE_SET_AGE


async def _column_names(db: AsyncSession) -> set[str]:
    result = await db.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'user_profiles'"
        )
    )
    return {row[0] for row in result.all()}


class TestMigrationProfileBirthdate:
    async def test_age_converte_para_birthdate_e_volta(self, db: AsyncSession) -> None:
        upgrade_sql, downgrade_sql = _load_migration_sql()
        expected_year = date.today().year - 30
        try:
            # --- Estado pré-migração: user_profiles com `age`, sem `birth_date`.
            await db.execute(text("ALTER TABLE user_profiles DROP COLUMN birth_date"))
            await db.execute(text("ALTER TABLE user_profiles ADD COLUMN age INTEGER"))

            user_id = (
                await db.execute(
                    text(
                        "INSERT INTO users (email, name, password_hash, is_active) "
                        "VALUES ('mig@caloria.com', 'Mig', 'x', true) RETURNING id"
                    )
                )
            ).scalar_one()
            await db.execute(
                text(
                    "INSERT INTO user_profiles (user_id, age, activity_level) "
                    "VALUES (:uid, 30, 'SEDENTARY')"
                ),
                {"uid": user_id},
            )

            # --- upgrade: add birth_date, converte, dropa age.
            await db.execute(
                text("ALTER TABLE user_profiles ADD COLUMN birth_date DATE")
            )
            await db.execute(text(upgrade_sql))
            await db.execute(text("ALTER TABLE user_profiles DROP COLUMN age"))

            birth_date = (
                await db.execute(
                    text("SELECT birth_date FROM user_profiles WHERE user_id = :uid"),
                    {"uid": user_id},
                )
            ).scalar_one()
            assert birth_date == date(expected_year, 1, 1)
            cols = await _column_names(db)
            assert "birth_date" in cols
            assert "age" not in cols

            # --- downgrade: recria age a partir de birth_date.
            await db.execute(text("ALTER TABLE user_profiles ADD COLUMN age INTEGER"))
            await db.execute(text(downgrade_sql))
            await db.execute(text("ALTER TABLE user_profiles DROP COLUMN birth_date"))

            age = (
                await db.execute(
                    text("SELECT age FROM user_profiles WHERE user_id = :uid"),
                    {"uid": user_id},
                )
            ).scalar_one()
            assert age == 30
            cols = await _column_names(db)
            assert "age" in cols
            assert "birth_date" not in cols
        finally:
            # DDL transacional: rollback restaura a tabela ao formato do modelo.
            await db.rollback()
