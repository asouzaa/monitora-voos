from datetime import datetime, timezone
from decimal import Decimal
from json import loads
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from monitora_voo.ofertas import OfertaVoo
from monitora_voo.painel import exportar_dados
from monitora_voo.planilha import registrar_consulta


class PainelTeste(unittest.TestCase):
    def test_exporta_resumo_ofertas_e_historico(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho_planilha = Path(pasta) / "monitoramento_voos.xlsx"
            caminho_json = Path(pasta) / "dados.json"
            registrar_consulta(
                caminho_planilha,
                [_oferta("1", "2156.00")],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )

            exportar_dados(caminho_planilha, caminho_json)
            dados = loads(caminho_json.read_text(encoding="utf-8"))

        self.assertEqual(dados["rota"]["origem"], "BEL")
        self.assertEqual(dados["rota"]["nome_destino"], "Recife")
        self.assertEqual(len(dados["rota"]["periodos"]), 6)
        self.assertEqual(dados["resumo"]["menor_preco_historico"], 2156.0)
        self.assertEqual(dados["ofertas"][0]["companhia"], "Azul")
        self.assertEqual(dados["historico"][0]["quantidade_ofertas"], 1)
        self.assertTrue(dados["planilha"]["disponivel"])
        self.assertEqual(
            dados["resumo"]["data_ultima_consulta_bem_sucedida"],
            "2026-07-26T12:00:00+00:00",
        )

    def test_exporta_apenas_as_cinco_ofertas_mais_baratas(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho_planilha = Path(pasta) / "monitoramento_voos.xlsx"
            caminho_json = Path(pasta) / "dados.json"
            ofertas = [
                _oferta(str(indice), preco)
                for indice, preco in enumerate(
                    ["2800", "2156", "2500", "2091", "2300", "2200"],
                    start=1,
                )
            ]
            registrar_consulta(
                caminho_planilha,
                ofertas,
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )

            exportar_dados(caminho_planilha, caminho_json)
            dados = loads(caminho_json.read_text(encoding="utf-8"))

        self.assertEqual(
            [oferta["preco_total"] for oferta in dados["ofertas"]],
            [2091.0, 2156.0, 2200.0, 2300.0, 2500.0],
        )
        self.assertEqual(dados["resumo"]["quantidade_ofertas_vistas"], 6)
        self.assertEqual(dados["historico"][0]["quantidade_ofertas"], 6)

    def test_exporta_periodos_e_todas_as_datas_vencedoras(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho_planilha = Path(pasta) / "monitoramento_fortaleza.xlsx"
            caminho_json = Path(pasta) / "dados_fortaleza.json"
            registrar_consulta(
                caminho_planilha,
                [
                    _oferta("1", "1900", "2026-12-29", "2027-01-06"),
                    _oferta("2", "1750", "2026-12-29", "2027-01-07"),
                    _oferta("3", "1750", "2026-12-30", "2027-01-06"),
                ],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )

            exportar_dados(caminho_planilha, caminho_json, "FOR")
            dados = loads(caminho_json.read_text(encoding="utf-8"))

        self.assertEqual(dados["rota"]["destino"], "FOR")
        self.assertEqual(dados["rota"]["nome_destino"], "Fortaleza")
        self.assertEqual(
            [periodo["menor_preco"] for periodo in dados["comparacao_periodos"][:3]],
            [1900.0, 1750.0, 1750.0],
        )
        self.assertEqual(
            [
                (periodo["data_ida"], periodo["data_volta"])
                for periodo in dados["datas_vencedoras"]
            ],
            [
                ("2026-12-29", "2027-01-07"),
                ("2026-12-30", "2027-01-06"),
            ],
        )

    def test_exporta_destino_sem_dados_sem_datas_vencedoras(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho_json = Path(pasta) / "dados_fortaleza.json"
            exportar_dados(
                Path(pasta) / "monitoramento_fortaleza.xlsx",
                caminho_json,
                "FOR",
            )
            dados = loads(caminho_json.read_text(encoding="utf-8"))

        self.assertIsNone(dados["resumo"]["ultimo_menor_preco"])
        self.assertEqual(dados["datas_vencedoras"], [])
        self.assertEqual(
            [periodo["menor_preco"] for periodo in dados["comparacao_periodos"]],
            [None] * 6,
        )

    def test_exporta_identificacao_dos_novos_destinos(self) -> None:
        destinos = {
            "MCZ": "Maceió",
            "NAT": "Natal",
            "RIO": "Rio de Janeiro",
            "JPA": "João Pessoa",
        }
        with TemporaryDirectory() as pasta:
            for codigo, nome in destinos.items():
                with self.subTest(destino=codigo):
                    caminho_json = Path(pasta) / f"dados_{codigo.lower()}.json"
                    exportar_dados(
                        Path(pasta) / f"monitoramento_{codigo.lower()}.xlsx",
                        caminho_json,
                        codigo,
                    )
                    dados = loads(caminho_json.read_text(encoding="utf-8"))

                    self.assertEqual(dados["rota"]["destino"], codigo)
                    self.assertEqual(dados["rota"]["nome_destino"], nome)

    def test_mantem_historicos_dos_destinos_isolados(self) -> None:
        with TemporaryDirectory() as pasta:
            pasta_temporaria = Path(pasta)
            planilha_recife = pasta_temporaria / "monitoramento_voos.xlsx"
            planilha_fortaleza = pasta_temporaria / "monitoramento_fortaleza.xlsx"
            dados_recife = pasta_temporaria / "dados.json"
            dados_fortaleza = pasta_temporaria / "dados_fortaleza.json"
            consulta_em = datetime(2026, 7, 26, 12, tzinfo=timezone.utc)

            registrar_consulta(
                planilha_recife,
                [_oferta("rec", "2100")],
                consulta_em,
            )
            registrar_consulta(
                planilha_fortaleza,
                [_oferta("for", "1800")],
                consulta_em,
            )
            exportar_dados(planilha_recife, dados_recife, "REC")
            exportar_dados(planilha_fortaleza, dados_fortaleza, "FOR")
            recife = loads(dados_recife.read_text(encoding="utf-8"))
            fortaleza = loads(dados_fortaleza.read_text(encoding="utf-8"))

        self.assertEqual(recife["resumo"]["menor_preco_historico"], 2100.0)
        self.assertEqual(fortaleza["resumo"]["menor_preco_historico"], 1800.0)
        self.assertEqual(recife["planilha"]["arquivo"], "monitoramento_voos.xlsx")
        self.assertEqual(
            fortaleza["planilha"]["arquivo"],
            "monitoramento_fortaleza.xlsx",
        )


def _oferta(
    identificador: str,
    preco: str,
    data_ida: str = "2026-12-29",
    data_volta: str = "2027-01-06",
) -> OfertaVoo:
    return OfertaVoo(
        identificador=identificador,
        companhia="Azul",
        partida_ida=f"{data_ida}T03:10:00",
        chegada_ida=f"{data_ida}T10:20:00",
        conexoes_ida=1,
        duracao_ida="PT7H10M",
        partida_volta=f"{data_volta}T12:00:00",
        chegada_volta=f"{data_volta}T16:20:00",
        conexoes_volta=0,
        duracao_volta="PT4H20M",
        preco_total=Decimal(preco),
        moeda="BRL",
    )


if __name__ == "__main__":
    unittest.main()
