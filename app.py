import streamlit as st
import pandas as pd
import plotly.express as px

# Page layout
st.set_page_config(page_title="Opportunity Insights Dashboard", layout="wide")

# Filter Columns
FILTER_COLUMNS = [
    "Account",
    "Market",
    "Description",
    "Stage",
    "Fiscal Period",
]

# Output Columns
OUTPUT_COLUMNS = [
    "Account",
    "Opportunity ID",
    "Opportunity Name",
    "Market",
    "Primary Industry",
    "Responsible Delivery Entity",
    "Description",
    "Stage",
    "Fiscal Period",
    "Total Current Revenue (converted)",
    "SI SG Revenue (converted)",
    "SC SG Revenue (converted)",
    "Con SG Revenue (converted)",
    "Primary Opportunity Lead",
    "Client Account Lead",
]


def load_file(uploaded_file):
    """Load CSV or Excel with encoding fallback."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file, encoding="utf-8")
        return pd.read_excel(uploaded_file)
    except:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1")


def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


st.title("📊 Opportunity Insights Dashboard")

# Step 1: Upload
st.header("Step 1️⃣: Upload Data")
uploaded = st.file_uploader("Upload a CSV or Excel File", type=["csv", "xlsx", "xls"])
if not uploaded:
    st.info("Please upload a file to continue.")
    st.stop()

df = load_file(uploaded)
data = df[[c for c in OUTPUT_COLUMNS if c in df.columns]].copy()

# Step 2: Filters
st.header("Step 2️⃣: Refine Filters")

if "filters_applied" not in st.session_state:
    st.session_state["filters_applied"] = False

filters = {}
for group in chunk_list(FILTER_COLUMNS, 4):
    row = st.columns(len(group))
    for col_ui, col in zip(row, group):
        if col in data.columns:
            options = sorted(data[col].dropna().unique().tolist())
            filters[col] = col_ui.multiselect(col, options, default=[])

if st.button("Apply Filters"):
    st.session_state["filters_applied"] = True

if not st.session_state["filters_applied"]:
    st.info("➡️ Modify filters and click **Apply Filters**")
    st.stop()

filtered = data.copy()
for col, selections in filters.items():
    if selections:
        filtered = filtered[filtered[col].isin(selections)]

st.subheader("📄 Filtered Data")
st.dataframe(filtered, use_container_width=True)

if filtered.empty:
    st.warning("No data after applying filters.")
    st.stop()

# Download CSV
st.download_button(
    "⬇️ Download Filtered Data",
    filtered.to_csv(index=False).encode("utf-8"),
    "filtered_data.csv",
    "text/csv"
)

# Step 3: KPI Tiles
st.header("Step 3️⃣: Summary Metrics")

total_rev_m = filtered["Total Current Revenue (converted)"].sum() / 1_000_000
total_opps = filtered["Opportunity ID"].nunique() if "Opportunity ID" in filtered.columns else len(filtered)

col1, col2 = st.columns(2)
col1.metric("💰 Total Revenue ($M)", f"{total_rev_m:,.2f}")
col2.metric("📌 # Opportunities", f"{total_opps:,}")

# Step 4: Charts
st.header("Step 4️⃣: Interactive Charts")

top_n = st.slider(
    "Top N Accounts by Revenue",
    min_value=1,
    max_value=max(5, len(filtered["Account"].unique())),
    value=min(10, len(filtered["Account"].unique())),
)

if st.button("📈 Generate Charts"):
    revenue_series = (
        filtered.groupby("Account")["Total Current Revenue (converted)"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )

    # Revenue Chart
    st.subheader("💰 Revenue by Account ($M)")
    fig1 = px.bar(
        x=revenue_series.index,
        y=revenue_series.values / 1_000_000,
        title="Revenue by Account (Descending)",
        labels={"x": "Account", "y": "Revenue ($M)"},
        text=revenue_series.values / 1_000_000,
    )
    fig1.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    # Count Chart
    st.subheader("📌 Opportunity Count by Account")
    count_series = (
        filtered.groupby("Account")["Opportunity ID"]
        .nunique()
        .reindex(revenue_series.index)
    )
    fig2 = px.bar(
        x=count_series.index,
        y=count_series.values,
        title="Opportunity Count (Sorted by Revenue)",
        labels={"x": "Account", "y": "Count"},
        text=count_series.values,
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Click **Generate Charts** above to view.")
