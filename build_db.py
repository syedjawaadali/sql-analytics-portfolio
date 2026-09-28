"""Build a SQLite sample database (customers, products, orders)."""
import random
import sqlite3
from pathlib import Path

random.seed(1)
DB = Path(__file__).resolve().parent / "shop.db"


def build() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, country TEXT,
                           signup_date TEXT);
    CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT,
                          price REAL);
    CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER,
                        product_id INTEGER, qty INTEGER, order_date TEXT);
    """)
    countries = ["PK", "AE", "UK", "US", "IN"]
    cats = ["Electronics", "Apparel", "Home", "Beauty"]
    cur.executemany("INSERT INTO customers VALUES(?,?,?,?)",
        [(i, f"Customer {i}", random.choice(countries),
          f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
         for i in range(1, 201)])
    cur.executemany("INSERT INTO products VALUES(?,?,?,?)",
        [(i, f"Product {i}", random.choice(cats), round(random.uniform(10, 500), 2))
         for i in range(1, 41)])
    oid = 1
    rows = []
    for _ in range(5000):
        rows.append((oid, random.randint(1, 200), random.randint(1, 40),
                     random.randint(1, 5),
                     f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"))
        oid += 1
    cur.executemany("INSERT INTO orders VALUES(?,?,?,?,?)", rows)
    con.commit(); con.close()
    print(f"Built {DB} (200 customers, 40 products, 5000 orders)")


if __name__ == "__main__":
    build()
