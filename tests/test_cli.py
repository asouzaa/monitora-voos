from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch

from monitora_voo.cli import principal
from monitora_voo.configuracao import (
    DESTINOS_MONITORADOS,
    PLANILHAS_PADRAO,
    SAIDAS_PAINEL_PADRAO,
)


class CliTeste(unittest.TestCase):
    def test_executar_mantem_recife_como_destino_padrao(self) -> None:
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "monitoramento_voos.xlsx"
            with (
                patch.object(
                    sys,
                    "argv",
                    ["monitora_voo", "executar", "--planilha", str(caminho)],
                ),
                patch(
                    "monitora_voo.cli.executar_uma_vez",
                    return_value=True,
                ) as executar,
                self.assertRaises(SystemExit) as saida,
            ):
                principal()

        self.assertEqual(saida.exception.code, 0)
        executar.assert_called_once_with(caminho, "REC")

    def test_exportar_usa_arquivos_padrao_de_fortaleza(self) -> None:
        with (
            patch.object(
                sys,
                "argv",
                ["monitora_voo", "exportar", "--destino", "FOR"],
            ),
            patch("monitora_voo.cli.exportar_dados") as exportar,
            patch("builtins.print"),
        ):
            principal()

        exportar.assert_called_once_with(
            Path("monitoramento_fortaleza.xlsx"),
            Path("docs/dados_fortaleza.json"),
            "FOR",
        )

    def test_todos_os_destinos_tem_arquivos_padrao_independentes(self) -> None:
        self.assertEqual(set(PLANILHAS_PADRAO), set(DESTINOS_MONITORADOS))
        self.assertEqual(set(SAIDAS_PAINEL_PADRAO), set(DESTINOS_MONITORADOS))
        self.assertEqual(PLANILHAS_PADRAO["MCZ"], "monitoramento_maceio.xlsx")
        self.assertEqual(PLANILHAS_PADRAO["NAT"], "monitoramento_natal.xlsx")
        self.assertEqual(PLANILHAS_PADRAO["RIO"], "monitoramento_rio.xlsx")
        self.assertEqual(
            PLANILHAS_PADRAO["JPA"],
            "monitoramento_joao_pessoa.xlsx",
        )


if __name__ == "__main__":
    unittest.main()
