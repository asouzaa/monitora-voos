from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile
import re
from xml.sax.saxutils import escape

from .ofertas import OfertaVoo


CABECALHO_CONSULTAS = [
    "consulta_em",
    "identificador_oferta",
    "companhia",
    "partida_ida",
    "chegada_ida",
    "conexoes_ida",
    "duracao_ida",
    "partida_volta",
    "chegada_volta",
    "conexoes_volta",
    "duracao_volta",
    "preco_total",
    "moeda",
    "queda_detectada",
]

CAMPOS_RESUMO = [
    "menor_preco_historico",
    "ultimo_menor_preco",
    "data_ultima_consulta",
    "quantidade_ofertas_vistas",
    "status",
]


@dataclass
class DadosPlanilha:
    consultas: list[list[str]]
    resumo: list[list[str]]


def registrar_consulta(
    caminho: Path,
    ofertas: Iterable[OfertaVoo],
    consultado_em: datetime,
) -> bool:
    ofertas_lista = list(ofertas)
    dados = carregar_planilha(caminho)
    menor_anterior = _menor_preco(dados.consultas)
    menor_atual = min((oferta.preco_total for oferta in ofertas_lista), default=None)
    queda_detectada = (
        menor_anterior is not None
        and menor_atual is not None
        and menor_atual < menor_anterior
    )

    consulta_em = consultado_em.isoformat(timespec="seconds")
    for oferta in ofertas_lista:
        dados.consultas.append(
            [
                consulta_em,
                oferta.identificador,
                oferta.companhia,
                oferta.partida_ida,
                oferta.chegada_ida,
                str(oferta.conexoes_ida),
                oferta.duracao_ida,
                oferta.partida_volta,
                oferta.chegada_volta,
                str(oferta.conexoes_volta),
                oferta.duracao_volta,
                _formatar_decimal(oferta.preco_total),
                oferta.moeda,
                "sim" if queda_detectada else "nao",
            ]
        )

    status = "queda detectada" if queda_detectada else "sem queda"
    if not ofertas_lista:
        status = "sem ofertas"

    menor_historico = _menor_preco(dados.consultas)
    dados.resumo = _montar_resumo(
        menor_historico=menor_historico,
        ultimo_menor_preco=menor_atual,
        consulta_em=consulta_em,
        quantidade_ofertas=len(dados.consultas) - 1,
        status=status,
    )
    salvar_planilha(caminho, dados)
    return queda_detectada


def registrar_erro(caminho: Path, mensagem: str, consultado_em: datetime) -> None:
    dados = carregar_planilha(caminho)
    menor_historico = _menor_preco(dados.consultas)
    resumo_atual = _resumo_para_dict(dados.resumo)
    ultimo_menor_preco = _decimal_ou_none(resumo_atual.get("ultimo_menor_preco", ""))
    dados.resumo = _montar_resumo(
        menor_historico=menor_historico,
        ultimo_menor_preco=ultimo_menor_preco,
        consulta_em=consultado_em.isoformat(timespec="seconds"),
        quantidade_ofertas=len(dados.consultas) - 1,
        status=f"erro: {mensagem[:180]}",
    )
    salvar_planilha(caminho, dados)


def carregar_planilha(caminho: Path) -> DadosPlanilha:
    if not caminho.exists():
        return DadosPlanilha(
            consultas=[CABECALHO_CONSULTAS.copy()],
            resumo=_montar_resumo(None, None, "", 0, "sem consultas"),
        )

    with ZipFile(caminho, "r") as arquivo:
        consultas = _ler_planilha_xml(arquivo.read("xl/worksheets/sheet1.xml"))
        resumo = _ler_planilha_xml(arquivo.read("xl/worksheets/sheet2.xml"))

    if not consultas:
        consultas = [CABECALHO_CONSULTAS.copy()]
    if consultas[0] != CABECALHO_CONSULTAS:
        raise ValueError("A aba Consultas não tem o formato esperado.")
    if not resumo:
        resumo = _montar_resumo(None, None, "", len(consultas) - 1, "sem consultas")

    return DadosPlanilha(consultas=consultas, resumo=resumo)


def salvar_planilha(caminho: Path, dados: DadosPlanilha) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(caminho, "w", ZIP_DEFLATED) as arquivo:
        arquivo.writestr("[Content_Types].xml", _content_types())
        arquivo.writestr("_rels/.rels", _rels_raiz())
        arquivo.writestr("docProps/app.xml", _app_xml())
        arquivo.writestr("docProps/core.xml", _core_xml())
        arquivo.writestr("xl/workbook.xml", _workbook_xml())
        arquivo.writestr("xl/_rels/workbook.xml.rels", _workbook_rels())
        arquivo.writestr("xl/styles.xml", _styles_xml())
        arquivo.writestr(
            "xl/worksheets/sheet1.xml",
            _sheet_xml("Consultas", dados.consultas),
        )
        arquivo.writestr(
            "xl/worksheets/sheet2.xml",
            _sheet_xml("Resumo", dados.resumo),
        )


