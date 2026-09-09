import pytest

from garantiu.incidents import load_incidents


@pytest.fixture
def sample_incidents_csv(tmp_path):
    path = tmp_path / "incidents.csv"
    path.write_text("module,incident_count\ncheckout,3\nauth,1\ncatalogo,0\n")
    return str(path)


def test_load_incidents_reads_counts(sample_incidents_csv):
    incidents = load_incidents(sample_incidents_csv)
    assert incidents == {"checkout": 3, "auth": 1, "catalogo": 0}


def test_load_incidents_skips_bad_rows(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("module,incident_count\ncheckout,tres\nauth,2\n")
    incidents = load_incidents(str(path))
    assert incidents == {"auth": 2}
