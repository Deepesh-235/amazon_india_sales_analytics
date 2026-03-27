import streamlit as st
from utils import run_query, get_filter_options, build_sql_filters

st.title("Product & Inventory Analytics")

options = get_filter_options()

st.sidebar.header("Product Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="prod_year")
selected_category = st.sidebar.selectbox("Category", ["All"] + options["categories"], key="prod_category")
selected_brand = st.sidebar.selectbox("Brand", ["All"] + options["brands"], key="prod_brand")
top_n = st.sidebar.slider("Top N", 5, 20, 10, key="prod_top_n")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_category=selected_category,
    selected_brand=selected_brand
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

product_perf_query = f"""
SELECT
    p.product_id,
    p.product_name,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue,
    COUNT(*) AS units_sold,
    ROUND(AVG(tr.customer_rating), 2) AS avg_customer_rating
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC
LIMIT {top_n};
"""
product_df = run_query(product_perf_query)

st.subheader(f"Top {top_n} Products")
st.dataframe(product_df, use_container_width=True)

st.markdown("---")

brand_query = f"""
SELECT
    p.brand,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND p.brand IS NOT NULL
GROUP BY p.brand
ORDER BY revenue DESC
LIMIT {top_n};
""" if where_sql else f"""
SELECT
    p.brand,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE p.brand IS NOT NULL
GROUP BY p.brand
ORDER BY revenue DESC
LIMIT {top_n};
"""
brand_df = run_query(brand_query)

b1, b2 = st.columns(2)
with b1:
    st.subheader("Top Brands by Revenue")
    if not brand_df.empty:
        st.bar_chart(brand_df.set_index("brand")[["revenue"]])

with b2:
    st.subheader("Brand Order Volume")
    if not brand_df.empty:
        st.bar_chart(brand_df.set_index("brand")[["orders_count"]])

st.markdown("---")

inventory_query = f"""
SELECT
    td.month,
    p.category,
    COUNT(*) AS demand
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.month, p.category
ORDER BY td.month;
"""
inv_df = run_query(inventory_query)

if not inv_df.empty:
    pivot_df = inv_df.pivot(index="month", columns="category", values="demand").fillna(0)
    st.subheader("Monthly Demand Pattern by Category")
    st.line_chart(pivot_df)

st.markdown("---")

rating_query = f"""
SELECT
    p.product_rating,
    COUNT(*) AS rating_count,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND p.product_rating IS NOT NULL
GROUP BY p.product_rating
ORDER BY p.product_rating;
""" if where_sql else """
SELECT
    p.product_rating,
    COUNT(*) AS rating_count,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE p.product_rating IS NOT NULL
GROUP BY p.product_rating
ORDER BY p.product_rating;
"""
rating_df = run_query(rating_query)

r1, r2 = st.columns(2)
with r1:
    st.subheader("Rating Distribution")
    if not rating_df.empty:
        st.bar_chart(rating_df.set_index("product_rating")[["rating_count"]])

with r2:
    st.subheader("Revenue vs Rating")
    if not rating_df.empty:
        st.line_chart(rating_df.set_index("product_rating")[["avg_revenue"]])

st.markdown("---")

launch_query = f"""
SELECT
    p.launch_year,
    COUNT(DISTINCT p.product_id) AS launched_products
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND p.launch_year IS NOT NULL
GROUP BY p.launch_year
ORDER BY p.launch_year;
""" if where_sql else """
SELECT
    p.launch_year,
    COUNT(DISTINCT p.product_id) AS launched_products
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE p.launch_year IS NOT NULL
GROUP BY p.launch_year
ORDER BY p.launch_year;
"""
launch_df = run_query(launch_query)

st.subheader("Product Launch Activity")
if not launch_df.empty:
    st.line_chart(launch_df.set_index("launch_year"))