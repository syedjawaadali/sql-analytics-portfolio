-- Customer value segmentation into quartiles (NTILE) with revenue concentration.
-- Answers "how top-heavy is our revenue?" — the Pareto question every CRM asks.
WITH ltv AS (
  SELECT c.id, SUM(o.qty * p.price) AS lifetime_value
  FROM customers c
  JOIN orders o   ON o.customer_id = c.id
  JOIN products p ON p.id = o.product_id
  GROUP BY c.id),
seg AS (
  SELECT id, lifetime_value,
         NTILE(4) OVER (ORDER BY lifetime_value DESC) AS quartile
  FROM ltv)
SELECT quartile,
       COUNT(*)                                              AS customers,
       ROUND(SUM(lifetime_value), 2)                         AS revenue,
       ROUND(100.0 * SUM(lifetime_value)
             / SUM(SUM(lifetime_value)) OVER (), 1)          AS pct_of_revenue,
       ROUND(AVG(lifetime_value), 2)                         AS avg_ltv
FROM seg
GROUP BY quartile
ORDER BY quartile;
