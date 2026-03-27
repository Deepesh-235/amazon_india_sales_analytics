import streamlit as st
import pandas as pd
from utils import run_query, get_filter_options, build_sql_filters

st.title("Revenue Analytics")

options = get_filter_options()

st.sidebar.header("Revenue Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="rev_year")
selected_month = st.sidebar.selectbox("Month", ["All"] + options["months"], key="rev_month")
selected_state = st.sidebar.selectbox("State", ["All"] + options["states"], key="rev_state")
selected_category = st.sidebar.selectbox("Category", ["All"] + options["categories"], key="rev_category")
top_n = st.sidebar.slider("Top N", 5, 20, 10, key="rev_top_n")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_month=selected_month,
    selected_state=selected_state,
    selected_category=selected_category
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

kpi_query = f"""
SELECT
    ROUND(SUM(tr.final_amount_inr), 2) AS total_revenue,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_order_value,
    COUNT(*) AS total_transactions
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql};
"""
kpi = run_query(kpi_query).iloc[0]

m1, m2, m3 = st.columns(3)
m1.metric("Total Revenue", f"₹{0 if pd.isna(kpi['total_revenue']) else kpi['total_revenue']:,.0f}")
m2.metric("Avg Revenue / Order", f"₹{0 if pd.isna(kpi['avg_order_value']) else kpi['avg_order_value']:,.2f}")
m3.metric("Transactions", f"{0 if pd.isna(kpi['total_transactions']) else int(kpi['total_transactions']):,}")

st.markdown("---")

yearly_query = f"""
SELECT
    td.year,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.year
ORDER BY td.year;
"""
monthly_query = f"""
SELECT
    td.month,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.month
ORDER BY td.month;
"""
category_query = f"""
SELECT
    p.category,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY p.category
ORDER BY revenue DESC
LIMIT {top_n};
"""
state_query = f"""
SELECT
    c.customer_state,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY c.customer_state
ORDER BY revenue DESC
LIMIT {top_n};
"""

yearly_df = run_query(yearly_query)
monthly_df = run_query(monthly_query)
category_df = run_query(category_query)
state_df = run_query(state_query)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Revenue by Year")
    if not yearly_df.empty:
        st.line_chart(yearly_df.set_index("year"))

with c2:
    st.subheader("Revenue by Month")
    if not monthly_df.empty:
        st.bar_chart(monthly_df.set_index("month"))

st.markdown("---")

c3, c4 = st.columns(2)
with c3:
    st.subheader(f"Top {top_n} Categories")
    if not category_df.empty:
        st.bar_chart(category_df.set_index("category"))

with c4:
    st.subheader(f"Top {top_n} States")
    if not state_df.empty:
        st.bar_chart(state_df.set_index("customer_state"))

st.markdown("---")

discount_query = f"""
SELECT
    tr.discount_percent,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
AND tr.discount_percent IS NOT NULL
GROUP BY tr.discount_percent
ORDER BY tr.discount_percent
LIMIT 30;
""" if where_sql else """
SELECT
    tr.discount_percent,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
WHERE tr.discount_percent IS NOT NULL
GROUP BY tr.discount_percent
ORDER BY tr.discount_percent
LIMIT 30;
"""

discount_df = run_query(discount_query)
st.subheader("Discount vs Average Revenue")
if not discount_df.empty:
    st.line_chart(discount_df.set_index("discount_percent"))