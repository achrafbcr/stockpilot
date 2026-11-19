# StockPilot data dictionary

All monetary values are in Moroccan dirhams (MAD). All entities are fictional.

## products
**Grain:** one row per product.
- `product_id`: primary key.
- `product_name`, `category`, `subcategory`: product descriptors.
- `unit_of_measure`: kg, sac or unite.
- `standard_cost_mad`, `list_price_mad`: synthetic reference prices.
- `reorder_point_units`, `target_stock_units`: inventory planning parameters.
- `is_active`: product status.

## customers
**Grain:** one row per customer.
- `customer_id`: primary key.
- `customer_name`, `city`, `customer_segment`.
- `credit_limit_mad`: synthetic credit limit.
- `is_active`: customer status.

## suppliers
**Grain:** one row per supplier.
- `supplier_id`: primary key.
- `supplier_name`, `country`.
- `lead_time_days`: expected supplier lead time.
- `payment_terms_days`: payment terms.
- `is_active`: supplier status.

## warehouses
**Grain:** one row per warehouse.
- `warehouse_id`: primary key.
- `warehouse_name`, `city`, `capacity_units`.

## sales
**Grain:** one row per sales order line.
- `sales_line_id`: primary key.
- `sales_order_id`: order identifier; multiple lines may share it.
- `order_date`, `customer_id`, `product_id`, `warehouse_id`.
- `quantity`, `unit_price_mad`, `discount_pct`, `unit_cost_mad`.
- `status`: Delivered, Invoiced, Cancelled or Returned.
- `gross_sales_mad`, `discount_mad`, `net_sales_mad`, `cost_of_goods_mad`, `gross_profit_mad`.

## purchases
**Grain:** one row per purchase order line.
- `purchase_line_id`: primary key.
- `purchase_order_id`: order identifier; multiple lines may share it.
- `order_date`, `expected_delivery_date`, `actual_delivery_date`.
- `supplier_id`, `product_id`, `warehouse_id`.
- `quantity_ordered`, `quantity_received`, `unit_cost_mad`.
- `status`: Open, Partially Received, Received Late or Received On Time.
- `ordered_value_mad`, `received_value_mad`, `delivery_delay_days`.

## inventory
**Grain:** one row per product, warehouse and snapshot date.
- `snapshot_date`, `product_id`, `warehouse_id`: composite key.
- `quantity_on_hand`, `quantity_reserved`, `quantity_available`.
- `reorder_point_units`, `target_stock_units`, `standard_cost_mad`, `stock_value_mad`.

## Relationship guidance
- products 1:* sales
- customers 1:* sales
- warehouses 1:* sales
- products 1:* purchases
- suppliers 1:* purchases
- warehouses 1:* purchases
- products 1:* inventory
- warehouses 1:* inventory

Use a separate Date dimension in Power BI and relate it to each fact table's relevant date. Avoid directly joining sales and purchases to each other.
