from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from json import dumps
from pathlib import Path

from .configuracao import (
    ADULTOS,
    CLASSE_VIAGEM,
    DESTINO_PADRAO,
    DESTINOS_MONITORADOS,
    ORIGEM,
    PERIODOS_MONITORADOS,
)
from .planilha import CABECALHO_CONSULTAS, carregar_planilha

LIMITE_OFERTAS_PAINEL = 5


def exportar_dados(
    caminho_planilha: Path,
    caminho_saida: Path,
    destino: str = DESTINO_PADRAO,
) -> None:
    if destino not in DESTINOS_MONITORADOS:
        raise ValueError(f"Destino não monitorado: {destino}.")

    dados = carregar_planilha(caminho_planilha)
    resumo = _resumo_para_dict(dados.resumo)
    consultas = [
        dict(zip(CABECALHO_CONSULTAS, linha, strict=False))
        for linha in dados.consultas[1:]
    ]
    por_consulta = _agrupar_consultas(consultas)
    ultima_consulta = max(por_consulta, default="")
    ofertas_ultima_consulta = por_consulta.get(ultima_consulta, [])
    comparacao_periodos = _comparar_periodos(ofertas_ultima_consulta)
    datas_vencedoras = _datas_vencedoras(comparacao_periodos)

    conteudo = {
        "rota": {
            "origem": ORIGEM,
            "destino": destino,
            "nome_destino": DESTINOS_MONITORADOS[destino],
            "periodos": [
                {"data_ida": data_ida, "data_volta": data_volta}
                for data_ida, data_volta in PERIODOS_MONITORADOS
            ],
            "adultos": ADULTOS,
            "classe": CLASSE_VIAGEM,
        },
        "resumo": {
            "menor_preco_historico": _numero(
                resumo.get("menor_preco_historico", "")
            ),
            "ultimo_menor_preco": _numero(resumo.get("ultimo_menor_preco", "")),
            "data_ultima_consulta": resumo.get("data_ultima_consulta", ""),
            "data_ultima_consulta_bem_sucedida": ultima_consulta,
            "quantidade_ofertas_vistas": int(
                resumo.get("quantidade_ofertas_vistas", "0") or 0
            ),
            "status": resumo.get("status", "sem consultas"),
        },
        "ofertas": [
            _normalizar_oferta(oferta)
            for oferta in sorted(
                ofertas_ultima_consulta,
                key=lambda item: _decimal(item.get("preco_total", ""))
                or Decimal("Infinity"),
            )[:LIMITE_OFERTAS_PAINEL]
        ],
        "comparacao_periodos": comparacao_periodos,
        "datas_vencedoras": datas_vencedoras,
        "historico": [
            {
                "consulta_em": consulta_em,
                "menor_preco": min(
                    (
                        _numero(oferta.get("preco_total", ""))
                        for oferta in ofertas
                        if _numero(oferta.get("preco_total", "")) is not None
                    ),
                    default=None,
                ),
                "queda_detectada": any(
                    oferta.get("queda_detectada") == "sim" for oferta in ofertas
                ),
                "quantidade_ofertas": len(ofertas),
            }
            for consulta_em, ofertas in por_consulta.items()
        ],
        "planilha": {
            "arquivo": caminho_planilha.name,
            "disponivel": caminho_planilha.exists(),
        },
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(
        dumps(conteudo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _comparar_periodos(
    ofertas: list[dict[str, str]],
) -> list[dict[str, object]]:
    menores: dict[tuple[str, str], Decimal] = {}
    periodos_validos = set(PERIODOS_MONITORADOS)

    for oferta in ofertas:
        periodo = (
            _data_voo(oferta.get("partida_ida", "")),
            _data_voo(oferta.get("partida_volta", "")),
        )
        preco = _decimal(oferta.get("preco_total", ""))
        if periodo not in periodos_validos or preco is None:
            continue
        menor_atual = menores.get(periodo)
        if menor_atual is None or preco < menor_atual:
            menores[periodo] = preco

    return [
        {
            "data_ida": data_ida,
            "data_volta": data_volta,
            "menor_preco": (
                float(menores[(data_ida, data_volta)])
                if (data_ida, data_volta) in menores
                else None
            ),
        }
        for data_ida, data_volta in PERIODOS_MONITORADOS
    ]


def _datas_vencedoras(
    comparacao_periodos: list[dict[str, object]],
) -> list[dict[str, object]]:
    precos = [
        periodo["menor_preco"]
        for periodo in comparacao_periodos
        if periodo["menor_preco"] is not None
    ]
    menor_preco = min(precos, default=None)
    if menor_preco is None:
        return []
    return [
        periodo.copy()
        for periodo in comparacao_periodos
        if periodo["menor_preco"] == menor_preco
    ]


def _data_voo(valor: str) -> str:
    return valor.split("T", maxsplit=1)[0] if valor else ""


def _agrupar_consultas(
    consultas: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    resultado: dict[str, list[dict[str, str]]] = {}
    for consulta in consultas:
        consulta_em = consulta.get("consulta_em", "")
        resultado.setdefault(consulta_em, []).append(consulta)
    return dict(sorted(resultado.items()))


def _normalizar_oferta(oferta: dict[str, str]) -> dict[str, object]:
    return {
        "identificador": oferta.get("identificador_oferta", ""),
        "companhia": oferta.get("companhia", ""),
        "partida_ida": oferta.get("partida_ida", ""),
        "chegada_ida": oferta.get("chegada_ida", ""),
        "conexoes_ida": int(oferta.get("conexoes_ida", "0") or 0),
        "duracao_ida": oferta.get("duracao_ida", ""),
        "partida_volta": oferta.get("partida_volta", ""),
        "chegada_volta": oferta.get("chegada_volta", ""),
        "conexoes_volta": int(oferta.get("conexoes_volta", "0") or 0),
        "duracao_volta": oferta.get("duracao_volta", ""),
        "preco_total": _numero(oferta.get("preco_total", "")),
        "moeda": oferta.get("moeda", ""),
        "queda_detectada": oferta.get("queda_detectada") == "sim",
    }


def _resumo_para_dict(resumo: list[list[str]]) -> dict[str, str]:
    return {
        linha[0]: linha[1]
        for linha in resumo[1:]
        if len(linha) >= 2
    }


def _decimal(valor: str) -> Decimal | None:
    if not valor:
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def _numero(valor: str) -> float | None:
    decimal = _decimal(valor)
    return float(decimal) if decimal is not None else None
