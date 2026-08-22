ORIGEM = "BEL"
DESTINO_PADRAO = "REC"
DESTINO = DESTINO_PADRAO
DESTINOS_MONITORADOS = {
    "REC": "Recife",
    "FOR": "Fortaleza",
}
PERIODOS_MONITORADOS = [
    ("2026-12-29", "2027-01-06"),
    ("2026-12-29", "2027-01-07"),
    ("2026-12-30", "2027-01-06"),
    ("2026-12-30", "2027-01-07"),
    ("2026-12-29", "2027-01-05"),
    ("2026-12-30", "2027-01-08"),
]
ADULTOS = 1
CLASSE_VIAGEM = "economy"
MOEDA = "BRL"
MAX_OFERTAS = 20
MAX_IDAS_CANDIDATAS = 10
PLANILHA_PADRAO = "monitoramento_voos.xlsx"
PLANILHAS_PADRAO = {
    "REC": PLANILHA_PADRAO,
    "FOR": "monitoramento_fortaleza.xlsx",
}
SAIDAS_PAINEL_PADRAO = {
    "REC": "docs/dados.json",
    "FOR": "docs/dados_fortaleza.json",
}
