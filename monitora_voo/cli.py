from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import sys
import time

from .configuracao import (
    DESTINO_PADRAO,
    DESTINOS_MONITORADOS,
    PLANILHAS_PADRAO,
    SAIDAS_PAINEL_PADRAO,
)
from .painel import exportar_dados
from .planilha import registrar_consulta, registrar_erro
from .raspador import RaspadorGoogleVoos


def principal() -> None:
    parser = ArgumentParser(prog="monitora_voo")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    executar = subparsers.add_parser("executar", help="Executa uma consulta imediata.")
    _adicionar_destino(executar)
    executar.add_argument("--planilha")

    monitorar = subparsers.add_parser("monitorar", help="Executa consultas recorrentes.")
    _adicionar_destino(monitorar)
    monitorar.add_argument("--intervalo-horas", type=float, default=6.0)
    monitorar.add_argument("--planilha")

    exportar = subparsers.add_parser(
        "exportar",
        help="Exporta os dados da planilha para o painel web.",
    )
    _adicionar_destino(exportar)
    exportar.add_argument("--planilha")
    exportar.add_argument("--saida")

    args = parser.parse_args()
    caminho_planilha = Path(args.planilha or PLANILHAS_PADRAO[args.destino])

    if args.comando == "executar":
        sucesso = executar_uma_vez(caminho_planilha, args.destino)
        raise SystemExit(0 if sucesso else 1)

    if args.comando == "monitorar":
        monitorar_periodicamente(caminho_planilha, args.intervalo_horas, args.destino)

    if args.comando == "exportar":
        caminho_saida = Path(args.saida or SAIDAS_PAINEL_PADRAO[args.destino])
        exportar_dados(caminho_planilha, caminho_saida, args.destino)
        print(f"Dados do painel exportados para {caminho_saida}.")


def executar_uma_vez(
    caminho_planilha: Path,
    destino: str = DESTINO_PADRAO,
) -> bool:
    consultado_em = datetime.now().astimezone()
    try:
        raspador = RaspadorGoogleVoos(destino)
        ofertas = raspador.buscar_ofertas()
        queda = registrar_consulta(caminho_planilha, ofertas, consultado_em)
    except Exception as erro:
        registrar_erro(caminho_planilha, str(erro), consultado_em)
        print(f"Erro ao coletar voos: {erro}", file=sys.stderr)
        return False

    print(
        f"Consulta registrada em {caminho_planilha} com {len(ofertas)} oferta(s). "
        f"Queda detectada: {'sim' if queda else 'nao'}."
    )
    return True


def monitorar_periodicamente(
    caminho_planilha: Path,
    intervalo_horas: float,
    destino: str = DESTINO_PADRAO,
) -> None:
    if intervalo_horas <= 0:
        raise ValueError("--intervalo-horas deve ser maior que zero.")

    intervalo_segundos = intervalo_horas * 60 * 60
    print(f"Monitorando a cada {intervalo_horas:g} hora(s). Pressione Ctrl+C para parar.")

    try:
        while True:
            executar_uma_vez(caminho_planilha, destino)
            time.sleep(intervalo_segundos)
    except KeyboardInterrupt:
        print("Monitoramento interrompido.")


def _adicionar_destino(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--destino",
        choices=DESTINOS_MONITORADOS,
        default=DESTINO_PADRAO,
        help="Aeroporto de destino monitorado (padrão: REC).",
    )
