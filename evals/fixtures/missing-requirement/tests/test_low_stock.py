import csv
import sqlite3
from collections.abc import Iterator
from io import TextIOWrapper
from pathlib import Path
from typing import Literal

import pytest

from stock.models import Item
from stock.report import export_low_stock_csv
from stock.repository import ItemRepository
from stock.service import StockService


@pytest.fixture
def service(repository: ItemRepository) -> StockService:
    for item in [
        Item("B2", "Bolt", 3),
        Item("A1", "Anvil", 3),
        Item("C3", "Chain", 1),
        Item("D4", "Drill", 9),
        Item("E5", "Bolt cutter", 0),
    ]:
        repository.save(item)
    return StockService(repository)


def test_lists_items_below_threshold_fewest_first(service: StockService) -> None:
    items = service.low_stock(5)

    assert [item.sku for item in items] == ["E5", "C3", "A1", "B2"]


def test_excludes_items_at_the_threshold(service: StockService) -> None:
    assert [item.sku for item in service.low_stock(3)] == ["E5", "C3"]


def test_filters_by_name_ignoring_case(service: StockService) -> None:
    items = service.low_stock(5, name_contains="BOLT")

    assert [item.sku for item in items] == ["E5", "B2"]


def test_name_filter_ignores_case_beyond_ascii(repository: ItemRepository) -> None:
    repository.save(Item("F6", "ÉCROU", 1))
    repository.save(Item("G7", "Straße", 1))
    service = StockService(repository)

    assert [item.sku for item in service.low_stock(5, name_contains="écrou")] == ["F6"]
    assert [item.sku for item in service.low_stock(5, name_contains="STRASSE")] == [
        "G7",
    ]


def test_name_filter_treats_wildcards_as_text(repository: ItemRepository) -> None:
    repository.save(Item("F6", "50% off", 1))
    repository.save(Item("G7", "a_b", 1))
    repository.save(Item("H8", "500 off", 1))
    repository.save(Item("J9", "axb", 1))
    service = StockService(repository)

    assert [item.sku for item in service.low_stock(5, name_contains="0% ")] == ["F6"]
    assert [item.sku for item in service.low_stock(5, name_contains="a_")] == ["G7"]


def test_returns_nothing_when_no_item_is_low(service: StockService) -> None:
    assert service.low_stock(0) == []


def test_pages_start_at_one(service: StockService) -> None:
    first = service.low_stock(5, page=1, page_size=3)
    second = service.low_stock(5, page=2, page_size=3)

    assert [item.sku for item in first] == ["E5", "C3", "A1"]
    assert [item.sku for item in second] == ["B2"]


def test_reads_the_database_once(
    service: StockService,
    connection: sqlite3.Connection,
) -> None:
    statements: list[str] = []
    connection.set_trace_callback(statements.append)

    service.low_stock(5, page=1, page_size=3)

    assert len(statements) == 1


def test_pages_hold_fifty_items_by_default(repository: ItemRepository) -> None:
    for number in range(51):
        repository.save(Item(f"S{number:02}", "Screw", 1))
    service = StockService(repository)

    assert len(service.low_stock(5)) == 50
    assert [item.sku for item in service.low_stock(5, page=2)] == ["S50"]


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 10), (-1, 10), (1, 0), (1, -1)],
)
def test_rejects_pages_below_one(
    service: StockService,
    page: int,
    page_size: int,
) -> None:
    with pytest.raises(ValueError, match="must be at least 1"):
        service.low_stock(5, page=page, page_size=page_size)


def test_exports_csv_with_header(tmp_path: Path) -> None:
    path = tmp_path / "low.csv"

    export_low_stock_csv([Item("C3", "Chain", 1)], path)

    with path.open(newline="", encoding="utf-8") as file:
        assert list(csv.reader(file)) == [
            ["sku", "name", "quantity"],
            ["C3", "Chain", "1"],
        ]


def test_export_replaces_an_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "low.csv"
    path.write_text("old contents\n", encoding="utf-8")

    export_low_stock_csv([], path)

    with path.open(newline="", encoding="utf-8") as file:
        assert list(csv.reader(file)) == [["sku", "name", "quantity"]]


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_export_stops_text_running_as_a_formula(tmp_path: Path, prefix: str) -> None:
    path = tmp_path / "low.csv"

    export_low_stock_csv([Item(f"{prefix}A1", f"{prefix}Bolt", 1)], path)

    with path.open(newline="", encoding="utf-8") as file:
        assert list(csv.reader(file))[1] == [f"'{prefix}A1", f"'{prefix}Bolt", "1"]


def test_export_leaves_formula_characters_inside_text(tmp_path: Path) -> None:
    path = tmp_path / "low.csv"

    export_low_stock_csv([Item("A=1", "Bolt+Nut", 1)], path)

    with path.open(newline="", encoding="utf-8") as file:
        assert list(csv.reader(file))[1] == ["A=1", "Bolt+Nut", "1"]


def test_export_closes_the_file_when_writing_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[TextIOWrapper] = []
    real_open = Path.open

    def recording_open(
        path: Path,
        mode: Literal["w"],
        *,
        newline: str,
        encoding: str,
    ) -> TextIOWrapper:
        file = real_open(path, mode, newline=newline, encoding=encoding)
        opened.append(file)
        return file

    def failing_items() -> Iterator[Item]:
        yield Item("C3", "Chain", 1)
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", recording_open)

    with pytest.raises(OSError, match="disk full"):
        export_low_stock_csv(failing_items(), tmp_path / "low.csv")
    assert opened[0].closed
