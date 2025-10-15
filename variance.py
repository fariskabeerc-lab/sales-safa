import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Config
# ================================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊 Sales & Profit Insights Dashboard")

# ================================
# Load Data
# ================================
@st.cache_data
def load_sales_data(file_path):
    df = pd.read_excel(file_path)
    df['Item Code'] = df['Item Code'].astype(str)
    return df

@st.cache_data
def load_price_list(file_path):
    df_price = pd.read_excel(file_path)
    df_price['Item Bar Code'] = df_price['Item Bar Code'].astype(str)
    return df_price

# ----------------------------
# File paths
# ----------------------------
sales_file = "july to sep safa2025.Xlsx"
price_file = "price list.xlsx"

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# Fill missing columns if not in sales
for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = 0

# Calculate GP columns in sales
sales_df['Jul-2025 GP'] = sales_df['Jul-2025 Total Profit'] / sales_df['Jul-2025 Total Sales'].replace(0,1)
sales_df['Aug-2025 GP'] = sales_df['Aug-2025 Total Profit'] / sales_df['Aug-2025 Total Sales'].replace(0,1)
sales_df['Sep-2025 GP'] = sales_df['Sep-2025 Total Profit'] / sales_df['Sep-2025 Total Sales'].replace(0,1)
sales_df['Total Sales'] = sales_df[['Jul-2025 Total Sales','Aug-2025 Total Sales','Sep-2025 Total Sales']].sum(axis=1)
sales_df['Total Profit'] = sales_df[['Jul-2025 Total Profit','Aug-2025 Total Profit','Sep-2025 Total Profit']].sum(axis=1)
sales_df['Overall GP'] = sales_df['Total Profit'] / sales_df['Total Sales'].replace(0,1)

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("Filters")
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Bar Code")

# ================================
# Filter Logic
# ================================
if item_search or barcode_search:
    # Use price list as base
    search_base = price_df.copy()

    if item_search:
        search_base = search_base[search_base['Item Name'].str.contains(item_search, case=False, na=False)]
    if barcode_search:
        search_base = search_base[search_base['Item Bar Code'].str.contains(barcode_search, case=False, na=False)]

    # Merge with sales to get sales values if available
    filtered_df = pd.merge(search_base, sales_df, left_on='Item Bar Code', right_on='Item Code', how='left')

    # Fill missing sales/profit/GP with NaN
    for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
                'Aug-2025 Total Sales','Aug-2025 Total Profit',
                'Sep-2025 Total Sales','Sep-2025 Total Profit',
                'Total Sales','Total Profit','Overall GP']:
        if col in filtered_df.columns:
            filtered_df[col] = filtered_df[col].where(filtered_df[col].notna(), None)
else:
    # Default dashboard: show only sales data
    filtered_df = sales_df.copy()

# ================================
# Key Metrics
# ================================
total_sales = filtered_df['Total Sales'].sum() if 'Total Sales' in filtered_df.columns else 0
total_profit = filtered_df['Total Profit'].sum() if 'Total Profit' in filtered_df.columns else 0
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
months = ['Jul-2025','Aug-2025','Sep-2025']
month_data = []
for month in months:
    month_sales = filtered_df[f'{month} Total Sales'].sum() if f'{month} Total Sales' in filtered_df.columns else 0
    month_profit = filtered_df[f'{month} Total Profit'].sum() if f'{month} Total Profit' in filtered_df.columns else 0
    month_data.append({'Month': month, 'Type': 'Sales', 'Value': month_sales})
    month_data.append({'Month': month, 'Type': 'Profit', 'Value': month_profit})

monthly_df = pd.DataFrame(month_data)
fig_monthly = px.bar(monthly_df, x='Month', y='Value', color='Type', barmode='group',
                     text='Value', title="Monthly Sales & Profit")
st.plotly_chart(fig_monthly, use_container_width=True)

# ================================
# Category-wise Analysis
# ================================
if 'Category' not in filtered_df.columns:
    filtered_df['Category'] = 'Unknown'

category_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
category_summary['GP'] = category_summary['Total Profit'] / category_summary['Total Sales'].replace(0,1)

fig_sales = px.bar(category_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Total Sales by Category")
st.plotly_chart(fig_sales, use_container_width=True)

fig_profit = px.bar(category_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Total Profit by Category")
st.plotly_chart(fig_profit, use_container_width=True)

fig_gp = px.bar(category_summary, x='Category', y='GP', color='GP', text=category_summary['GP'].apply(lambda x:f"{x:.2%}"), title="Gross Profit % by Category")
st.plotly_chart(fig_gp, use_container_width=True)

# ================================
# Item-wise Table
# ================================
st.markdown("### 📝 Item-wise Details")
table_cols = ['Item Bar Code','Item Name','Cost','Selling',
              'Jul-2025 Total Sales','Jul-2025 Total Profit',
              'Aug-2025 Total Sales','Aug-2025 Total Profit',
              'Sep-2025 Total Sales','Sep-2025 Total Profit',
              'Total Sales','Total Profit','Overall GP']

st.dataframe(filtered_df[table_cols].sort_values('Total Sales', ascending=False))
