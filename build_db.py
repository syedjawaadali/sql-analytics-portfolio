"""Build a self-contained SQLite sample database (customers, products, orders).

The schema is a minimal star: an ``orders`` fact referencing ``customers`` and
``products`` dimensions. Generation is seeded (deterministic) and modestly
realistic — customers are acquired across the year, and every order falls on or
after its customer's signup date — so the analytical queries (monthly ramp,
new-vs-returning, cohorts) show real shape instead of noise.
"""
import datetime as dt
import random
import sqlite3
from pathlib import Path

random.seed(1)
DB = Path(__file__).resolve().parent / "shop.db"

START = dt.date(2025, 1, 1)
END = dt.date(2025, 12, 28)
SPAN = (END - START).days
COUNTRIES = ["PK", "AE", "UK", "US", "IN"]
CATEGORIES = ["Electronics", "Apparel", "Home", "Beauty"]
N_CUSTOMERS, N_PRODUCTS, N_ORDERS = 200, 40, 5000


def build() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE customers(
        id           INTEGER PRIMARY KEY,
        name         TEXT,
        country      TEXT,
        signup_date  TEXT);
    CREATE TABLE products(
        id           INTEGER PRIMARY KEY,
        name         TEXT,
        category     TEXT,
        price        REAL);
    CREATE TABLE orders(
        id           INTEGER PRIMARY KEY,
        customer_id  INTEGER REFERENCES customers(id),
        product_id   INTEGER REFERENCES products(id),
        qty          INTEGER,
        order_date   TEXT);
    """)

    # Customers acquired across the year (front-loaded so there's a base to retain)
    signup = {}
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        offset = int(random.triangular(0, SPAN, 0))  # mode at day 0 -> earlier
        sd = START + dt.timedelta(days=offset)
        signup[i] = sd
        customers.append((i, f"Customer {i}", random.choice(COUNTRIES), sd.isoformat()))
    cur.executemany("INSERT INTO customers VALUES(?,?,?,?)", customers)

    cur.executemany("INSERT INTO products VALUES(?,?,?,?)",
        [(i, f"Product {i}", random.choice(CATEGORIES), round(random.uniform(10, 500), 2))
         for i in range(1, N_PRODUCTS + 1)])

    orders = []
    for oid in range(1, N_ORDERS + 1):
        cid = random.randint(1, N_CUSTOMERS)
        max_off = (END - signup[cid]).days
        od = signup[cid] + dt.timedelta(days=random.randint(0, max_off) if max_off > 0 else 0)
        orders.append((oid, cid, random.randint(1, N_PRODUCTS),
                       random.randint(1, 5), od.isoformat()))
    cur.executemany("INSERT INTO orders VALUES(?,?,?,?,?)", orders)

    con.commit()
    con.close()
    print(f"Built {DB} "
          f"({N_CUSTOMERS} customers, {N_PRODUCTS} products, {N_ORDERS} orders)")


if __name__ == "__main__":
    build()
