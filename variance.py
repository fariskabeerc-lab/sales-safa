import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Config
# ================================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊 Sales & Profit Insights Dashboard")

# ================================
# Load Data (Cached for Speed)
# ================================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    # Calculate GP
    df['Jul-2025 GP'] = df['Jul-2025 Total Profit'] / df['Jul-2025 Total Sales'].replace(0, 1)
    df['Aug-2025 GP'] = df['Aug-2025 Total Profit'] / df['Aug-2025 Total Sales'].replace(0, 1)
    df['Sep-2025 GP'] = df['Sep-2025 Total Profit'] / df['Sep-2025 Total Sales'].replace(0, 1)
    # Total and Overall GP
    df['Total Sales'] = df[['Jul-2025 Total Sales', 'Aug-2025 Total Sales', 'Sep-2025 Total Sales']].sum(axis=1)
    df['Total Profit'] = df[['Jul-2025 Total Profit', 'Aug-2025 Total Profit', 'Sep-2025 Total Profit']].sum(axis=1)
    df['Overall GP'] = df['Total Profit'] / df['Total Sales'].replace(0, 1)
    return df

# ----------------------------
# File path (replace this)
# ----------------------------
file_path = "july to sep safa2025.Xlsx"  # <-- Replace with your Excel file path
df = load_data(file_path)

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("Filters")

# Category filter
categories = list(df['Category'].unique())
categories.sort()
categories.insert(0, "All")
selected_category = st.sidebar.multiselect("Select Category", categories, default="All")

# Item and Barcode search
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Code")

# ================================
# Apply Filters
# ================================
filtered_df = df.copy()

if "All" not in selected_category:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_category)]

if item_search:
    filtered_df = filtered_df[filtered_df['Items'].str.contains(item_search, case=False, na=False)]

if barcode_search:
    filtered_df = filtered_df[filtered_df['Item Code'].astype(str).str.contains(barcode_search, case=False, na=False)]

# ================================
# Key Metrics
# ================================
total_sales = filtered_df['Total Sales'].sum()
total_profit = filtered_df['Total Profit'].sum()
overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

st.markdown("### 🔑 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Overall GP", f"{overall_gp:.2%}")

# ================================
# Category-wise Analysis
# ================================
st.markdown("### 📈 Category-wise Analysis")
category_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
category_summary['GP'] = category_summary['Total Profit'] / category_summary['Total Sales'].replace(0, 1)

fig_sales = px.bar(category_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Total Sales by Category")
st.plotly_chart(fig_sales, use_container_width=True)

fig_profit = px.bar(category_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Total Profit by Category")
st.plotly_chart(fig_profit, use_container_width=True)

fig_gp = px.bar(category_summary, x='Category', y='GP', color='GP', text=category_summary['GP'].apply(lambda x: f"{x:.2%}"), title="Gross Profit % by Category")
st.plotly_chart(fig_gp, use_container_width=True)

# ================================
# Monthly Performance
# ================================
st.markdown("### 📅 Monthly Performance")
monthly_summary = filtered_df[['Jul-2025 Total Sales','Jul-2025 Total Profit',
                               'Aug-2025 Total Sales','Aug-2025 Total Profit',
                               'Sep-2025 Total Sales','Sep-2025 Total Profit']].sum().reset_index()
monthly_summary.columns = ['Metric', 'Value']
monthly_summary['Month'] = monthly_summary['Metric'].apply(lambda x: x.split('-')[0])
monthly_summary['Type'] = monthly_summary['Metric'].apply(lambda x: 'Sales' if 'Sales' in x else 'Profit')
monthly_summary = monthly_summary.groupby(['Month','Type'])['Value'].sum().reset_index()

fig_monthly = px.bar(monthly_summary, x='Month', y='Value', color='Type', barmode='group', text='Value', title="Monthly Sales & Profit")
st.plotly_chart(fig_monthly, use_container_width=True)

# ================================
# Item-wise Table
# ================================
st.markdown("### 📝 Item-wise Details")
st.dataframe(filtered_df[['Item Code', 'Items', 'Category', 'Jul-2025 Total Sales', 'Jul-2025 Total Profit', 
                          'Aug-2025 Total Sales', 'Aug-2025 Total Profit', 
                          'Sep-2025 Total Sales', 'Sep-2025 Total Profit', 'Total Sales', 'Total Profit', 'Overall GP']].sort_values('Total Sales', ascending=False))
