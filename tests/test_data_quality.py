import pandas as pd
from src.validate_data import validate


def valid_fixture():
    return {
        "products": pd.DataFrame({"product_id": ["P1"]}),
        "customers": pd.DataFrame({"customer_id": ["C1"]}),
        "suppliers": pd.DataFrame({"supplier_id": ["S1"]}),
        "warehouses": pd.DataFrame({"warehouse_id": ["W1"]}),
        "sales": pd.DataFrame({
            "sales_line_id": ["SL1"], "product_id": ["P1"], "customer_id": ["C1"],
            "warehouse_id": ["W1"], "quantity": [10], "gross_sales_mad": [100.0],
            "net_sales_mad": [95.0], "cost_of_goods_mad": [70.0],
            "gross_profit_mad": [25.0], "order_date": ["2026-01-01"],
        }),
        "purchases": pd.DataFrame({
            "purchase_line_id": ["PL1"], "product_id": ["P1"], "supplier_id": ["S1"],
            "warehouse_id": ["W1"], "quantity_ordered": [20], "quantity_received": [20],
            "order_date": ["2026-01-01"],
        }),
        "inventory": pd.DataFrame({
            "snapshot_date": ["2026-11-19"], "product_id": ["P1"], "warehouse_id": ["W1"],
            "quantity_on_hand": [50], "quantity_reserved": [5], "quantity_available": [45],
        }),
    }


def test_valid_dataset_passes():
    assert validate(valid_fixture()) == []


def test_orphan_product_foreign_key_is_detected():
    d = valid_fixture()
    d["sales"].loc[0, "product_id"] = "UNKNOWN"
    assert any("orphan" in e for e in validate(d))


def test_reserved_stock_cannot_exceed_on_hand():
    d = valid_fixture()
    d["inventory"].loc[0, "quantity_reserved"] = 60
    assert any("reserved quantity exceeds" in e for e in validate(d))


def test_gross_profit_must_reconcile():
    d = valid_fixture()
    d["sales"].loc[0, "gross_profit_mad"] = 999
    assert any("gross profit calculation mismatch" in e for e in validate(d))
