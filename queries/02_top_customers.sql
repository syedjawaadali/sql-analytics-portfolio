-- Top 10 customers by lifetime value, ranked
SELECT c.id, c.name, c.country,
       ROUND(SUM(o.qty * p.price), 2) AS lifetime_value,
       RANK() OVER (ORDER BY SUM(o.qty * p.price) DESC) AS rnk
FROM customers c
JOIN orders o   ON o.customer_id = c.id
JOIN products p ON p.id = o.product_id
GROUP BY c.id, c.name, c.country
ORDER BY lifetime_value DESC
LIMIT 10;
