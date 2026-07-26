from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OfertaVoo:
    identificador: str
    companhia: str
    partida_ida: str
    chegada_ida: str
    conexoes_ida: int
    duracao_ida: str
    partida_volta: str
    chegada_volta: str
    conexoes_volta: int
    duracao_volta: str
    preco_total: Decimal
    moeda: str
