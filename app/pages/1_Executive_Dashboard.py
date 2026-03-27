import streamlit as st
import pandas as pd
from utils import run_query, get_filter_options, build_sql_filters

st.title("Executive Dashboard")

options = get_filter_options()

st.sidebar.header("Executive Filters")
selected_year = st.sidebar.selectbox("Year", ["All"] + options["years"], key="exec_year")
selected_state = st.sidebar.selectbox("State", ["All"] + options["states"], key="exec_state")
selected_category = st.sidebar.selectbox("Category", ["All"] + options["categories"], key="exec_category")

filter_clause = build_sql_filters(
    selected_year=selected_year,
    selected_state=selected_state,
    selected_category=selected_category
)
where_sql = f"WHERE {filter_clause}" if filter_clause else ""

kpi_query = f"""
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
kpi = run_query(kpi_query).iloc[0]

growth_query = f"""
SELECT
    td.year,
    SUM(tr.final_amount_inr) AS revenue
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.year
ORDER BY td.year;
"""
growth_df = run_query(growth_query)

growth_rate = None
if len(growth_df) > 1:
    growth_df["growth_pct"] = growth_df["revenue"].pct_change() * 100
    growth_rate = growth_df["growth_pct"].iloc[-1]

top_category_query = f"""
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
LIMIT 1;
"""
top_cat_df = run_query(top_category_query)
top_category = top_cat_df.iloc[0]["category"] if not top_cat_df.empty else "N/A"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"₹{0 if pd.isna(kpi['total_revenue']) else kpi['total_revenue']:,.0f}")
c2.metric("Growth Rate", "N/A" if growth_rate is None or pd.isna(growth_rate) else f"{growth_rate:.2f}%")
c3.metric("Active Customers", f"{0 if pd.isna(kpi['active_customers']) else int(kpi['active_customers']):,}")
c4.metric("Avg Order Value", f"₹{0 if pd.isna(kpi['avg_order_value']) else kpi['avg_order_value']:,.2f}")
c5.metric("Top Category", str(top_category).title())

st.markdown("---")
st.subheader("Current Performance Monitor")

monthly_perf_query = f"""
SELECT
    td.year,
    td.month,
    ROUND(SUM(tr.final_amount_inr), 2) AS revenue,
    COUNT(DISTINCT tr.customer_id) AS customers,
    ROUND(AVG(tr.delivery_days), 2) AS avg_delivery_days
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.year, td.month
ORDER BY td.year, td.month;
"""
monthly_df = run_query(monthly_perf_query)

if len(monthly_df) >= 2:
    latest = monthly_df.iloc[-1]
    previous = monthly_df.iloc[-2]

    latest_period = f"{int(latest['year'])}-{int(latest['month']):02d}"
    previous_period = f"{int(previous['year'])}-{int(previous['month']):02d}"

    gap = latest["revenue"] - previous["revenue"]
    growth_pct = ((latest["revenue"] - previous["revenue"]) / previous["revenue"] * 100) if previous["revenue"] != 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latest Available Month", latest_period)
    m2.metric("Latest Month Revenue", f"₹{latest['revenue']:,.0f}")
    m3.metric("Previous Month Revenue", f"₹{previous['revenue']:,.0f}")
    m4.metric("MoM Growth", f"{growth_pct:.2f}%")

    m5, m6 = st.columns(2)
    m5.metric("Customer Acquisition", f"{int(latest['customers']):,}")
    m6.metric("Avg Delivery Days", f"{0 if pd.isna(latest['avg_delivery_days']) else latest['avg_delivery_days']:.2f}")

    st.metric("Revenue Gap vs Previous Month", f"₹{gap:,.0f}")

    if growth_pct < 0:
        st.warning(f"Underperformance alert: revenue declined compared to {previous_period}.")
    else:
        st.success(f"Performance is improving compared to {previous_period}.")
elif len(monthly_df) == 1:
    latest = monthly_df.iloc[0]
    st.info("Only one month is available for the selected filters, so month-over-month comparison cannot be shown.")

st.markdown("---")

left, right = st.columns(2)

strategic_cat_query = f"""
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
strategic_geo_query = f"""
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
LIMIT 8;
"""

cat_df = run_query(strategic_cat_query)
geo_df = run_query(strategic_geo_query)

with left:
    st.subheader("Category Leadership")
    if not cat_df.empty:
        st.bar_chart(cat_df.set_index("category"))

with right:
    st.subheader("Geographic Strength")
    if not geo_df.empty:
        st.bar_chart(geo_df.set_index("customer_state"))

st.markdown("---")

gl, gr = st.columns(2)

growth_analytics_query = f"""
SELECT
    td.year,
    COUNT(*) AS orders_count,
    COUNT(DISTINCT tr.customer_id) AS active_customers,
    COUNT(DISTINCT tr.product_id) AS product_portfolio
FROM transactions tr
JOIN time_dimension td ON tr.date_key = td.date_key
JOIN customers c ON tr.customer_id = c.customer_id
JOIN products p ON tr.product_id = p.product_id
{where_sql}
GROUP BY td.year
ORDER BY td.year;
"""
ga_df = run_query(growth_analytics_query)

with gl:
    st.subheader("Customer Growth")
    if not ga_df.empty:
        st.line_chart(ga_df.set_index("year")[["active_customers"]])

with gr:
    st.subheader("Order / Portfolio Expansion")
    if not ga_df.empty:
        st.line_chart(ga_df.set_index("year")[["orders_count", "product_portfolio"]])