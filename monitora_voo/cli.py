from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import sys
import time

from .configuracao import PLANILHA_PADRAO
from .painel import exportar_dados
from .planilha import registrar_consulta, registrar_erro
from .raspador import RaspadorGoogleVoos


def principal() -> None:
    parser = ArgumentParser(prog="monitora_voo")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    executar = subparsers.add_parser("executar", help="Executa uma consulta imediata.")
    executar.add_argument("--planilha", default=PLANILHA_PADRAO)

    monitorar = subparsers.add_parser("monitorar", help="Executa consultas recorrentes.")
    monitorar.add_argument("--intervalo-horas", type=float, default=6.0)
    monitorar.add_argument("--planilha", default=PLANILHA_PADRAO)

    exportar = subparsers.add_parser(
        "exportar",
        help="Exporta os dados da planilha para o painel web.",
    )
    exportar.add_argument("--planilha", default=PLANILHA_PADRAO)
    exportar.add_argument("--saida", default="docs/dados.json")

    args = parser.parse_args()

    if args.comando == "executar":
        sucesso = executar_uma_vez(Path(args.planilha))
        raise SystemExit(0 if sucesso else 1)

    if args.comando == "monitorar":
        monitorar_periodicamente(Path(args.planilha), args.intervalo_horas)

    if args.comando == "exportar":
        exportar_dados(Path(args.planilha), Path(args.saida))
        print(f"Dados do painel exportados para {args.saida}.")


def executar_uma_vez(caminho_planilha: Path) -> bool:
    consultado_em = datetime.now().astimezone()
    try:
        raspador = RaspadorGoogleVoos()
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


def monitorar_periodicamente(caminho_planilha: Path, intervalo_horas: float) -> None:
    if intervalo_horas <= 0:
        raise ValueError("--intervalo-horas deve ser maior que zero.")

    intervalo_segundos = intervalo_horas * 60 * 60
    print(f"Monitorando a cada {intervalo_horas:g} hora(s). Pressione Ctrl+C para parar.")

    try:
        while True:
            executar_uma_vez(caminho_planilha)
            time.sleep(intervalo_segundos)
    except KeyboardInterrupt:
        print("Monitoramento interrompido.")
