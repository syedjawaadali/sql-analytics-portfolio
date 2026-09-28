# SQL Analytics Portfolio

A self-contained SQLite database and a set of **analytical SQL** queries
showcasing the patterns I use daily to feed dashboards: window functions,
CTEs, ranking, running totals and share-of-total.

## Queries
| File | Technique |
|------|-----------|
| `01_monthly_revenue.sql` | `LAG()` month-over-month growth |
| `02_top_customers.sql` | `RANK()` lifetime value |
| `03_category_share.sql` | `SUM() OVER ()` share of total |
| `04_running_total.sql` | windowed cumulative running total |

## Run it
```bash
python build_db.py      # creates shop.db
python run_queries.py   # runs every query and prints results
```
No third-party dependencies — pure `sqlite3` from the standard library.

---
Part of my analytics portfolio — [github.com/syedjawaadali](https://github.com/syedjawaadali)
