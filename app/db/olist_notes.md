Olist is a Brazilian e-commerce marketplace. Data covers Sep 2016 to Aug 2018.
Treat 2018-08-31 as "today" (Sep-Oct 2018 have almost no orders).

How tables join:
- orders.customer_id = customers.customer_id
- order_items.order_id = orders.order_id (an order can have several items)
- order_items.product_id = products.product_id
- order_items.seller_id = sellers.seller_id
- order_payments.order_id = orders.order_id (an order can have several payments)
- order_reviews.order_id = orders.order_id
- products.product_category_name = category_translation.product_category_name

Business rules:
- Revenue = SUM(order_items.price). Freight (freight_value) is not revenue.
- Exclude orders with order_status 'canceled' or 'unavailable' from revenue and order counts.
- Use orders.order_purchase_timestamp as the order date.
- Never join order_items and order_payments in the same query: both have many rows
  per order, so the join multiplies rows and inflates totals.
- Category names are in Portuguese; join category_translation and show
  product_category_name_english.
- Count orders with COUNT(DISTINCT order_id).
- States are 2-letter codes, e.g. 'SP' = São Paulo.
