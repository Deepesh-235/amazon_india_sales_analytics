import streamlit as st

st.set_page_config(
    page_title="Amazon India Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
    color: #f9fafb;
}
[data-testid="stSidebar"] {
    background: #0f172a;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.2rem;
}
.stMetric {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 14px;
    border-radius: 16px;
}
h1, h2, h3, p, label, div {
    color: #f9fafb;
}
</style>
""", unsafe_allow_html=True)

st.title("Amazon India Sales Analytics Dashboard")
st.caption("Six business dashboards covering 30 analytics questions")

left, right = st.columns([2, 1])

with left:
    st.markdown("""
### Dashboard Modules
- Executive Dashboard
- Revenue Analytics
- Customer Analytics
- Product & Inventory Analytics
- Operations & Logistics
- Advanced Analytics

Use the sidebar to open each page.
""")

with right:
    st.info("""
**Tech Stack**
- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SQLite
- Jupyter Notebook
- Streamlit
- GitHub
""")