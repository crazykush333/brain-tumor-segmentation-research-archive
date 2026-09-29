"""Parse the TCIA BraTS 2021 crosswalk and derive the cohorts (§5, gate B6).

The crosswalk ``BraTS2021_MappingToTCIA.xlsx`` is licensed metadata and is never
committed. Its SHA-256 is recorded at gate B3. Column names are configuration
(``configs/dataset/brats2021.yaml``) and must be confirmed against the hashed
file at B3/B6.

Cohort rule: held-out institution = Site ID == "1" (all 511 UPenn-origin
cases); development = Site ID != "1" (740 cases). Selection is by site ID, never
by collection name. Count mismatches raise (SR3).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brats_uncertainty.errors import DataValidationError

PLACEHOLDER_TCIA_ID = "new-not-previously-in-TCIA"


@dataclass(frozen=True)
class CrosswalkRow:
    case_id: str
    site_id: str
    collection: str
    tcia_subject_id: str | None

    @property
    def has_real_tcia_id(self) -> bool:
        return bool(self.tcia_subject_id) and self.tcia_subject_id != PLACEHOLDER_TCIA_ID


def _norm_site(value: Any) -> str:
    if value is None:
        raise DataValidationError("missing site ID")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def parse_rows(
    records: Iterable[Mapping[str, Any]], columns: Mapping[str, str]
) -> list[CrosswalkRow]:
    """Convert raw records (dicts keyed by spreadsheet header) to typed rows."""
    rows: list[CrosswalkRow] = []
    for rec in records:
        case = rec.get(columns["case_id"])
        if case is None or str(case).strip() == "":
            continue  # blank spreadsheet row
        tcia = rec.get(columns["tcia_subject_id"])
        rows.append(
            CrosswalkRow(
                case_id=str(case).strip(),
                site_id=_norm_site(rec.get(columns["site_id"])),
                collection=str(rec.get(columns["collection"], "")).strip(),
                tcia_subject_id=str(tcia).strip() if tcia is not None else None,
            )
        )
    ids = [r.case_id for r in rows]
    if len(ids) != len(set(ids)):
        raise DataValidationError("duplicate case IDs in crosswalk")
    return rows


def read_xlsx_records(path: str | Path, sheet: str | None = None) -> list[dict[str, Any]]:
    """Read a spreadsheet into header-keyed dicts (requires the ``io`` extra)."""
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "install the optional extra: pip install 'brats-uncertainty[io]'"
        ) from exc
    wb = openpyxl.load_workbook(Path(path), read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    return [dict(zip(header, row, strict=False)) for row in it]


@dataclass(frozen=True)
class Cohorts:
    development: tuple[CrosswalkRow, ...]
    held_out_institution: tuple[CrosswalkRow, ...]


def derive_cohorts(
    rows: Iterable[CrosswalkRow],
    *,
    hoi_site_id: str,
    expected_total: int,
    expected_hoi: int,
    expected_development: int,
) -> Cohorts:
    """Split by site ID and assert the frozen counts (1,251 / 511 / 740)."""
    rows = list(rows)
    hoi = tuple(r for r in rows if r.site_id == hoi_site_id)
    dev = tuple(r for r in rows if r.site_id != hoi_site_id)
    problems = []
    if len(rows) != expected_total:
        problems.append(f"total {len(rows)} != {expected_total}")
    if len(hoi) != expected_hoi:
        problems.append(f"held-out institution {len(hoi)} != {expected_hoi}")
    if len(dev) != expected_development:
        problems.append(f"development {len(dev)} != {expected_development}")
    if problems:
        raise DataValidationError(
            "crosswalk counts do not match the frozen protocol (SR3 applies): "
            + "; ".join(problems)
        )
    return Cohorts(development=dev, held_out_institution=hoi)


def shared_tcia_id_groups(rows: Iterable[CrosswalkRow]) -> list[list[str]]:
    """Case-ID sets sharing a real (non-placeholder) TCIA subject ID (§6.1)."""
    by_id: dict[str, list[str]] = {}
    for r in rows:
        if r.has_real_tcia_id and r.tcia_subject_id is not None:
            by_id.setdefault(r.tcia_subject_id, []).append(r.case_id)
    return sorted(sorted(v) for v in by_id.values() if len(v) > 1)