def _montar_resumo(
    menor_historico: Decimal | None,
    ultimo_menor_preco: Decimal | None,
    consulta_em: str,
    quantidade_ofertas: int,
    status: str,
) -> list[list[str]]:
    valores = {
        "menor_preco_historico": _formatar_decimal(menor_historico),
        "ultimo_menor_preco": _formatar_decimal(ultimo_menor_preco),
        "data_ultima_consulta": consulta_em,
        "quantidade_ofertas_vistas": str(max(0, quantidade_ofertas)),
        "status": status,
    }
    return [["campo", "valor"], *[[campo, valores[campo]] for campo in CAMPOS_RESUMO]]


def _menor_preco(linhas: list[list[str]]) -> Decimal | None:
    if len(linhas) <= 1:
        return None

    indice_preco = CABECALHO_CONSULTAS.index("preco_total")
    precos: list[Decimal] = []
    for linha in linhas[1:]:
        if len(linha) <= indice_preco:
            continue
        preco = _decimal_ou_none(linha[indice_preco])
        if preco is not None:
            precos.append(preco)

    return min(precos, default=None)


def _decimal_ou_none(valor: str) -> Decimal | None:
    if not valor:
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def _formatar_decimal(valor: Decimal | None) -> str:
    if valor is None:
        return ""
    return format(valor, "f")


def _resumo_para_dict(resumo: list[list[str]]) -> dict[str, str]:
    resultado: dict[str, str] = {}
    for linha in resumo[1:]:
        if len(linha) >= 2:
            resultado[linha[0]] = linha[1]
    return resultado


def _ler_planilha_xml(conteudo: bytes) -> list[list[str]]:
    raiz = ElementTree.fromstring(conteudo)
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    linhas: list[list[str]] = []

    for row in raiz.findall(".//x:sheetData/x:row", namespace):
        valores: list[str] = []
        for celula in row.findall("x:c", namespace):
            referencia = celula.attrib.get("r", "")
            indice = _indice_coluna(referencia)
            while len(valores) < indice - 1:
                valores.append("")

            texto = ""
            inline = celula.find("x:is/x:t", namespace)
            valor = celula.find("x:v", namespace)
            if inline is not None and inline.text is not None:
                texto = inline.text
            elif valor is not None and valor.text is not None:
                texto = valor.text
            valores.append(texto)
        linhas.append(valores)

    return linhas


def _indice_coluna(referencia: str) -> int:
    letras = re.sub(r"[^A-Z]", "", referencia.upper())
    indice = 0
    for letra in letras:
        indice = indice * 26 + ord(letra) - ord("A") + 1
    return max(1, indice)


def _sheet_xml(nome: str, linhas: list[list[str]]) -> str:
    total_linhas = max(1, len(linhas))
    total_colunas = max((len(linha) for linha in linhas), default=1)
    dimensao = f"A1:{_nome_coluna(total_colunas)}{total_linhas}"
    linhas_xml = "\n".join(
        f'<row r="{numero}">'
        + "".join(
            _celula_xml(numero, coluna, valor)
            for coluna, valor in enumerate(linha, start=1)
        )
        + "</row>"
        for numero, linha in enumerate(linhas, start=1)
    )
    colunas_xml = "".join(
        f'<col min="{indice}" max="{indice}" width="22" customWidth="1"/>'
        for indice in range(1, total_colunas + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<dimension ref=\"{dimensao}\"/>"
        f"<cols>{colunas_xml}</cols>"
        f"<sheetData>{linhas_xml}</sheetData>"
        "</worksheet>"
    )


def _celula_xml(linha: int, coluna: int, valor: str) -> str:
    referencia = f"{_nome_coluna(coluna)}{linha}"
    texto = escape(str(valor))
    return f'<c r="{referencia}" t="inlineStr"><is><t>{texto}</t></is></c>'


def _nome_coluna(indice: int) -> str:
    nome = ""
    while indice:
        indice, resto = divmod(indice - 1, 26)
        nome = chr(ord("A") + resto) + nome
    return nome


def _content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _rels_raiz() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _workbook_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Consultas" sheetId="1" r:id="rId1"/>
<sheet name="Resumo" sheetId="2" r:id="rId2"/>
</sheets>
</workbook>"""


def _workbook_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>"""


def _app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
<Application>monitora_voo</Application>
</Properties>"""


def _core_xml() -> str:
    agora = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:creator>monitora_voo</dc:creator>
<cp:lastModifiedBy>monitora_voo</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">{agora}</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">{agora}</dcterms:modified>
</cp:coreProperties>"""
