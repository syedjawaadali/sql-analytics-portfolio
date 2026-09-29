"""Render the query results as a one-page dashboard and draw the schema (ERD).

Kept separate from ``run_queries.py`` so the queries themselves stay
dependency-free; this module adds pandas + matplotlib only for the visuals.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import sqlite3
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
DB = ROOT / "shop.db"
OUT = ROOT / "outputs"

# ---- House style -----------------------------------------------------------
INK = "#0f172a"
GRID = "#e2e8f0"
ACCENT = "#1E90FF"
ACCENT_2 = "#00C2A8"
PALETTE = ["#1E90FF", "#00C2A8", "#F5A524", "#7C5CFF", "#F2647C"]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": GRID,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
})

_MONEY = FuncFormatter(lambda x, _: f"${x/1e6:.2f}M" if abs(x) >= 1e6 else f"${x/1e3:.0f}K")


def _q(con, name):
    return pd.read_sql_query((ROOT / "queries" / name).read_text(), con)


def dashboard(con) -> None:
    OUT.mkdir(exist_ok=True)
    monthly = _q(con, "01_monthly_revenue.sql")
    top = _q(con, "02_top_customers.sql")
    cats = _q(con, "03_category_share.sql")
    nvr = _q(con, "06_new_vs_returning.sql")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("SQL Analytics — Executive Dashboard", fontsize=16,
                 fontweight="bold", color=INK, x=0.5, y=0.98)

    # 1) Monthly revenue trend
    ax = axes[0, 0]
    ax.plot(range(len(monthly)), monthly["revenue"], marker="o", color=ACCENT, lw=2.2)
    ax.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.12, color=ACCENT)
    ax.set_title("Monthly Revenue Trend")
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly["month"], rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(_MONEY)

    # 2) Category share
    ax = axes[0, 1]
    ax.barh(cats["category"][::-1], cats["revenue"][::-1], color=PALETTE)
    for y, (rev, pct) in enumerate(zip(cats["revenue"][::-1], cats["pct_of_total"][::-1])):
        ax.text(rev, y, f" {pct:.0f}%", va="center", fontsize=9, color=INK)
    ax.set_title("Revenue by Category")
    ax.xaxis.set_major_formatter(_MONEY)
    ax.margins(x=0.12)

    # 3) Top 10 customers by lifetime value
    ax = axes[1, 0]
    ax.barh(top["name"][::-1], top["lifetime_value"][::-1], color=ACCENT_2)
    ax.set_title("Top 10 Customers by Lifetime Value")
    ax.xaxis.set_major_formatter(_MONEY)
    ax.tick_params(axis="y", labelsize=8)

    # 4) New vs returning revenue (stacked)
    ax = axes[1, 1]
    x = range(len(nvr))
    ax.bar(x, nvr["new_customer_rev"], color=PALETTE[2], label="New")
    ax.bar(x, nvr["returning_rev"], bottom=nvr["new_customer_rev"],
           color=PALETTE[3], label="Returning")
    ax.set_title("New vs Returning Revenue")
    ax.set_xticks(list(x))
    ax.set_xticklabels(nvr["month"], rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(_MONEY)
    ax.legend(fontsize=8, frameon=False)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT / "dashboard.png", dpi=130)
    plt.close(fig)


def erd(con) -> None:
    """Draw the star schema as a simple, legible ERD."""
    OUT.mkdir(exist_ok=True)
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("customers", "products", "orders")}
    tables = {
        "customers": (0.06, 0.55, ["id (PK)", "name", "country", "signup_date"]),
        "products": (0.06, 0.08, ["id (PK)", "name", "category", "price"]),
        "orders": (0.60, 0.30, ["id (PK)", "customer_id (FK)", "product_id (FK)",
                                "qty", "order_date"]),
    }
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.suptitle("Sample Schema (star) — orders fact + customers / products dims",
                 fontsize=14, fontweight="bold", color=INK, y=0.96)

    boxes = {}
    for name, (x, y, fields) in tables.items():
        h = 0.09 + 0.052 * len(fields)
        w = 0.32
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                             linewidth=1.6, edgecolor=ACCENT, facecolor="#f8fafc")
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.035, f"{name}  ({counts[name]:,} rows)",
                ha="center", va="center", fontweight="bold", color=INK, fontsize=11)
        ax.plot([x + 0.01, x + w - 0.01], [y + h - 0.06, y + h - 0.06],
                color=GRID, lw=1)
        for i, fld in enumerate(fields):
            weight = "bold" if "PK" in fld or "FK" in fld else "normal"
            ax.text(x + 0.02, y + h - 0.09 - 0.05 * i, fld, ha="left", va="center",
                    fontsize=9, color=INK, fontweight=weight)
        boxes[name] = (x, y, w, h)

    # FK arrows: orders -> customers, orders -> products
    ox, oy, ow, oh = boxes["orders"]
    for target in ("customers", "products"):
        tx, ty, tw, th = boxes[target]
        arrow = FancyArrowPatch((ox, oy + oh / 2), (tx + tw, ty + th / 2),
                                arrowstyle="-|>", mutation_scale=14,
                                color=ACCENT_2, lw=1.6,
                                connectionstyle="arc3,rad=0.12")
        ax.add_patch(arrow)
    ax.text(0.5, 0.02, "FK: orders.customer_id → customers.id   ·   "
            "orders.product_id → products.id",
            ha="center", fontsize=9, color=INK)

    fig.savefig(OUT / "schema.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    if not DB.exists():
        raise SystemExit("Run: python build_db.py first")
    con = sqlite3.connect(DB)
    dashboard(con)
    erd(con)
    con.close()
    print(f"dashboard.png + schema.png -> {OUT}/")


if __name__ == "__main__":
    main()
