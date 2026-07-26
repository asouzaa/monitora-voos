from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import json
import unittest

from monitora_voo.raspador import converter_ofertas


class RaspadorGoogleVoosTeste(unittest.TestCase):
    def test_converte_resultado_do_google_voos(self) -> None:
        caminho = Path(__file__).parent / "fixtures" / "google_voos_ofertas.json"
        resposta = json.loads(caminho.read_text(encoding="utf-8"))
        ida = _para_objeto(resposta["ida"])
        voltas = [_para_objeto(item) for item in resposta["voltas"]]

        ofertas = converter_ofertas(ida, voltas)

        self.assertEqual(len(ofertas), 2)
        self.assertEqual(ofertas[0].companhia, "Azul / Gol")
        self.assertEqual(ofertas[0].partida_ida, "2026-12-29T03:15:00")
        self.assertEqual(ofertas[0].conexoes_ida, 0)
        self.assertEqual(ofertas[0].duracao_ida, "PT2H45M")
        self.assertEqual(ofertas[0].partida_volta, "2027-01-06T12:00:00")
        self.assertEqual(ofertas[0].conexoes_volta, 1)
        self.assertEqual(ofertas[0].duracao_volta, "PT8H0M")
        self.assertEqual(ofertas[0].preco_total, Decimal("2156"))
        self.assertEqual(ofertas[0].moeda, "BRL")
        self.assertEqual(len(ofertas[0].identificador), 16)
        self.assertEqual(ofertas[1].companhia, "Azul")


def _para_objeto(valor):
    if isinstance(valor, dict):
        return SimpleNamespace(
            **{chave: _para_objeto(conteudo) for chave, conteudo in valor.items()}
        )
    if isinstance(valor, list):
        return [_para_objeto(item) for item in valor]
    return valor


if __name__ == "__main__":
    unittest.main()
