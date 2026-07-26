from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from monitora_voo.ofertas import OfertaVoo
from monitora_voo.planilha import carregar_planilha, registrar_consulta, registrar_erro


class PlanilhaTeste(unittest.TestCase):
    def test_cria_planilha_vazia_ao_carregar_caminho_inexistente(self) -> None:
        with TemporaryDirectory() as pasta:
            dados = carregar_planilha(Path(pasta) / "monitoramento_voos.xlsx")

        self.assertEqual(dados.consultas[0][0], "consulta_em")
        self.assertEqual(dados.resumo[1], ["menor_preco_historico", ""])
        self.assertEqual(dados.resumo[5], ["status", "sem consultas"])

    def test_registra_consulta_na_planilha(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "monitoramento_voos.xlsx"
            queda = registrar_consulta(
                caminho,
                [_oferta("1", "1500.00")],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )
            dados = carregar_planilha(caminho)

        self.assertFalse(queda)
        self.assertEqual(len(dados.consultas), 2)
        self.assertEqual(dados.consultas[1][11], "1500.00")
        self.assertEqual(dados.resumo[1], ["menor_preco_historico", "1500.00"])

    def test_detecta_queda_de_preco(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "monitoramento_voos.xlsx"
            registrar_consulta(
                caminho,
                [_oferta("1", "1500.00")],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )
            queda = registrar_consulta(
                caminho,
                [_oferta("2", "1499.99")],
                datetime(2026, 7, 26, 18, tzinfo=timezone.utc),
            )
            dados = carregar_planilha(caminho)

        self.assertTrue(queda)
        self.assertEqual(dados.consultas[2][13], "sim")
        self.assertEqual(dados.resumo[1], ["menor_preco_historico", "1499.99"])
        self.assertEqual(dados.resumo[5], ["status", "queda detectada"])

    def test_nao_detecta_queda_quando_preco_igual_ou_maior(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "monitoramento_voos.xlsx"
            registrar_consulta(
                caminho,
                [_oferta("1", "1500.00")],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )
            queda = registrar_consulta(
                caminho,
                [_oferta("2", "1500.00"), _oferta("3", "1600.00")],
                datetime(2026, 7, 26, 18, tzinfo=timezone.utc),
            )
            dados = carregar_planilha(caminho)

        self.assertFalse(queda)
        self.assertEqual(dados.consultas[2][13], "nao")
        self.assertEqual(dados.consultas[3][13], "nao")
        self.assertEqual(dados.resumo[5], ["status", "sem queda"])

    def test_registra_erro_sem_remover_consultas_existentes(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "monitoramento_voos.xlsx"
            registrar_consulta(
                caminho,
                [_oferta("1", "1500.00")],
                datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
            )
            registrar_erro(
                caminho,
                "falha simulada",
                datetime(2026, 7, 26, 18, tzinfo=timezone.utc),
            )
            dados = carregar_planilha(caminho)

        self.assertEqual(len(dados.consultas), 2)
        self.assertEqual(dados.resumo[1], ["menor_preco_historico", "1500.00"])
        self.assertEqual(dados.resumo[5], ["status", "erro: falha simulada"])


def _oferta(identificador: str, preco: str) -> OfertaVoo:
    return OfertaVoo(
        identificador=identificador,
        companhia="Azul",
        partida_ida="2026-12-29T03:10:00",
        chegada_ida="2026-12-29T10:20:00",
        conexoes_ida=1,
        duracao_ida="PT5H10M",
        partida_volta="2027-01-06T12:00:00",
        chegada_volta="2027-01-06T16:20:00",
        conexoes_volta=0,
        duracao_volta="PT4H20M",
        preco_total=Decimal(preco),
        moeda="BRL",
    )


if __name__ == "__main__":
    unittest.main()

