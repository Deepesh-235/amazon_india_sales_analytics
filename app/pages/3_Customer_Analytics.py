import streamlit as st
import pandas as pd
from utils import run_query, get_filter_options, build_sql_filters

st.title("Customer Analytics")

options = get_filter_options()

st.sidebar.header("Customer Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="cust_year")
selected_state = st.sidebar.selectbox("State", ["All"] + options["states"], key="cust_state")
selected_prime = st.sidebar.selectbox("Prime Member", ["All"] + options["prime_values"], key="cust_prime")
selected_age_group = st.sidebar.selectbox("Age Group", ["All"] + options["age_groups"], key="cust_age")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_state=selected_state,
    selected_prime=selected_prime,
    selected_age_group=selected_age_group
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

kpi_query = f"""
SELECT
    COUNT(DISTINCT tr.customer_id) AS active_customers,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_spend
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql};
"""
kpi = run_query(kpi_query).iloc[0]

c1, c2 = st.columns(2)
c1.metric("Active Customers", f"{0 if pd.isna(kpi['active_customers']) else int(kpi['active_customers']):,}")
c2.metric("Avg Spend", f"₹{0 if pd.isna(kpi['avg_spend']) else kpi['avg_spend']:,.2f}")

st.markdown("---")

rfm_proxy_query = f"""
SELECT
    tr.customer_id,
    COUNT(*) AS frequency,
    ROUND(SUM(tr.final_amount_inr), 2) AS monetary
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY tr.customer_id
ORDER BY monetary DESC
LIMIT 10;
"""
rfm_df = run_query(rfm_proxy_query)
st.subheader("Top High-Value Customers")
st.dataframe(rfm_df, use_container_width=True)

st.markdown("---")

journey_query = f"""
SELECT
    CASE
        WHEN order_count = 1 THEN 'First-time'
        WHEN order_count BETWEEN 2 AND 4 THEN 'Repeat'
        ELSE 'Loyal'
    END AS customer_stage,
    COUNT(*) AS customers
FROM (
    SELECT tr.customer_id, COUNT(*) AS order_count
    FROM transactions tr
    JOIN time_dimension td ON tr.date_key = td.date_key
    JOIN customers c ON tr.customer_id = c.customer_id
    JOIN products p ON tr.product_id = p.product_id
    {where_sql}
    GROUP BY tr.customer_id
)
GROUP BY customer_stage
ORDER BY customers DESC;
"""
journey_df = run_query(journey_query)
st.subheader("Customer Stage Distribution")
if not journey_df.empty:
    st.bar_chart(journey_df.set_index("customer_stage"))

st.markdown("---")

prime_query = f"""
SELECT
    c.is_prime_member,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_spend,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY c.is_prime_member;
"""
prime_df = run_query(prime_query)

p1, p2 = st.columns(2)
with p1:
    st.subheader("Prime vs Non-Prime Avg Spending")
    if not prime_df.empty:
        st.bar_chart(prime_df.set_index("is_prime_member")[["avg_spend"]])

with p2:
    st.subheader("Prime vs Non-Prime Orders")
    if not prime_df.empty:
        st.bar_chart(prime_df.set_index("is_prime_member")[["orders_count"]])

st.markdown("---")

age_city_left, age_city_right = st.columns(2)

age_query = f"""
SELECT
    c.customer_age_group,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND c.customer_age_group IS NOT NULL
GROUP BY c.customer_age_group
ORDER BY orders_count DESC;
""" if where_sql else """
SELECT
    c.customer_age_group,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE c.customer_age_group IS NOT NULL
GROUP BY c.customer_age_group
ORDER BY orders_count DESC;
"""

city_query = f"""
SELECT
    c.customer_city,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND c.customer_city IS NOT NULL
GROUP BY c.customer_city
ORDER BY orders_count DESC
LIMIT 10;
""" if where_sql else """
SELECT
    c.customer_city,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE c.customer_city IS NOT NULL
GROUP BY c.customer_city
ORDER BY orders_count DESC
LIMIT 10;
"""

age_df = run_query(age_query)
city_df = run_query(city_query)

with age_city_left:
    st.subheader("Age Group Preferences")
    if not age_df.empty:
        st.bar_chart(age_df.set_index("customer_age_group"))

with age_city_right:
    st.subheader("Top Customer Cities")
    if not city_df.empty:
        st.bar_chart(city_df.set_index("customer_city"))