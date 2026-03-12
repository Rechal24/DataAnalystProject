import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Nassau Candy Profitability Dashboard", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():

    file_path = "Nassau Candy Distributor.csv"

    if not os.path.exists(file_path):
        st.error("CSV file not found. Please place 'Nassau Candy Distributor.csv' in the project folder.")
        st.stop()

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        st.error("CSV file is empty. Please check the dataset.")
        st.stop()

    # Required columns check
    required_cols = [
        "Order Date","Ship Date","Division","Product Name",
        "Sales","Cost","Units","Gross Profit"
    ]

    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        st.error(f"Missing columns in dataset: {missing}")
        st.stop()

    # Convert dates
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce", dayfirst=True)
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce", dayfirst=True)

    return df


df = load_data()

st.title("🍬 Nassau Candy Distributor Profitability Dashboard")

# -----------------------------
# DATA CLEANING
# -----------------------------
df = df.dropna()

df = df[df["Sales"] > 0]
df = df[df["Units"] > 0]

df["Division"] = df["Division"].str.strip()
df["Product Name"] = df["Product Name"].str.strip()

# -----------------------------
# METRIC CALCULATIONS
# -----------------------------
df["Gross Margin %"] = (df["Gross Profit"] / df["Sales"]) * 100
df["Profit per Unit"] = df["Gross Profit"] / df["Units"]

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Select Date Range",
    [df["Order Date"].min(), df["Order Date"].max()]
)

division_filter = st.sidebar.multiselect(
    "Select Division",
    df["Division"].unique(),
    default=df["Division"].unique()
)

margin_threshold = st.sidebar.slider(
    "Minimum Margin %",
    0, 100, 10
)

product_search = st.sidebar.text_input("Search Product")

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered = df[
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Division"].isin(division_filter)) &
    (df["Gross Margin %"] >= margin_threshold)
]

if product_search:
    filtered = filtered[
        filtered["Product Name"].str.contains(product_search, case=False)
    ]

# -----------------------------
# PRODUCT PROFITABILITY
# -----------------------------
st.header("📊 Product Profitability Overview")

product_metrics = filtered.groupby("Product Name").agg({
    "Sales": "sum",
    "Gross Profit": "sum",
    "Units": "sum"
}).reset_index()

product_metrics["Gross Margin %"] = (
    product_metrics["Gross Profit"] / product_metrics["Sales"]
) * 100

product_metrics["Profit per Unit"] = (
    product_metrics["Gross Profit"] / product_metrics["Units"]
)

top_products = product_metrics.sort_values(
    by="Gross Profit", ascending=False
).head(20)

fig = px.bar(
    top_products,
    x="Product Name",
    y="Gross Profit",
    title="Top 20 Products by Profit",
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(product_metrics.sort_values(by="Gross Profit", ascending=False))

# -----------------------------
# DIVISION PERFORMANCE
# -----------------------------
st.header("🏭 Division Performance")

division_metrics = filtered.groupby("Division").agg({
    "Sales": "sum",
    "Gross Profit": "sum"
}).reset_index()

division_metrics["Avg Margin %"] = (
    division_metrics["Gross Profit"] / division_metrics["Sales"]
) * 100

fig2 = px.bar(
    division_metrics,
    x="Division",
    y=["Sales", "Gross Profit"],
    barmode="group",
    title="Revenue vs Profit by Division"
)

st.plotly_chart(fig2, use_container_width=True)

fig3 = px.box(
    filtered,
    x="Division",
    y="Gross Margin %",
    title="Margin Distribution by Division"
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# COST VS SALES DIAGNOSTICS
# -----------------------------
st.header("📉 Cost vs Margin Diagnostics")

fig4 = px.scatter(
    filtered,
    x="Cost",
    y="Sales",
    size="Gross Profit",
    color="Gross Margin %",
    hover_data=["Product Name"],
    title="Cost vs Sales Scatter"
)

st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# LOW MARGIN PRODUCTS
# -----------------------------
risk_products = filtered[filtered["Gross Margin %"] < 10]

st.subheader("⚠ Low Margin Risk Products")

st.dataframe(risk_products[[
    "Product Name",
    "Division",
    "Sales",
    "Gross Profit",
    "Gross Margin %"
]].sort_values(by="Gross Margin %"))

# -----------------------------
# PARETO ANALYSIS
# -----------------------------
st.header("📈 Profit Concentration (Pareto Analysis)")

pareto = product_metrics.sort_values(by="Gross Profit", ascending=False)

pareto["Cumulative Profit"] = pareto["Gross Profit"].cumsum()
pareto["Cumulative %"] = (
    pareto["Cumulative Profit"] /
    pareto["Gross Profit"].sum()
) * 100

fig5 = px.line(
    pareto,
    x=pareto.index,
    y="Cumulative %",
    title="Profit Pareto Curve"
)

st.plotly_chart(fig5, use_container_width=True)

# -----------------------------
# KPI SUMMARY
# -----------------------------
st.header("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"${filtered['Sales'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered['Gross Profit'].sum():,.0f}")
col3.metric("Average Margin", f"{filtered['Gross Margin %'].mean():.2f}%")