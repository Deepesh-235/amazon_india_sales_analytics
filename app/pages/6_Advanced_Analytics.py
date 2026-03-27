import streamlit as st
import pandas as pd
from utils import run_query, get_filter_options, build_sql_filters

st.title("Advanced Analytics")

options = get_filter_options()

st.sidebar.header("Advanced BI Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="bi_year")
selected_state = st.sidebar.selectbox("State", ["All"] + options["states"], key="bi_state")
selected_category = st.sidebar.selectbox("Category", ["All"] + options["categories"], key="bi_category")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_state=selected_state,
    selected_category=selected_category
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

forecast_query = f"""
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
forecast_df = run_query(forecast_query)

if len(forecast_df) >= 2:
    forecast_df["growth"] = forecast_df["revenue"].pct_change()
    avg_growth = forecast_df["growth"].dropna().mean()
    last_revenue = float(forecast_df["revenue"].iloc[-1])
    next_forecast = last_revenue * (1 + avg_growth if pd.notna(avg_growth) else 1)

    f1, f2 = st.columns(2)
    with f1:
        st.subheader("Historical Revenue")
        st.line_chart(forecast_df.set_index("year")[["revenue"]])
    with f2:
        st.subheader("Forecast Signal")
        st.metric("Projected Next-Year Revenue", f"₹{next_forecast:,.0f}")
        st.caption("Simple trend-based forecast used as a planning proxy.")

st.markdown("---")

market_query = f"""
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
LIMIT 8;
"""
market_df = run_query(market_query)
st.subheader("Category Market Positioning")
if not market_df.empty:
    st.bar_chart(market_df.set_index("category"))

st.markdown("---")

cross_query = f"""
SELECT
    p.category,
    COUNT(DISTINCT tr.customer_id) AS unique_customers,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_spend
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY p.category
ORDER BY unique_customers DESC
LIMIT 10;
"""
cross_df = run_query(cross_query)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Customer Reach by Category")
    if not cross_df.empty:
        st.bar_chart(cross_df.set_index("category")[["unique_customers"]])

with c2:
    st.subheader("Upsell Signal: Avg Spend by Category")
    if not cross_df.empty:
        st.bar_chart(cross_df.set_index("category")[["avg_spend"]])

st.markdown("---")

seasonal_query = f"""
SELECT
    td.month,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue,
    COUNT(*) AS orders_count
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.month
ORDER BY td.month;
"""
seasonal_df = run_query(seasonal_query)

s1, s2 = st.columns(2)
with s1:
    st.subheader("Seasonal Revenue Pattern")
    if not seasonal_df.empty:
        st.line_chart(seasonal_df.set_index("month")[["revenue"]])

with s2:
    st.subheader("Seasonal Order Pattern")
    if not seasonal_df.empty:
        st.line_chart(seasonal_df.set_index("month")[["orders_count"]])

st.markdown("---")

command_query = f"""
SELECT
    ROUND(SUM(tr.final_amount_inr), 2) AS total_revenue,
    COUNT(*) AS total_orders,
    COUNT(DISTINCT tr.customer_id) AS active_customers,
    ROUND(AVG(tr.final_amount_inr), 2) AS avg_order_value
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql};
"""
command = run_query(command_query).iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue", f"₹{0 if pd.isna(command['total_revenue']) else command['total_revenue']:,.0f}")
k2.metric("Orders", f"{0 if pd.isna(command['total_orders']) else int(command['total_orders']):,}")
k3.metric("Customers", f"{0 if pd.isna(command['active_customers']) else int(command['active_customers']):,}")
k4.metric("AOV", f"₹{0 if pd.isna(command['avg_order_value']) else command['avg_order_value']:,.2f}")