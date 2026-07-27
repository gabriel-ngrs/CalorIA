"""A procedência do valor nutricional sobrevive ao salvamento e à leitura.

O pipeline de análise calcula, por item, de onde veio o número (`data_source`,
`food_id`) e qual porção o usuário descreveu. O front descartava esses campos
ao montar o `POST /meals`: a tela de revisão dizia "veio da tabela nutricional"
e a refeição gravada não sabia mais responder isso.

Sem procedência persistida não há como medir a precisão do produto — a métrica
"% de itens resolvidos pelo banco" não pode ser calculada sobre o histórico, e o
usuário não tem como calibrar a confiança no próprio diário.

Estes testes travam o contrato de ponta a ponta: gravar → ler de volta → agregar.
"""

from __future__ import annotations

from datetime import date

from httpx import AsyncClient

from app.models import User

_REFEICAO = {
    "meal_type": "dinner",
    "date": str(date.today()),
    "items": [
        {
            "food_name": "pizza de calabresa",
            # Massa já normalizada pela tabela de porções: 8 fatias × 100g.
            "quantity": 800,
            "unit": "g",
            "raw_input": "8 fatia",
            "calories": 2160,
            "protein": 96,
            "carbs": 240,
            "fat": 88,
            "fiber": 16,
            "data_source": "taco",
            "sodium": 4.2,
            "sugar": 8.0,
            "saturated_fat": 30.0,
        },
        {
            "food_name": "refrigerante",
            "quantity": 350,
            "unit": "g",
            "raw_input": "1 lata",
            "calories": 147,
            "protein": 0,
            "carbs": 37,
            "fat": 0,
            "fiber": 0,
            "data_source": "ai_estimated",
        },
    ],
}


