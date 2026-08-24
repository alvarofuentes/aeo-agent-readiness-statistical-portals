"""Shared v2 schema for the technical AEO layer.

The v2 evaluation keeps two claims separate:
* ``e2e_*`` fields describe an agent completing a concrete portal query.
* the remaining fields describe machine-readability and technical access.

Statistical-portal rows stay ``not_rebuilt`` until they are rerun with the
same portal-directed search and technical evidence package. This prevents a
frozen pilot score from being presented as a fresh v2 finding.
"""
from __future__ import annotations

from typing import Any

TECHNICAL_FIELDS = [
    "portal_id", "portal", "evidence_date", "technical_score", "technical_confidence",
    "e2e_queries", "e2e_passes", "e2e_pass_rate", "candidate_count_mean",
    "specific_url_rate", "metadata_complete_rate", "citation_reproducible_rate",
    "robots_status", "sitemap_status", "llms_status", "jsonld_rendered",
    "api_direct_verified", "source_evidence_path", "status", "notes",
]


def blank_row(portal_id: str, portal: str, *, evidence_date: str = "2026-08-23") -> dict[str, Any]:
    row = {field: "" for field in TECHNICAL_FIELDS}
    row.update({
        "portal_id": portal_id,
        "portal": portal,
        "evidence_date": evidence_date,
        "status": "not_rebuilt",
        "notes": "Rehacer con flujo E2E dirigido al portal + auditoría técnica v2; no reutilizar resultados congelados.",
    })
    return row


def planning_row() -> dict[str, Any]:
    row = blank_row("planning", "Observatorio Regional de Planificación")
    row.update({
        "technical_score": 40,
        "technical_confidence": "media",
        "e2e_queries": 1,
        "e2e_passes": 1,
        "e2e_pass_rate": 1.0,
        "candidate_count_mean": 2,
        "specific_url_rate": 1.0,
        "metadata_complete_rate": 1.0,
        "citation_reproducible_rate": 1.0,
        "robots_status": "404",
        "sitemap_status": "404",
        "llms_status": "404",
        "jsonld_rendered": 0,
        "api_direct_verified": False,
        "source_evidence_path": "outputs/v2-2026-08-23/evidence/planning-e2e-2026-08-23.json",
        "status": "verified_one_case",
        "notes": "Gate E2E PASS en una consulta; el score técnico no incluye API HTTP independiente ni HTML inicial no capturado.",
    })
    return row


def statistical_rows() -> list[dict[str, Any]]:
    portals = [
        ("worldbank", "World Bank Open Data"),
        ("who", "WHO Data"),
        ("cepalstat", "CEPALSTAT"),
        ("undata", "UN Data Commons (UNSD)"),
        ("sdg", "UN SDG Indicators"),
    ]
    return [blank_row(portal_id, portal) for portal_id, portal in portals]


def current_rows() -> list[dict[str, Any]]:
    """Return the explicit v2 boundary used by reports and spreadsheets."""
    return [planning_row(), *statistical_rows()]
