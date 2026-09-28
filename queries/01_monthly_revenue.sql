-- Monthly revenue with month-over-month growth (window function)
WITH monthly AS (
  SELECT strftime('%Y-%m', o.order_date) AS month,
         ROUND(SUM(o.qty * p.price), 2)  AS revenue
  FROM orders o JOIN products p ON p.id = o.product_id
  GROUP BY 1)
SELECT month, revenue,
       ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS mom_change,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1)         AS mom_pct
FROM monthly ORDER BY month;
