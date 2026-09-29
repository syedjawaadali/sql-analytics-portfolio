-- New vs returning revenue by month. ROW_NUMBER() over each customer's order
-- history flags the acquisition order (rn = 1); everything after is repeat
-- business. The split shows how much growth is new logos vs. existing base.
WITH ord AS (
  SELECT strftime('%Y-%m', o.order_date)                     AS month,
         o.qty * p.price                                     AS amount,
         ROW_NUMBER() OVER (PARTITION BY o.customer_id
                            ORDER BY o.order_date, o.id)      AS rn
  FROM orders o
  JOIN products p ON p.id = o.product_id)
SELECT month,
       ROUND(SUM(CASE WHEN rn = 1 THEN amount ELSE 0 END), 2)  AS new_customer_rev,
       ROUND(SUM(CASE WHEN rn > 1 THEN amount ELSE 0 END), 2)  AS returning_rev,
       ROUND(100.0 * SUM(CASE WHEN rn > 1 THEN amount ELSE 0 END)
             / SUM(amount), 1)                                 AS returning_pct
FROM ord
GROUP BY month
ORDER BY month;
