from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any, Iterable

from fast_flights import (
    FlightQuery,
    Passengers,
    ShoppingOptions,
    create_query,
    get_flights,
    get_return_flights,
    select_flight,
)

from .configuracao import (
    ADULTOS,
    CLASSE_VIAGEM,
    DESTINO,
    MAX_IDAS_CANDIDATAS,
    MAX_OFERTAS,
    MOEDA,
    ORIGEM,
    PERIODOS_MONITORADOS,
)
from .ofertas import OfertaVoo


class RaspadorGoogleVoos:
    def buscar_ofertas(self) -> list[OfertaVoo]:
        ofertas: list[OfertaVoo] = []
        erros: list[str] = []

        for data_ida, data_volta in PERIODOS_MONITORADOS:
            try:
                ofertas.extend(self._buscar_ofertas_periodo(data_ida, data_volta))
            except Exception as erro:
                erros.append(f"{data_ida}/{data_volta}: {erro}")

        if not ofertas and erros:
            raise RuntimeError("; ".join(erros))

        limite_total = MAX_OFERTAS * len(PERIODOS_MONITORADOS)
        return _ordenar_e_limitar(ofertas, limite_total)

    def _buscar_ofertas_periodo(
        self,
        data_ida: str,
        data_volta: str,
    ) -> list[OfertaVoo]:
        consulta = create_query(
            flights=[
                FlightQuery(
                    date=data_ida,
                    from_airport=ORIGEM,
                    to_airport=DESTINO,
                ),
                FlightQuery(
                    date=data_volta,
                    from_airport=DESTINO,
                    to_airport=ORIGEM,
                ),
            ],
            seat=CLASSE_VIAGEM,
            trip="round-trip",
            passengers=Passengers(adults=ADULTOS),
            language="pt-BR",
            currency=MOEDA,
        )
        ordenacao = ShoppingOptions(ranking_mode="cheapest", result_sort="price")
        opcoes_ida = get_flights(consulta, shopping=ordenacao)
        if not opcoes_ida:
            return []

        ofertas: list[OfertaVoo] = []
        erros: list[str] = []

        for ida in _opcoes_mais_baratas(opcoes_ida, MAX_IDAS_CANDIDATAS):
            try:
                consulta_volta = select_flight(consulta, ida)
                opcoes_volta = get_return_flights(consulta_volta, shopping=ordenacao)
            except Exception as erro:
                erros.append(str(erro))
                continue

            ofertas.extend(converter_ofertas(ida, opcoes_volta[:MAX_OFERTAS]))

        if not ofertas and erros:
            raise RuntimeError("; ".join(erros))

        return _ordenar_e_limitar(ofertas, MAX_OFERTAS)


def converter_ofertas(ida: Any, opcoes_volta: Iterable[Any]) -> list[OfertaVoo]:
    if not ida.flights:
        return []

    ofertas: list[OfertaVoo] = []
    for volta in opcoes_volta:
        if not volta.flights:
            continue

        partida_ida, chegada_ida, duracao_ida = _resumir_itinerario(ida.flights)
        partida_volta, chegada_volta, duracao_volta = _resumir_itinerario(
            volta.flights
        )
        companhias = _companhias(ida.airlines, volta.airlines)
        preco = Decimal(str(volta.price))
        identificador = _identificador(ida.flights, volta.flights, preco)

        ofertas.append(
            OfertaVoo(
                identificador=identificador,
                companhia=companhias,
                partida_ida=partida_ida,
                chegada_ida=chegada_ida,
                conexoes_ida=max(0, len(ida.flights) - 1),
                duracao_ida=duracao_ida,
                partida_volta=partida_volta,
                chegada_volta=chegada_volta,
                conexoes_volta=max(0, len(volta.flights) - 1),
                duracao_volta=duracao_volta,
                preco_total=preco,
                moeda=MOEDA,
            )
        )

    return ofertas


def _opcoes_mais_baratas(opcoes: Iterable[Any], limite: int) -> list[Any]:
    return sorted(opcoes, key=lambda opcao: Decimal(str(opcao.price)))[:limite]


def _ordenar_e_limitar(ofertas: Iterable[OfertaVoo], limite: int) -> list[OfertaVoo]:
    unicas = {oferta.identificador: oferta for oferta in ofertas}
    return sorted(unicas.values(), key=lambda oferta: oferta.preco_total)[:limite]


def _resumir_itinerario(segmentos: list[Any]) -> tuple[str, str, str]:
    partida = _converter_data_hora(segmentos[0].departure)
    chegada = _converter_data_hora(segmentos[-1].arrival)
    minutos = int((chegada - partida).total_seconds() // 60)
    return partida.isoformat(), chegada.isoformat(), _duracao_iso(minutos)


def _converter_data_hora(valor: Any) -> datetime:
    return datetime(*valor.date, *valor.time)


def _duracao_iso(minutos: int) -> str:
    horas, minutos_restantes = divmod(max(0, minutos), 60)
    return f"PT{horas}H{minutos_restantes}M"


def _companhias(ida: list[str], volta: list[str]) -> str:
    nomes = list(dict.fromkeys([*ida, *volta]))
    return " / ".join(nome for nome in nomes if nome)


def _identificador(
    segmentos_ida: list[Any],
    segmentos_volta: list[Any],
    preco: Decimal,
) -> str:
    partes = []
    for segmento in [*segmentos_ida, *segmentos_volta]:
        partes.extend(
            [
                segmento.from_airport.code,
                segmento.to_airport.code,
                str(segmento.departure.date),
                str(segmento.departure.time),
                segmento.airline_code,
                segmento.flight_number,
            ]
        )
    partes.append(str(preco))
    return sha256("|".join(partes).encode("utf-8")).hexdigest()[:16]
