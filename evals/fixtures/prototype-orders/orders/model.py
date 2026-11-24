"""An order and its parcels."""

from dataclasses import dataclass, field


@dataclass
class Order:
    items: list[str]
    shipped: list[str] = field(default_factory=list)
    status: str = "open"  # open, part-shipped, shipped or cancelled

    def ship(self, items: list[str]) -> None:
        self.shipped += items
        self.status = ("shipped" if set(self.shipped) == set(self.items)
                       else "part-shipped")

    def cancel(self) -> None:
        self.status = "cancelled"  # what about the parcels already sent?
