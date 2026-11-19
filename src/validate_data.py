"""Reusable data quality checks for StockPilot."""
from __future__ import annotations
import pandas as pd
from src.config import RAW_DIR

FILES = ["products", "customers", "suppliers", "warehouses", "sales", "purchases", "inventory"]


def load_data():
    return {name: pd.read_csv(RAW_DIR / f"{name}.csv") for name in FILES}


def validate(d):
    errors = []

    # Primary keys
    primary_keys = {
        "products": ["product_id"],
        "customers": ["customer_id"],
        "suppliers": ["supplier_id"],
        "warehouses": ["warehouse_id"],
        "sales": ["sales_line_id"],
        "purchases": ["purchase_line_id"],
    }
    for table, cols in primary_keys.items():
        if d[table][cols].isna().any().any():
            errors.append(f"{table}: null primary key")
        if d[table].duplicated(cols).any():
            errors.append(f"{table}: duplicate primary key")

    # Foreign keys
    fk_rules = [
        ("sales", "product_id", "products", "product_id"),
        ("sales", "customer_id", "customers", "customer_id"),
        ("sales", "warehouse_id", "warehouses", "warehouse_id"),
        ("purchases", "product_id", "products", "product_id"),
        ("purchases", "supplier_id", "suppliers", "supplier_id"),
        ("purchases", "warehouse_id", "warehouses", "warehouse_id"),
        ("inventory", "product_id", "products", "product_id"),
        ("inventory", "warehouse_id", "warehouses", "warehouse_id"),
    ]
    for child, child_col, parent, parent_col in fk_rules:
        missing = set(d[child][child_col].dropna()) - set(d[parent][parent_col].dropna())
        if missing:
            errors.append(f"{child}.{child_col}: {len(missing)} orphan values")

    # Numeric/business rules
    for table, col in [("sales", "quantity"), ("purchases", "quantity_ordered"),
                       ("inventory", "quantity_on_hand")]:
        if (d[table][col] < 0).any():
            errors.append(f"{table}.{col}: negative values")

    if (d["purchases"]["quantity_received"] > d["purchases"]["quantity_ordered"]).any():
        errors.append("purchases: received quantity exceeds ordered quantity")
    if (d["inventory"]["quantity_reserved"] > d["inventory"]["quantity_on_hand"]).any():
        errors.append("inventory: reserved quantity exceeds on-hand quantity")
    if not (d["inventory"]["quantity_available"] ==
            d["inventory"]["quantity_on_hand"] - d["inventory"]["quantity_reserved"]).all():
        errors.append("inventory: available quantity does not reconcile")
    if not (d["sales"]["net_sales_mad"] <= d["sales"]["gross_sales_mad"] + 0.01).all():
        errors.append("sales: net sales exceeds gross sales")
    if not (d["sales"]["gross_profit_mad"].round(2) ==
            (d["sales"]["net_sales_mad"] - d["sales"]["cost_of_goods_mad"]).round(2)).all():
        errors.append("sales: gross profit calculation mismatch")

    # Dates
    for table, col in [("sales", "order_date"), ("purchases", "order_date")]:
        parsed = pd.to_datetime(d[table][col], errors="coerce")
        if parsed.isna().any():
            errors.append(f"{table}.{col}: invalid dates")

    if d["inventory"].duplicated(["snapshot_date", "product_id", "warehouse_id"]).any():
        errors.append("inventory: duplicate product/warehouse snapshot")

    return errors


def main():
    data = load_data()
    errors = validate(data)
    if errors:
        print("DATA VALIDATION FAILED:")
        for error in errors:
            print(f" - {error}")
        raise SystemExit(1)
    print("DATA VALIDATION PASSED: no issues found.")


if __name__ == "__main__":
    main()
