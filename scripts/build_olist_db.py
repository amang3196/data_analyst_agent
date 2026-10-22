"""Load the 9 Olist CSVs into a single DuckDB file.

Run once from the project root:
    python scripts/build_olist_db.py

Creates data/olist.duckdb with one table per CSV, using short table names.
DuckDB guesses column types (including dates) from the files.
"""

from pathlib import Path

import duckdb

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/olist.duckdb")

# table name -> CSV file name
TABLES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def build() -> None:
    """Create (or recreate) the DuckDB file and print row counts as a sanity check."""
    DB_PATH.unlink(missing_ok=True)
    con = duckdb.connect(str(DB_PATH))

    for table, file_name in TABLES.items():
        csv_path = RAW_DIR / file_name
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{csv_path}')")
        rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:<22} {rows:>10,} rows")

    con.close()
    print(f"\nSaved to {DB_PATH}")


if __name__ == "__main__":
    build()
