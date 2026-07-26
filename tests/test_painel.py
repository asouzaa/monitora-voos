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
        self.assertEqual(dados["resumo"]["menor_preco_historico"], 2156.0)
        self.assertEqual(dados["ofertas"][0]["companhia"], "Azul")
        self.assertEqual(dados["historico"][0]["quantidade_ofertas"], 1)
        self.assertTrue(dados["planilha"]["disponivel"])


def _oferta(identificador: str, preco: str) -> OfertaVoo:
    return OfertaVoo(
        identificador=identificador,
        companhia="Azul",
        partida_ida="2026-12-29T03:10:00",
        chegada_ida="2026-12-29T10:20:00",
        conexoes_ida=1,
        duracao_ida="PT7H10M",
        partida_volta="2027-01-06T12:00:00",
        chegada_volta="2027-01-06T16:20:00",
        conexoes_volta=0,
        duracao_volta="PT4H20M",
        preco_total=Decimal(preco),
        moeda="BRL",
    )


if __name__ == "__main__":
    unittest.main()
