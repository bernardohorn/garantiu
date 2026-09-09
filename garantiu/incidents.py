import csv
from datetime import date


def _require_columns(reader: csv.DictReader, required: set[str]) -> None:
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise ValueError("CSV sem colunas obrigatórias: " + ", ".join(sorted(missing)))


def load_incidents(csv_path: str) -> dict:
    """
    Reads a CSV with columns 'module' and 'incident_count', returns
    {module: incident_count}. Rows with a missing or non-integer
    incident_count are skipped.
    """
    incidents = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        _require_columns(reader, {"module", "incident_count"})
        for row in reader:
            try:
                module = (row["module"] or "").strip()
                count = int(row["incident_count"])
                if module and count >= 0:
                    incidents[module] = count
            except (KeyError, ValueError, TypeError):
                continue
    return incidents


def load_incident_details(csv_path: str) -> dict[str, list[dict]]:
    """Read incident descriptions with YYYY-MM-DD dates, newest first."""
    by_module = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        _require_columns(reader, {"module", "description", "date"})
        for row in reader:
            module = (row["module"] or "").strip()
            description = (row["description"] or "").strip()
            incident_date = (row["date"] or "").strip()
            if not module or not description:
                raise ValueError(
                    f"CSV linha {reader.line_num}: módulo e descrição obrigatórios."
                )
            try:
                parsed_date = date.fromisoformat(incident_date)
                if parsed_date.isoformat() != incident_date:
                    raise ValueError("non-canonical date")
            except ValueError as exc:
                raise ValueError(
                    f"CSV linha {reader.line_num}: data inválida; use YYYY-MM-DD."
                ) from exc
            by_module.setdefault(module, []).append({
                "description": description,
                "date": incident_date,
            })
    for entries in by_module.values():
        entries.sort(key=lambda item: item["date"], reverse=True)
    return by_module
