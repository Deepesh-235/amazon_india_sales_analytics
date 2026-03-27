import os
import sqlite3
import pandas as pd
import numpy as np

INPUT_FILE = "data/processed/cleaned_data.csv"
DB_FILE = "data/database/amazon_db.db"


def load_data() -> pd.DataFrame:
    print("Loading cleaned data...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print("Loaded shape:", df.shape)
    return df


def create_connection() -> sqlite3.Connection:
    os.makedirs("data/database", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    print("Preparing cleaned dataframe...")

    # Ensure required base columns exist
    required_cols = [
        "transaction_id", "order_date", "customer_id", "product_id",
        "product_name", "category", "category_catalog", "brand",
        "customer_city", "customer_state", "customer_age_group",
        "payment_method", "final_amount_inr", "original_price_inr",
        "discount_percent", "delivery_days", "is_prime_member",
        "is_prime_eligible", "is_festival_sale", "customer_rating",
        "product_rating", "return_status", "festival_name", "launch_year"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    # Safer date standardization
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_date_key"] = df["order_date"].dt.strftime("%Y-%m-%d")

    # Fallback IDs if missing
    if df["transaction_id"].isna().all():
        df["transaction_id"] = [f"T{i:07d}" for i in range(1, len(df) + 1)]
    else:
        df["transaction_id"] = df["transaction_id"].astype(str).fillna("")
        missing_mask = df["transaction_id"].str.strip() == ""
        df.loc[missing_mask, "transaction_id"] = [f"T{i:07d}" for i in range(1, missing_mask.sum() + 1)]

    if df["customer_id"].isna().all():
        df["customer_id"] = [f"C{i:07d}" for i in range(1, len(df) + 1)]
    else:
        df["customer_id"] = df["customer_id"].astype(str)

    if df["product_id"].isna().all():
        df["product_id"] = [f"P{i:07d}" for i in range(1, len(df) + 1)]
    else:
        df["product_id"] = df["product_id"].astype(str)

    # Convert booleans for SQLite
    bool_cols = ["is_prime_member", "is_prime_eligible", "is_festival_sale"]
    for col in bool_cols:
        df[col] = df[col].map({True: 1, False: 0})

    # Prefer category_catalog when available
    df["final_category"] = np.where(
        df["category_catalog"].notna() & (df["category_catalog"].astype(str).str.strip() != ""),
        df["category_catalog"],
        df["category"]
    )

    # Drop duplicate transaction IDs
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")

    return df


def create_dimension_tables(df: pd.DataFrame):
    print("Building dimension tables...")

    # Products dimension
    products = df[[
        "product_id", "product_name", "final_category", "brand",
        "is_prime_eligible", "product_rating", "launch_year"
    ]].copy()

    products = products.rename(columns={
        "final_category": "category"
    })
    products = products.drop_duplicates(subset=["product_id"], keep="first")

    # Customers dimension
    customers = df[[
        "customer_id", "customer_city", "customer_state",
        "customer_age_group", "is_prime_member"
    ]].copy()
    customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

    # Time dimension
    time_dimension = df[["order_date_key"]].dropna().drop_duplicates().copy()
    time_dimension = time_dimension.rename(columns={"order_date_key": "date_key"})
    time_dimension["date"] = pd.to_datetime(time_dimension["date_key"], errors="coerce")
    time_dimension["year"] = time_dimension["date"].dt.year
    time_dimension["month"] = time_dimension["date"].dt.month
    time_dimension["month_name"] = time_dimension["date"].dt.strftime("%b")
    time_dimension["quarter"] = time_dimension["date"].dt.quarter
    time_dimension["day"] = time_dimension["date"].dt.day
    time_dimension["day_name"] = time_dimension["date"].dt.strftime("%A")
    time_dimension = time_dimension.drop(columns=["date"])

    return products, customers, time_dimension


def create_fact_table(df: pd.DataFrame) -> pd.DataFrame:
    print("Building fact table...")

    transactions = df[[
        "transaction_id",
        "order_date_key",
        "customer_id",
        "product_id",
        "payment_method",
        "final_amount_inr",
        "original_price_inr",
        "discount_percent",
        "delivery_days",
        "is_festival_sale",
        "festival_name",
        "customer_rating",
        "return_status"
    ]].copy()

    transactions = transactions.rename(columns={
        "order_date_key": "date_key"
    })

    return transactions


def create_schema(conn: sqlite3.Connection):
    print("Creating schema...")

    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS transactions;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS time_dimension;

    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        brand TEXT,
        is_prime_eligible INTEGER,
        product_rating REAL,
        launch_year REAL
    );

    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        customer_city TEXT,
        customer_state TEXT,
        customer_age_group TEXT,
        is_prime_member INTEGER
    );

    CREATE TABLE time_dimension (
        date_key TEXT PRIMARY KEY,
        year INTEGER,
        month INTEGER,
        month_name TEXT,
        quarter INTEGER,
        day INTEGER,
        day_name TEXT
    );

    CREATE TABLE transactions (
        transaction_id TEXT PRIMARY KEY,
        date_key TEXT,
        customer_id TEXT,
        product_id TEXT,
        payment_method TEXT,
        final_amount_inr REAL,
        original_price_inr REAL,
        discount_percent REAL,
        delivery_days REAL,
        is_festival_sale INTEGER,
        festival_name TEXT,
        customer_rating REAL,
        return_status TEXT,
        FOREIGN KEY (date_key) REFERENCES time_dimension(date_key),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)
    conn.commit()


def load_tables(
    conn: sqlite3.Connection,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    time_dimension: pd.DataFrame,
    transactions: pd.DataFrame
):
    print("Loading tables into database...")

    products.to_sql("products", conn, if_exists="append", index=False)
    customers.to_sql("customers", conn, if_exists="append", index=False)
    time_dimension.to_sql("time_dimension", conn, if_exists="append", index=False)
    transactions.to_sql("transactions", conn, if_exists="append", index=False)

    conn.commit()


def create_indexes(conn: sqlite3.Connection):
    print("Creating indexes...")

    cursor = conn.cursor()
    cursor.executescript("""
    CREATE INDEX IF NOT EXISTS idx_transactions_date_key ON transactions(date_key);
    CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method);

    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
    CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);

    CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(customer_city);
    CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(customer_state);

    CREATE INDEX IF NOT EXISTS idx_time_year ON time_dimension(year);
    CREATE INDEX IF NOT EXISTS idx_time_month ON time_dimension(month);
    """)
    conn.commit()


def validate_database(conn: sqlite3.Connection):
    print("\nValidation results:")

    queries = {
        "transactions_rows": "SELECT COUNT(*) FROM transactions;",
        "products_rows": "SELECT COUNT(*) FROM products;",
        "customers_rows": "SELECT COUNT(*) FROM customers;",
        "time_dimension_rows": "SELECT COUNT(*) FROM time_dimension;",
        "total_revenue": "SELECT ROUND(SUM(final_amount_inr), 2) FROM transactions;",
        "distinct_categories": "SELECT COUNT(DISTINCT category) FROM products;",
        "date_range": """
            SELECT MIN(date_key), MAX(date_key)
            FROM time_dimension;
        """,
    }

    for name, query in queries.items():
        result = conn.execute(query).fetchone()
        print(f"{name}: {result}")


def test_join_queries(conn: sqlite3.Connection):
    print("\nTesting join queries...")

    query = """
    SELECT
        t.year,
        p.category,
        ROUND(SUM(tr.final_amount_inr), 2) AS revenue
    FROM transactions tr
    JOIN time_dimension t ON tr.date_key = t.date_key
    JOIN products p ON tr.product_id = p.product_id
    GROUP BY t.year, p.category
    ORDER BY t.year, revenue DESC
    LIMIT 10;
    """

    preview = pd.read_sql(query, conn)
    print(preview)


def main():
    df = load_data()
    df = prepare_data(df)

    products, customers, time_dimension = create_dimension_tables(df)
    transactions = create_fact_table(df)

    conn = create_connection()
    create_schema(conn)
    load_tables(conn, products, customers, time_dimension, transactions)
    create_indexes(conn)
    validate_database(conn)
    test_join_queries(conn)

    conn.close()
    print(f"\nStar schema database created successfully: {DB_FILE}")


if __name__ == "__main__":
    main()