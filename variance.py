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

# Single-select Category filter
categories = list(df['Category'].unique())
categories.sort()
categories.insert(0, "All")  # Add 'All' option
selected_category = st.sidebar.selectbox("Select Category", categories)

# Item search
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Code")

# ================================
# Apply Filters
# ================================
filtered_df = df.copy()

# If item search is used, show that first (item has higher priority than category)
if item_search:
    filtered_df = filtered_df[filtered_df['Items'].str.contains(item_search, case=False, na=False)]
elif barcode_search:
    filtered_df = filtered_df[filtered_df['Item Code'].astype(str).str.contains(barcode_search, case=False, na=False)]
elif selected_category != "All":
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# ================================
# Key Metrics (No $ Sign)
# ================================
total_sales = filtered_df['Total Sales'].sum()
total_profit = filtered_df['Total Profit'].sum()
overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

st.markdown("### 🔑 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"{total_sales:,.0f}")
col2.metric("Total Profit", f"{total_profit:,.0f}")
col3.metric("Overall GP", f"{overall_gp:.2%}")

# ================================
# Monthly Performance Graph
# ================================
st.markdown("### 📅 Month-wise Performance")

# Aggregate month-wise sales & profit
months = ['Jul-2025', 'Aug-2025', 'Sep-2025']
month_data = []

for month in months:
    month_sales = filtered_df[f'{month} Total Sales'].sum()
    month_profit = filtered_df[f'{month} Total Profit'].sum()
    month_data.append({'Month': month, 'Type': 'Sales', 'Value': month_sales})
    month_data.append({'Month': month, 'Type': 'Profit', 'Value': month_profit})

monthly_df = pd.DataFrame(month_data)

fig_monthly = px.bar(monthly_df, x='Month', y='Value', color='Type', barmode='group',
                     text='Value', title="Monthly Sales & Profit")
st.plotly_chart(fig_monthly, use_container_width=True)

# ================================
# Category-wise Analysis (if no item search)
# ================================
if not item_search:
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
# Item-wise Table
# ================================
st.markdown("### 📝 Item-wise Details")
st.dataframe(filtered_df[['Item Code', 'Items', 'Category', 'Jul-2025 Total Sales', 'Jul-2025 Total Profit', 
                          'Aug-2025 Total Sales', 'Aug-2025 Total Profit', 
                          'Sep-2025 Total Sales', 'Sep-2025 Total Profit', 'Total Sales', 'Total Profit', 'Overall GP']].sort_values('Total Sales', ascending=False))
