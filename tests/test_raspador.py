from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch

from monitora_voo.raspador import RaspadorGoogleVoos, converter_ofertas


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

    def test_busca_varias_idas_para_encontrar_menor_preco_total(self) -> None:
        ida_mais_barata = _opcao(
            preco=900,
            companhia="Azul",
            origem="BEL",
            destino="REC",
            partida=(2026, 12, 29, 17, 55),
            chegada=(2026, 12, 29, 20, 25),
            codigo="AD",
            numero="4432",
        )
        ida_segunda_opcao = _opcao(
            preco=950,
            companhia="Gol",
            origem="BEL",
            destino="REC",
            partida=(2026, 12, 29, 6, 10),
            chegada=(2026, 12, 29, 11, 45),
            codigo="G3",
            numero="1750",
        )
        volta_total_2156 = _opcao(
            preco=2156,
            companhia="Azul",
            origem="REC",
            destino="BEL",
            partida=(2027, 1, 6, 10, 30),
            chegada=(2027, 1, 6, 13, 5),
            codigo="AD",
            numero="4541",
        )
        volta_total_2091 = _opcao(
            preco=2091,
            companhia="Gol",
            origem="REC",
            destino="BEL",
            partida=(2027, 1, 6, 4, 20),
            chegada=(2027, 1, 6, 9, 55),
            codigo="G3",
            numero="1681",
        )

        def selecionar(_, ida):
            return ida

        def buscar_voltas(ida, *, shopping):
            if ida is ida_mais_barata:
                return [volta_total_2156]
            return [volta_total_2091]

        with (
            patch(
                "monitora_voo.raspador.get_flights",
                return_value=[ida_mais_barata, ida_segunda_opcao],
            ),
            patch("monitora_voo.raspador.select_flight", side_effect=selecionar),
            patch("monitora_voo.raspador.get_return_flights", side_effect=buscar_voltas),
        ):
            ofertas = RaspadorGoogleVoos().buscar_ofertas()

        self.assertEqual(
            [oferta.preco_total for oferta in ofertas],
            [Decimal("2091"), Decimal("2156")],
        )


def _para_objeto(valor):
    if isinstance(valor, dict):
        return SimpleNamespace(
            **{chave: _para_objeto(conteudo) for chave, conteudo in valor.items()}
        )
    if isinstance(valor, list):
        return [_para_objeto(item) for item in valor]
    return valor


def _opcao(
    *,
    preco: int,
    companhia: str,
    origem: str,
    destino: str,
    partida: tuple[int, int, int, int, int],
    chegada: tuple[int, int, int, int, int],
    codigo: str,
    numero: str,
):
    return SimpleNamespace(
        price=preco,
        airlines=[companhia],
        flights=[
            SimpleNamespace(
                from_airport=SimpleNamespace(code=origem),
                to_airport=SimpleNamespace(code=destino),
                departure=SimpleNamespace(date=partida[:3], time=partida[3:]),
                arrival=SimpleNamespace(date=chegada[:3], time=chegada[3:]),
                airline_code=codigo,
                flight_number=numero,
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
