from pathlib import Path
import unittest

from monitora_voo.configuracao import DESTINOS_MONITORADOS


class PaginasTeste(unittest.TestCase):
    def test_comparacao_e_analise_incluem_todos_os_destinos(self) -> None:
        pasta_docs = Path(__file__).parents[1] / "docs"
        pagina_inicial = (pasta_docs / "index.html").read_text(encoding="utf-8")
        comparacao = (pasta_docs / "comparacao.js").read_text(encoding="utf-8")
        painel = (pasta_docs / "painel.js").read_text(encoding="utf-8")

        for codigo in DESTINOS_MONITORADOS:
            with self.subTest(destino=codigo):
                self.assertIn(f'data-destino="{codigo}"', pagina_inicial)
                self.assertIn(f"destino={codigo}", pagina_inicial)
                self.assertIn(f"{codigo}:", comparacao)
                self.assertIn(f"{codigo}:", painel)

        self.assertEqual(pagina_inicial.count('class="cartao-destino"'), 6)


if __name__ == "__main__":
    unittest.main()
