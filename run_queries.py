"""Execute every .sql file against the sample DB and print the results."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "shop.db"


def main() -> None:
    if not DB.exists():
        raise SystemExit("Run: python build_db.py first")
    con = sqlite3.connect(DB)
    for sql_file in sorted((ROOT / "queries").glob("*.sql")):
        print("\n" + "=" * 70)
        print(f"QUERY: {sql_file.name}")
        print("=" * 70)
        sql = sql_file.read_text()
        cur = con.execute(sql)
        cols = [c[0] for c in cur.description]
        print(" | ".join(cols))
        for row in cur.fetchmany(12):
            print(" | ".join(str(v) for v in row))
    con.close()


if __name__ == "__main__":
    main()
