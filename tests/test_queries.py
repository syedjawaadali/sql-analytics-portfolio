"""Invariant tests for the analytical SQL against a freshly built sample DB.

Each test asserts a property the query must hold regardless of the (seeded) data:
share-of-total sums to 100, running totals are monotonic, ranks are dense and
ordered, and reported aggregates reconcile against an independent recomputation.
"""
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_db  # noqa: E402

QUERIES = ROOT / "queries"


def sql(name: str) -> str:
    return (QUERIES / name).read_text()


@pytest.fixture(scope="module")
def con():
    build_db.build()               # deterministic (seed=1)
    c = sqlite3.connect(build_db.DB)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_db_populated(con):
    assert con.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 200
    assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 40
    assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 5000


def test_orders_after_signup(con):
    """Referential + temporal integrity: every order dated on/after signup."""
    bad = con.execute("""
        SELECT COUNT(*) FROM orders o JOIN customers c ON c.id = o.customer_id
        WHERE o.order_date < c.signup_date
    """).fetchone()[0]
    assert bad == 0


def test_monthly_mom_matches_recompute(con):
    rows = con.execute(sql("01_monthly_revenue.sql")).fetchall()
    revs = [r["revenue"] for r in rows]
    assert rows[0]["mom_change"] is None            # first month has no prior
    for prev, cur in zip(rows, rows[1:]):
        assert cur["mom_change"] == pytest.approx(cur["revenue"] - prev["revenue"], abs=0.02)


def test_top_customers_rank_dense_and_ordered(con):
    rows = con.execute(sql("02_top_customers.sql")).fetchall()
    assert len(rows) == 10
    assert [r["rnk"] for r in rows] == list(range(1, 11))
    ltv = [r["lifetime_value"] for r in rows]
    assert ltv == sorted(ltv, reverse=True)


def test_category_share_sums_to_100(con):
    rows = con.execute(sql("03_category_share.sql")).fetchall()
    assert sum(r["pct_of_total"] for r in rows) == pytest.approx(100.0, abs=0.2)
    total = con.execute(
        "SELECT SUM(o.qty * p.price) FROM orders o JOIN products p ON p.id = o.product_id"
    ).fetchone()[0]
    assert sum(r["revenue"] for r in rows) == pytest.approx(total, rel=1e-4)


def test_running_total_monotonic_and_cumulative(con):
    rows = con.execute(sql("04_running_total.sql")).fetchall()
    rt = [r["running_total"] for r in rows]
    assert all(b >= a for a, b in zip(rt, rt[1:]))     # non-decreasing (revenue >= 0)
    running = 0.0
    for r in rows:
        running += r["revenue"]
        assert r["running_total"] == pytest.approx(running, abs=0.02)


def test_segments_quartiles_and_concentration(con):
    rows = con.execute(sql("05_customer_segments.sql")).fetchall()
    assert [r["quartile"] for r in rows] == [1, 2, 3, 4]
    assert sum(r["customers"] for r in rows) == 200
    assert sum(r["pct_of_revenue"] for r in rows) == pytest.approx(100.0, abs=0.2)
    # Quartile 1 (top) must out-earn quartile 4 on average.
    assert rows[0]["avg_ltv"] > rows[-1]["avg_ltv"]


def test_new_vs_returning_reconciles(con):
    nvr = con.execute(sql("06_new_vs_returning.sql")).fetchall()
    monthly = {r["month"]: r["revenue"]
               for r in con.execute(sql("01_monthly_revenue.sql")).fetchall()}
    for r in nvr:
        assert 0 <= r["returning_pct"] <= 100
        assert (r["new_customer_rev"] + r["returning_rev"]) == pytest.approx(
            monthly[r["month"]], abs=0.05)
    # Retention compounds: returning share ends higher than it starts.
    assert nvr[-1]["returning_pct"] > nvr[0]["returning_pct"]
