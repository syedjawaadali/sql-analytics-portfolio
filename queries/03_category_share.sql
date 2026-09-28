-- Revenue share by category (% of grand total)
WITH cat AS (
  SELECT p.category, SUM(o.qty * p.price) AS revenue
  FROM orders o JOIN products p ON p.id = o.product_id
  GROUP BY p.category)
SELECT category,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS pct_of_total
FROM cat ORDER BY revenue DESC;
