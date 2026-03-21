"""corrige search_text de registros TACO e remove duplicatas ruins do OpenFoodFacts

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-03-20 00:00:00.000000
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove registros OpenFoodFacts com valores calóricos incorretos
    # que sobrescreviam os registros TACO corretos via pg_trgm.
    # Feijão carioca openfoodfacts: 44 kcal/100g (errado — TACO tem 76 kcal)
    op.execute("""
        DELETE FROM foods
        WHERE source = 'openfoodfacts'
          AND name ILIKE '%feijão carioca%'
          AND calories_100g < 60
    """)

    # Encurta search_text de registros TACO para maximizar score de similaridade
    # pg_trgm. Strings longas diluem o score porque o denominador (trigramas únicos)
    # cresce — strings curtas e focadas no nome principal têm score muito maior.

    # Feijão carioca cozido (TACO id=318, ~76 kcal/100g)
    op.execute("""
        UPDATE foods
        SET search_text = 'feijão carioca cozido feijão carioca'
        WHERE source = 'taco'
          AND name ILIKE '%feijão carioca%'
          AND preparation ILIKE '%cozido%'
    """)

    # Ovo inteiro cozido (TACO id=370, ~146 kcal/100g)
    op.execute("""
        UPDATE foods
        SET search_text = 'ovo inteiro cozido ovo cozido'
        WHERE source = 'taco'
          AND name ILIKE '%ovo inteiro%'
          AND preparation ILIKE '%cozido%'
    """)

    # Ovo mexido (TACO id=371)
    op.execute("""
        UPDATE foods
        SET search_text = 'ovo mexido ovo mexido com oleo'
        WHERE source = 'taco'
          AND name ILIKE '%ovo%'
          AND preparation ILIKE '%mexido%'
    """)

    # Ovo frito (TACO id=372)
    op.execute("""
        UPDATE foods
        SET search_text = 'ovo frito estrelado ovo frito no sol'
        WHERE source = 'taco'
          AND name ILIKE '%ovo%'
          AND preparation ILIKE '%frito%'
    """)

    # Clara de ovo cozida (TACO id=373)
    op.execute("""
        UPDATE foods
        SET search_text = 'clara de ovo cozida clara ovo'
        WHERE source = 'taco'
          AND name ILIKE '%clara%'
          AND name ILIKE '%ovo%'
    """)

    # Mandioca/aipim cozida (TACO id=396, ~125 kcal/100g)
    op.execute("""
        UPDATE foods
        SET search_text = 'aipim cozido mandioca'
        WHERE source = 'taco'
          AND (name ILIKE '%mandioca%' OR name ILIKE '%aipim%')
          AND preparation ILIKE '%cozid%'
    """)

    # Mandioca/aipim frita (TACO id=397)
    op.execute("""
        UPDATE foods
        SET search_text = 'mandioca frita aipim frito macaxeira frita'
        WHERE source = 'taco'
          AND (name ILIKE '%mandioca%' OR name ILIKE '%aipim%')
          AND preparation ILIKE '%frit%'
    """)


def downgrade() -> None:
    # Revertemos os search_text para os valores originais do TACO
    # (mesmos que seriam gerados pelo script de importação).
    # A deleção do registro OpenFoodFacts não é revertida para evitar
    # reintroduzir dados incorretos.

    op.execute("""
        UPDATE foods
        SET search_text = name || ' ' || COALESCE(preparation, '') || ' ' ||
                          COALESCE(array_to_string(aliases, ' '), '')
        WHERE source = 'taco'
          AND (
            name ILIKE '%feijão carioca%'
            OR (name ILIKE '%ovo%')
            OR name ILIKE '%mandioca%'
            OR name ILIKE '%aipim%'
          )
    """)
