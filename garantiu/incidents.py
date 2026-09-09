import csv


def load_incidents(csv_path: str) -> dict:
    """
    Reads a CSV with columns 'module' and 'incident_count', returns
    {module: incident_count}. Rows with a missing or non-integer
    incident_count are skipped.
    """
    incidents = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                incidents[row["module"]] = int(row["incident_count"])
            except (KeyError, ValueError):
                continue
    return incidents
