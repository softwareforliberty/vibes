import pytest

from stock.models import Item
from stock.repository import ItemRepository
from stock.service import InsufficientStockError, StockService


def test_receive_adds_to_stock(repository: ItemRepository) -> None:
    repository.save(Item("A1", "Anvil", 2))

    updated = StockService(repository).receive("A1", 3)

    assert updated.quantity == 5
    assert repository.get("A1").quantity == 5


def test_ship_refuses_more_than_on_hand(repository: ItemRepository) -> None:
    repository.save(Item("A1", "Anvil", 2))

    with pytest.raises(InsufficientStockError):
        StockService(repository).ship("A1", 3)
    assert repository.get("A1").quantity == 2
