import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "data/database/amazon_db.db"


@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def run_query(query: str):
    conn = get_connection()
    return pd.read_sql(query, conn)


def get_filter_options():
    queries = {
        "years": """
            SELECT DISTINCT year
            FROM time_dimension
            WHERE year IS NOT NULL
            ORDER BY year
        """,
        "months": """
            SELECT DISTINCT month
            FROM time_dimension
            WHERE month IS NOT NULL
            ORDER BY month
        """,
        "states": """
            SELECT DISTINCT customer_state
            FROM customers
            WHERE customer_state IS NOT NULL
            ORDER BY customer_state
        """,
        "cities": """
            SELECT DISTINCT customer_city
            FROM customers
            WHERE customer_city IS NOT NULL
            ORDER BY customer_city
        """,
        "categories": """
            SELECT DISTINCT category
            FROM products
            WHERE category IS NOT NULL
            ORDER BY category
        """,
        "brands": """
            SELECT DISTINCT brand
            FROM products
            WHERE brand IS NOT NULL
            ORDER BY brand
        """,
        "payment_methods": """
            SELECT DISTINCT payment_method
            FROM transactions
            WHERE payment_method IS NOT NULL
            ORDER BY payment_method
        """,
        "prime_values": """
            SELECT DISTINCT is_prime_member
            FROM customers
            WHERE is_prime_member IS NOT NULL
            ORDER BY is_prime_member
        """,
        "age_groups": """
            SELECT DISTINCT customer_age_group
            FROM customers
            WHERE customer_age_group IS NOT NULL
            ORDER BY customer_age_group
        """,
        "return_statuses": """
            SELECT DISTINCT return_status
            FROM transactions
            WHERE return_status IS NOT NULL
            ORDER BY return_status
        """
    }

    options = {}
    for key, query in queries.items():
        df = run_query(query)
        if df.empty:
            options[key] = []
        else:
            options[key] = df.iloc[:, 0].tolist()

    return options


def build_sql_filters(
    selected_year=None,
    selected_month=None,
    selected_state=None,
    selected_city=None,
    selected_category=None,
    selected_brand=None,
    selected_payment_method=None,
    selected_prime=None,
    selected_age_group=None,
    selected_return_status=None,
):
    conditions = []

    if selected_year and selected_year != "All":
        conditions.append(f"td.year = {int(selected_year)}")

    if selected_month and selected_month != "All":
        conditions.append(f"td.month = {int(selected_month)}")

    if selected_state and selected_state != "All":
        conditions.append(f"c.customer_state = '{selected_state}'")

    if selected_city and selected_city != "All":
        conditions.append(f"c.customer_city = '{selected_city}'")

    if selected_category and selected_category != "All":
        conditions.append(f"p.category = '{selected_category}'")

    if selected_brand and selected_brand != "All":
        conditions.append(f"p.brand = '{selected_brand}'")

    if selected_payment_method and selected_payment_method != "All":
        conditions.append(f"tr.payment_method = '{selected_payment_method}'")

    if selected_prime != "All" and selected_prime is not None:
        conditions.append(f"c.is_prime_member = {int(selected_prime)}")

    if selected_age_group and selected_age_group != "All":
        conditions.append(f"c.customer_age_group = '{selected_age_group}'")

    if selected_return_status and selected_return_status != "All":
        conditions.append(f"tr.return_status = '{selected_return_status}'")

    return " AND ".join(conditions)