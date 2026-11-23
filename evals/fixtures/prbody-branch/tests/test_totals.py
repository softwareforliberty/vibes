# Covers: sales-csv R2, R4
from reports.totals import ProductTotal, product_totals


def test_sums_each_sku_and_sorts_by_sku() -> None:
    sales = [{"sku": "B", "quantity": 1, "total_pence": 250},
             {"sku": "A", "quantity": 2, "total_pence": 400},
             {"sku": "B", "quantity": 3, "total_pence": 750}]
    assert product_totals(sales) == [ProductTotal("A", 2, 400),
                                     ProductTotal("B", 4, 1000)]


def test_no_sales_gives_no_totals() -> None:
    assert product_totals([]) == []
