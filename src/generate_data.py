"""Generate deterministic, relational synthetic data for StockPilot.

Run from the project root:
    python -m src.generate_data
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker

from src.config import (
    N_CUSTOMERS, N_PRODUCTS, N_PURCHASE_LINES, N_SALES_LINES,
    N_SUPPLIERS, N_WAREHOUSES, PROCESSED_DIR, RAW_DIR,
    REFERENCE_DATE, SEED,
)

fake = Faker("fr_FR")
Faker.seed(SEED)
rng = np.random.default_rng(SEED)

REFERENCE = pd.Timestamp(REFERENCE_DATE)
START_DATE = REFERENCE - pd.DateOffset(months=12)
CATEGORIES = {
    "Alimentation animale": ["Aliment volaille", "Aliment bovin", "Aliment ovin"],
    "Cereales": ["Mais", "Ble", "Orge"],
    "Premix": ["Premix vitamines", "Premix mineral", "Complement nutritionnel"],
    "Matiere premiere": ["Tourteau soja", "Son de ble", "Huile vegetale"],
}
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir", "Kenitra", "Settat"]
WAREHOUSE_DATA = [
    ("WH001", "Casablanca Central", "Casablanca", 1200),
    ("WH002", "Rabat North", "Rabat", 800),
    ("WH003", "Marrakech South", "Marrakech", 900),
]


def random_dates(n: int, start=START_DATE, end=REFERENCE) -> pd.Series:
    span = max((end - start).days, 1)
    offsets = rng.integers(0, span + 1, size=n)
    return pd.to_datetime(start) + pd.to_timedelta(offsets, unit="D")


def build_dimensions():
    warehouses = pd.DataFrame(
        WAREHOUSE_DATA, columns=["warehouse_id", "warehouse_name", "city", "capacity_units"]
    )

    supplier_names = [fake.company() for _ in range(N_SUPPLIERS)]
    suppliers = pd.DataFrame({
        "supplier_id": [f"SUP{i:03d}" for i in range(1, N_SUPPLIERS + 1)],
        "supplier_name": supplier_names,
        "country": rng.choice(["Morocco", "Spain", "France", "Turkey"], N_SUPPLIERS,
                              p=[0.65, 0.15, 0.10, 0.10]),
        "lead_time_days": rng.integers(3, 22, N_SUPPLIERS),
        "payment_terms_days": rng.choice([30, 45, 60, 90], N_SUPPLIERS),
        "is_active": rng.choice([True, False], N_SUPPLIERS, p=[0.9, 0.1]),
    })

    customer_names = [fake.company() for _ in range(N_CUSTOMERS)]
    customers = pd.DataFrame({
        "customer_id": [f"CUS{i:04d}" for i in range(1, N_CUSTOMERS + 1)],
        "customer_name": customer_names,
        "city": rng.choice(CITIES, N_CUSTOMERS),
        "customer_segment": rng.choice(["Retailer", "Wholesaler", "Farm", "Industrial"],
                                       N_CUSTOMERS, p=[0.25, 0.35, 0.25, 0.15]),
        "credit_limit_mad": rng.choice([10000, 25000, 50000, 100000, 200000], N_CUSTOMERS),
        "is_active": rng.choice([True, False], N_CUSTOMERS, p=[0.94, 0.06]),
    })

    product_rows = []
    product_id = 1
    for category, names in CATEGORIES.items():
        for i in range(N_PRODUCTS // len(CATEGORIES)):
            subcategory = names[i % len(names)]
            cost = round(float(rng.uniform(8, 180)), 2)
            margin = float(rng.uniform(0.12, 0.38))
            product_rows.append({
                "product_id": f"PRD{product_id:04d}",
                "product_name": f"{subcategory} {i+1:02d}",
                "category": category,
                "subcategory": subcategory,
                "unit_of_measure": rng.choice(["kg", "sac", "unite"], p=[0.65, 0.25, 0.10]),
                "standard_cost_mad": cost,
                "list_price_mad": round(cost * (1 + margin), 2),
                "reorder_point_units": int(rng.integers(100, 700)),
                "target_stock_units": int(rng.integers(700, 2500)),
                "is_active": rng.choice([True, False], p=[0.96, 0.04]),
            })
            product_id += 1

    products = pd.DataFrame(product_rows)
    return products, customers, suppliers, warehouses


def build_sales(products, customers, warehouses):
    n = N_SALES_LINES
    dates = random_dates(n)
    product_idx = rng.integers(0, len(products), n)
    customer_idx = rng.integers(0, len(customers), n)
    warehouse_idx = rng.integers(0, len(warehouses), n)

    selected_products = products.iloc[product_idx].reset_index(drop=True)
    qty = rng.integers(5, 251, n)
    unit_price = selected_products["list_price_mad"].to_numpy()
    discount = rng.choice([0, 0.02, 0.05, 0.08, 0.10], n,
                          p=[0.45, 0.15, 0.20, 0.15, 0.05])
    unit_cost = selected_products["standard_cost_mad"].to_numpy()
    status = rng.choice(["Delivered", "Invoiced", "Cancelled", "Returned"],
                        n, p=[0.65, 0.25, 0.07, 0.03])

    sales = pd.DataFrame({
        "sales_line_id": [f"SL{i:06d}" for i in range(1, n + 1)],
        "sales_order_id": [f"SO{int(x):06d}" for x in rng.integers(1, int(n * 0.72), n)],
        "order_date": dates,
        "customer_id": customers.iloc[customer_idx]["customer_id"].to_numpy(),
        "product_id": selected_products["product_id"].to_numpy(),
        "warehouse_id": warehouses.iloc[warehouse_idx]["warehouse_id"].to_numpy(),
        "quantity": qty,
        "unit_price_mad": np.round(unit_price, 2),
        "discount_pct": discount,
        "unit_cost_mad": np.round(unit_cost, 2),
        "status": status,
    })
    sales["gross_sales_mad"] = (sales["quantity"] * sales["unit_price_mad"]).round(2)
    sales["discount_mad"] = (sales["gross_sales_mad"] * sales["discount_pct"]).round(2)
    sales["net_sales_mad"] = (sales["gross_sales_mad"] - sales["discount_mad"]).round(2)
    sales["cost_of_goods_mad"] = (sales["quantity"] * sales["unit_cost_mad"]).round(2)
    sales["gross_profit_mad"] = (sales["net_sales_mad"] - sales["cost_of_goods_mad"]).round(2)
    return sales.sort_values("order_date").reset_index(drop=True)


def build_purchases(products, suppliers, warehouses):
    n = N_PURCHASE_LINES
    order_dates = random_dates(n)
    product_idx = rng.integers(0, len(products), n)
    supplier_idx = rng.integers(0, len(suppliers), n)
    warehouse_idx = rng.integers(0, len(warehouses), n)
    selected_products = products.iloc[product_idx].reset_index(drop=True)
    selected_suppliers = suppliers.iloc[supplier_idx].reset_index(drop=True)

    ordered_qty = rng.integers(100, 1501, n)
    unit_cost = selected_products["standard_cost_mad"].to_numpy() * rng.uniform(0.88, 1.12, n)
    lead = selected_suppliers["lead_time_days"].to_numpy()
    expected = order_dates + pd.to_timedelta(lead, unit="D")
    lateness = rng.choice([-3, -1, 0, 1, 2, 5, 8, 12], n,
                          p=[0.08, 0.10, 0.25, 0.15, 0.15, 0.12, 0.10, 0.05])
    actual = expected + pd.to_timedelta(lateness, unit="D")
    # Orders near the reference date may still be open / partially received.
    open_mask = actual > REFERENCE
    received_qty = ordered_qty.copy()
    received_qty[open_mask] = rng.integers(0, 2, open_mask.sum()) * (
        ordered_qty[open_mask] // 2
    )
    status = np.where(received_qty == 0, "Open",
             np.where(received_qty < ordered_qty, "Partially Received",
             np.where(lateness > 0, "Received Late", "Received On Time")))

    purchases = pd.DataFrame({
        "purchase_line_id": [f"PL{i:05d}" for i in range(1, n + 1)],
        "purchase_order_id": [f"PO{int(x):05d}" for x in rng.integers(1, int(n * 0.75), n)],
        "order_date": order_dates,
        "expected_delivery_date": expected,
        "actual_delivery_date": pd.Series(actual).where(received_qty > 0, pd.NaT),
        "supplier_id": selected_suppliers["supplier_id"].to_numpy(),
        "product_id": selected_products["product_id"].to_numpy(),
        "warehouse_id": warehouses.iloc[warehouse_idx]["warehouse_id"].to_numpy(),
        "quantity_ordered": ordered_qty,
        "quantity_received": received_qty,
        "unit_cost_mad": np.round(unit_cost, 2),
        "status": status,
    })
    purchases["ordered_value_mad"] = (purchases["quantity_ordered"] * purchases["unit_cost_mad"]).round(2)
    purchases["received_value_mad"] = (purchases["quantity_received"] * purchases["unit_cost_mad"]).round(2)
    purchases["delivery_delay_days"] = (
        pd.to_datetime(purchases["actual_delivery_date"]) -
        pd.to_datetime(purchases["expected_delivery_date"])
    ).dt.days
    return purchases.sort_values("order_date").reset_index(drop=True)


def build_inventory(products, warehouses):
    rows = []
    for _, p in products.iterrows():
        for _, w in warehouses.iterrows():
            target = int(p["target_stock_units"])
            reorder = int(p["reorder_point_units"])
            # Most product/warehouse combinations are healthy; a meaningful minority are low.
            if rng.random() < 0.18:
                on_hand = int(rng.integers(0, max(reorder, 1)))
            else:
                on_hand = int(rng.integers(max(reorder, 1), max(target, reorder + 1)))
            reserved = int(rng.integers(0, min(on_hand, 80) + 1))
            available = on_hand - reserved
            rows.append({
                "snapshot_date": REFERENCE,
                "product_id": p["product_id"],
                "warehouse_id": w["warehouse_id"],
                "quantity_on_hand": on_hand,
                "quantity_reserved": reserved,
                "quantity_available": available,
                "reorder_point_units": reorder,
                "target_stock_units": target,
                "standard_cost_mad": p["standard_cost_mad"],
                "stock_value_mad": round(on_hand * p["standard_cost_mad"], 2),
            })
    return pd.DataFrame(rows)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    products, customers, suppliers, warehouses = build_dimensions()
    sales = build_sales(products, customers, warehouses)
    purchases = build_purchases(products, suppliers, warehouses)
    inventory = build_inventory(products, warehouses)

    datasets = {
        "products": products,
        "customers": customers,
        "suppliers": suppliers,
        "warehouses": warehouses,
        "sales": sales,
        "purchases": purchases,
        "inventory": inventory,
    }

    for name, df in datasets.items():
        df.to_csv(RAW_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")

    print("StockPilot synthetic data generated.")
    for name, df in datasets.items():
        print(f"{name:12s}: {len(df):>6,} rows | {len(df.columns):>2} columns")
    print(f"Output: {RAW_DIR}")


if __name__ == "__main__":
    main()
