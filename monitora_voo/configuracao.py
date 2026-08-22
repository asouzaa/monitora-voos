ORIGEM = "BEL"
DESTINO_PADRAO = "REC"
DESTINO = DESTINO_PADRAO
DESTINOS_MONITORADOS = {
    "REC": "Recife",
    "FOR": "Fortaleza",
    "MCZ": "Maceió",
    "NAT": "Natal",
    "RIO": "Rio de Janeiro",
    "JPA": "João Pessoa",
}
AEROPORTOS_POR_DESTINO = {
    **{codigo: (codigo,) for codigo in DESTINOS_MONITORADOS},
    "RIO": ("GIG", "SDU"),
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
    "MCZ": "monitoramento_maceio.xlsx",
    "NAT": "monitoramento_natal.xlsx",
    "RIO": "monitoramento_rio.xlsx",
    "JPA": "monitoramento_joao_pessoa.xlsx",
}
SAIDAS_PAINEL_PADRAO = {
    "REC": "docs/dados.json",
    "FOR": "docs/dados_fortaleza.json",
    "MCZ": "docs/dados_maceio.json",
    "NAT": "docs/dados_natal.json",
    "RIO": "docs/dados_rio.json",
    "JPA": "docs/dados_joao_pessoa.json",
}
