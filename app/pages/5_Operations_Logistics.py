import streamlit as st
import pandas as pd
from utils import run_query, get_filter_options, build_sql_filters

st.title("Operations & Logistics")

options = get_filter_options()

st.sidebar.header("Operations Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="ops_year")
selected_state = st.sidebar.selectbox("State", ["All"] + options["states"], key="ops_state")
selected_payment_method = st.sidebar.selectbox("Payment Method", ["All"] + options["payment_methods"], key="ops_payment")
selected_return_status = st.sidebar.selectbox("Return Status", ["All"] + options["return_statuses"], key="ops_return")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_state=selected_state,
    selected_payment_method=selected_payment_method,
    selected_return_status=selected_return_status
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

delivery_kpi_query = f"""
SELECT
    ROUND(AVG(tr.delivery_days), 2) AS avg_delivery_days
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql};
"""
avg_delivery = run_query(delivery_kpi_query).iloc[0]["avg_delivery_days"]
st.metric("Average Delivery Days", f"{0 if pd.isna(avg_delivery) else avg_delivery:.2f}")

delivery_query = f"""
SELECT
    tr.delivery_days,
    COUNT(*) AS frequency
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND tr.delivery_days IS NOT NULL
GROUP BY tr.delivery_days
ORDER BY tr.delivery_days
LIMIT 30;
""" if where_sql else """
SELECT
    tr.delivery_days,
    COUNT(*) AS frequency
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE tr.delivery_days IS NOT NULL
GROUP BY tr.delivery_days
ORDER BY tr.delivery_days
LIMIT 30;
"""
delivery_df = run_query(delivery_query)

st.subheader("Delivery Time Distribution")
if not delivery_df.empty:
    st.line_chart(delivery_df.set_index("delivery_days"))

st.markdown("---")

payment_query = f"""
SELECT
    tr.payment_method,
    COUNT(*) AS orders_count,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND tr.payment_method IS NOT NULL
GROUP BY tr.payment_method
ORDER BY orders_count DESC;
""" if where_sql else """
SELECT
    tr.payment_method,
    COUNT(*) AS orders_count,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE tr.payment_method IS NOT NULL
GROUP BY tr.payment_method
ORDER BY orders_count DESC;
"""
payment_df = run_query(payment_query)

p1, p2 = st.columns(2)
with p1:
    st.subheader("Payment Method Preference")
    if not payment_df.empty:
        st.bar_chart(payment_df.set_index("payment_method")[["orders_count"]])

with p2:
    st.subheader("Revenue by Payment Method")
    if not payment_df.empty:
        st.bar_chart(payment_df.set_index("payment_method")[["revenue"]])

st.markdown("---")

return_query = f"""
SELECT
    tr.return_status,
    COUNT(*) AS return_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND tr.return_status IS NOT NULL
GROUP BY tr.return_status
ORDER BY return_count DESC;
""" if where_sql else """
SELECT
    tr.return_status,
    COUNT(*) AS return_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE tr.return_status IS NOT NULL
GROUP BY tr.return_status
ORDER BY return_count DESC;
"""
return_df = run_query(return_query)

st.subheader("Return Status Analysis")
if not return_df.empty:
    st.bar_chart(return_df.set_index("return_status"))

st.markdown("---")

regional_query = f"""
SELECT
    c.customer_state,
    ROUND(AVG(tr.delivery_days), 2) AS avg_delivery_days
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND c.customer_state IS NOT NULL
AND tr.delivery_days IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC
LIMIT 10;
""" if where_sql else """
SELECT
    c.customer_state,
    ROUND(AVG(tr.delivery_days), 2) AS avg_delivery_days
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE c.customer_state IS NOT NULL
AND tr.delivery_days IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC
LIMIT 10;
"""
regional_df = run_query(regional_query)

st.subheader("Regional Delivery Reliability")
if not regional_df.empty:
    st.bar_chart(regional_df.set_index("customer_state"))