class TestProcedenciaPersistida:
    async def test_data_source_sobrevive_ao_salvamento(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post("/api/v1/meals", json=_REFEICAO)
        assert resp.status_code == 201

        itens = {i["food_name"]: i for i in resp.json()["items"]}
        assert itens["pizza de calabresa"]["data_source"] == "taco"
        assert itens["refrigerante"]["data_source"] == "ai_estimated"

    async def test_porcao_descrita_sobrevive_ao_salvamento(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post("/api/v1/meals", json=_REFEICAO)
        itens = {i["food_name"]: i for i in resp.json()["items"]}
        # A refeição gravada consegue explicar de onde saíram os 800 g.
        assert itens["pizza de calabresa"]["raw_input"] == "8 fatia"
        assert itens["pizza de calabresa"]["quantity"] == 800
        assert itens["pizza de calabresa"]["unit"] == "g"

    async def test_micronutrientes_sobrevivem_ao_salvamento(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post("/api/v1/meals", json=_REFEICAO)
        pizza = next(
            i for i in resp.json()["items"] if i["food_name"] == "pizza de calabresa"
        )
        assert pizza["sodium"] == 4.2
        assert pizza["sugar"] == 8.0
        assert pizza["saturated_fat"] == 30.0

    async def test_procedencia_volta_na_leitura_da_refeicao(
        self, client: AsyncClient, test_user: User
    ) -> None:
        criada = await client.post("/api/v1/meals", json=_REFEICAO)
        meal_id = criada.json()["id"]

        lida = await client.get(f"/api/v1/meals/{meal_id}")
        assert lida.status_code == 200
        itens = {i["food_name"]: i for i in lida.json()["items"]}
        assert itens["pizza de calabresa"]["data_source"] == "taco"
        assert itens["refrigerante"]["data_source"] == "ai_estimated"
        assert itens["pizza de calabresa"]["raw_input"] == "8 fatia"

    async def test_procedencia_volta_na_listagem(
        self, client: AsyncClient, test_user: User
    ) -> None:
        await client.post("/api/v1/meals", json=_REFEICAO)
        lista = await client.get(f"/api/v1/meals?date={date.today()}")
        assert lista.status_code == 200
        itens = [i for m in lista.json() for i in m["items"]]
        fontes = {i["data_source"] for i in itens}
        assert fontes == {"taco", "ai_estimated"}

    async def test_percentual_resolvido_pelo_banco_e_calculavel(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """A métrica de precisão do produto depende deste dado estar gravado."""
        await client.post("/api/v1/meals", json=_REFEICAO)
        lista = await client.get(f"/api/v1/meals?date={date.today()}")
        itens = [i for m in lista.json() for i in m["items"]]
        do_banco = [
            i for i in itens if i["data_source"] and i["data_source"] != "ai_estimated"
        ]
        assert len(itens) == 2
        assert len(do_banco) == 1


class TestAgregadosUsamAQuantidadeNormalizada:
    async def test_total_do_dia_bate_com_a_soma_dos_itens(
        self, client: AsyncClient, test_user: User
    ) -> None:
        await client.post("/api/v1/meals", json=_REFEICAO)

        resumo = await client.get(f"/api/v1/dashboard/today?today={date.today()}")
        assert resumo.status_code == 200
        total = resumo.json()["nutrition"]["total_calories"]
        assert total == 2160 + 147

    async def test_dashboard_reflete_a_massa_normalizada(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """800 g de pizza — não 8 g, que era o que o pipeline antigo gravaria."""
        await client.post("/api/v1/meals", json=_REFEICAO)
        lista = await client.get(f"/api/v1/meals?date={date.today()}")
        pizza = next(
            i
            for m in lista.json()
            for i in m["items"]
            if i["food_name"] == "pizza de calabresa"
        )
        assert pizza["quantity"] == 800
        assert pizza["calories"] == 2160


class TestValidacaoDosCamposDeRastreabilidade:
    """`food_id`, `data_source` e `raw_input` vêm do cliente e vão para colunas
    tipadas — sem validação, erro de entrada virava erro de servidor."""

    async def test_food_id_inexistente_responde_422(
        self, client: AsyncClient, test_user: User
    ) -> None:
        payload = {
            "meal_type": "lunch",
            "date": str(date.today()),
            "items": [
                {
                    "food_name": "arroz",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 130,
                    "protein": 2.5,
                    "carbs": 28,
                    "fat": 0.2,
                    "food_id": 99_999_999,
                }
            ],
        }
        resp = await client.post("/api/v1/meals", json=payload)
        assert resp.status_code == 422, (
            "id inexistente deve ser erro de entrada, não IntegrityError não tratada"
        )

    async def test_food_id_negativo_e_recusado(
        self, client: AsyncClient, test_user: User
    ) -> None:
        payload = {
            "meal_type": "lunch",
            "date": str(date.today()),
            "items": [
                {
                    "food_name": "arroz",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 130,
                    "protein": 2.5,
                    "carbs": 28,
                    "fat": 0.2,
                    "food_id": -1,
                }
            ],
        }
        assert (await client.post("/api/v1/meals", json=payload)).status_code == 422

    async def test_data_source_fora_do_vocabulario_e_recusado(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """String livre estourava a coluna varchar(20) e devolvia 500."""
        payload = {
            "meal_type": "lunch",
            "date": str(date.today()),
            "items": [
                {
                    "food_name": "arroz",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 130,
                    "protein": 2.5,
                    "carbs": 28,
                    "fat": 0.2,
                    "data_source": "x" * 200,
                }
            ],
        }
        assert (await client.post("/api/v1/meals", json=payload)).status_code == 422

    async def test_raw_input_longo_demais_e_recusado(
        self, client: AsyncClient, test_user: User
    ) -> None:
        payload = {
            "meal_type": "lunch",
            "date": str(date.today()),
            "items": [
                {
                    "food_name": "arroz",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 130,
                    "protein": 2.5,
                    "carbs": 28,
                    "fat": 0.2,
                    "raw_input": "a" * 5000,
                }
            ],
        }
        assert (await client.post("/api/v1/meals", json=payload)).status_code == 422
