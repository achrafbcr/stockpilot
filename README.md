# StockPilot — Day 1 data foundation

A synthetic Moroccan wholesale-distribution dataset for a Power BI portfolio project.

## Business scenario
Atlas Distribution is a fictional wholesaler operating three warehouses. The dataset covers sales, purchasing, suppliers, customers, products and an inventory snapshot.

## Requirements
- Python 3.11+
- VS Code (recommended)
- Git

## Setup (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Generate data
Run from the project root:
```powershell
python -m src.generate_data
```

CSV files are created in `data/raw/`.

## Validate data
```powershell
python -m src.validate_data
```

## Run automated tests
```powershell
pytest -q
```

## Dataset inventory
| File | Grain | Expected rows |
|---|---|---:|
| products.csv | One row per product | 100 |
| customers.csv | One row per customer | 50 |
| suppliers.csv | One row per supplier | 20 |
| warehouses.csv | One row per warehouse | 3 |
| sales.csv | One row per sales order line | 5,000 |
| purchases.csv | One row per purchase order line | 1,000 |
| inventory.csv | One row per product, warehouse and snapshot date | 300 |

## Important modeling notes
- `sales` and `purchases` are fact-like transaction tables.
- `inventory` is a periodic snapshot fact table, not a movement ledger.
- Sales statuses include Cancelled and Returned. Exclude or separately analyze these statuses when defining recognized sales and profit KPIs.
- `unit_cost_mad` on sales is a synthetic cost snapshot for the line, not a complete accounting valuation method.
- Inventory snapshot quantities are generated independently of transaction history. Do not claim that inventory reconciles to all historical purchases and sales.
- Dates are generated over the 12 months ending 2026-11-19.
- All company and transaction data are fictional.

## Suggested GitHub description
StockPilot is a synthetic inventory and sales intelligence project demonstrating relational data generation, Python data quality validation, and Power BI-ready datasets for a wholesale distributor.
