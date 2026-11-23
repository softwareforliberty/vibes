# Covers: sales-csv R1, R3, R5
from reports import cli


def test_rejects_a_malformed_day(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["csv", "24-11-2026"]) == 2
    assert "YYYY-MM-DD" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_writes_the_days_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "daily_sales", lambda url, day: {"sales": [
        {"sku": "A", "quantity": 2, "total_pence": 400}]})
    assert cli.main(["csv", "2026-11-24"]) == 0
    assert (tmp_path / "sales-2026-11-24.csv").read_bytes() == (
        b"sku,quantity,total_pence\r\nA,2,400\r\n")
