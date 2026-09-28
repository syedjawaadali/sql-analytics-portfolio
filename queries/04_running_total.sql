-- Daily revenue with a cumulative running total (window frame)
WITH daily AS (
  SELECT o.order_date AS d, SUM(o.qty * p.price) AS revenue
  FROM orders o JOIN products p ON p.id = o.product_id
  GROUP BY o.order_date)
SELECT d, ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY d
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_total
FROM daily ORDER BY d LIMIT 15;
