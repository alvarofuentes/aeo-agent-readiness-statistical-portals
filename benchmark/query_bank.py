"""Generate the canonical 120-query statistical-portal benchmark.

The committed CSV is the execution contract. This generator must reproduce it
exactly: 24 templates per portal and the declared global stratum totals.
"""
from __future__ import annotations

import csv
from pathlib import Path

PORTALS = ["worldbank", "who", "cepalstat", "undata", "sdg"]
COUNTRIES = [
    ("Chile", "CHL"), ("Argentina", "ARG"), ("Brazil", "BRA"), ("Mexico", "MEX"),
    ("Colombia", "COL"), ("Peru", "PER"), ("Uruguay", "URY"), ("Costa Rica", "CRI"),
    ("Ecuador", "ECU"), ("Bolivia", "BOL"),
]
GDP_PAIRS = [
    ("PIB total", "PIB per cápita"),
    ("PIB a precios corrientes", "PIB a precios constantes"),
    ("PIB en dólares corrientes", "PIB en dólares constantes"),
    ("PIB nivel", "crecimiento del PIB"),
    ("PIB total", "PIB por actividad económica"),
]
TEMPLATES = [
    ("discovery", "Encuentra la fuente oficial para el PIB de {country} y dame la URL de la serie más pertinente."),
    ("discovery", "¿Dónde puedo consultar oficialmente el PIB de {country} para 2024?"),
    ("discovery", "Localiza el indicador oficial de PIB de {country} y explica por qué esa página es la adecuada."),
    ("discovery", "Encuentra una página o API oficial con datos de PIB para {country} y cita la fuente."),
    ("exact_indicator", "¿Cuál fue el {indicator} de {country} en 2024?"),
    ("exact_indicator", "Dame el valor de {indicator} de {country} para 2023 y 2024."),
    ("exact_indicator", "Busca la serie oficial de {indicator} de {country} y devuelve el dato de 2024."),
    ("exact_indicator", "¿Qué indicador usarías para responder: {indicator} de {country} en 2024?"),
    ("semantic_disambiguation", "Para {country} en 2024, ¿debo usar {a} o {b}? Explica la diferencia estadística."),
    ("semantic_disambiguation", "Distingue correctamente entre {a} y {b} para responder una consulta sobre {country}."),
    ("semantic_disambiguation", "Un usuario pide el tamaño de la economía de {country}. ¿Es mejor {a} o {b}?"),
    ("semantic_disambiguation", "Un usuario pide el crecimiento económico de {country}. ¿Qué serie corresponde y qué series no deben usarse?"),
    ("semantic_disambiguation", "Un usuario pide una comparación internacional del PIB de {country}. ¿Qué medida evitaría mezclar niveles con tasas de crecimiento?"),
    ("dimensions", "Compara el PIB de {country} entre 2023 y 2024 y conserva la misma unidad y frecuencia."),
    ("dimensions", "¿El dato de PIB de {country} es anual o trimestral? Verifica la frecuencia."),
    ("dimensions", "¿El PIB de {country} está expresado en moneda nacional, USD o USD por habitante? Verifica la unidad."),
    ("comparison", "Compara el PIB de {country} y {other} en 2024 usando una medida estadísticamente comparable."),
    ("comparison", "Compara el crecimiento del PIB de {country} y {other} en 2024."),
    ("comparison", "¿Qué economía es mayor en 2024, {country} o {other}? Define la medida usada."),
    ("temporal", "¿Cuál es el último año disponible para el PIB de {country}? Indica fecha de actualización si existe."),
    ("temporal", "Compara 2019, 2020 y 2024 para el PIB de {country}."),
    ("metadata", "¿Qué significa exactamente el indicador de PIB que encontraste para {country}? Cita su definición."),
    ("metadata", "¿Quién produce el dato de PIB de {country}, cuál es la fuente y qué metodología declara?"),
    ("citation", "Responde con el PIB de {country} en 2024 y proporciona una cita o URL verificable de la evidencia."),
]
EXPECTED_PER_PORTAL = {
    "discovery": 4, "exact_indicator": 4, "semantic_disambiguation": 5,
    "dimensions": 3, "comparison": 3, "temporal": 2, "metadata": 2, "citation": 1,
}


def build() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    qid = 1
    for portal in PORTALS:
        by_stratum: dict[str, int] = {k: 0 for k in EXPECTED_PER_PORTAL}
        country_idx = 0
        for kind, template in TEMPLATES:
            country, code = COUNTRIES[country_idx % len(COUNTRIES)]
            other, _ = COUNTRIES[(country_idx + 1) % len(COUNTRIES)]
            a, b = GDP_PAIRS[country_idx % len(GDP_PAIRS)]
            rows.append({
                "query_id": f"Q{qid:03d}", "portal_id": portal, "stratum": kind,
                "query": template.format(country=country, other=other, indicator=a, a=a, b=b),
                "country": country, "country_code": code,
            })
            by_stratum[kind] += 1
            qid += 1
            country_idx += 1
        if by_stratum != EXPECTED_PER_PORTAL:
            raise AssertionError(f"Unexpected stratum distribution for {portal}: {by_stratum}")
    if len(rows) != 120:
        raise AssertionError(f"Expected 120 queries, got {len(rows)}")
    return rows


def write_bank(path: Path) -> None:
    rows = build()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    out = Path(__file__).with_name("query-bank-120.csv")
    write_bank(out)
    print(out, 120)
