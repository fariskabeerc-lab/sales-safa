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
sales_file = "july to sep safa2025.Xlsx"  # replace with your sales file
price_file = "price list.xlsx"            # replace with your price list file

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# Fill missing sales columns if not in sales
for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = 0

# Calculate GP and totals
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

# Category filter (single-select)
all_categories = sales_df['Category'].dropna().unique().tolist()
all_categories.sort()
all_categories.insert(0, "All")  # Add 'All' option
selected_category = st.sidebar.selectbox("Select Category", all_categories)

# ================================
# Filter Logic
# ================================
if item_search or barcode_search:
    # Search in price list
    search_base = price_df.copy()
    if item_search:
        search_base = search_base[search_base['Item Name'].str.contains(item_search, case=False, na=False)]
    if barcode_search:
        search_base = search_base[search_base['Item Bar Code'].str.contains(barcode_search, case=False, na=False)]

    # Merge with sales data if available
    filtered_df = pd.merge(search_base, sales_df, left_on='Item Bar Code', right_on='Item Code', how='left')

    # Fill missing sales/profit/GP with None safely
    sales_cols = ['Jul-2025 Total Sales','Jul-2025 Total Profit',
                  'Aug-2025 Total Sales','Aug-2025 Total Profit',
                  'Sep-2025 Total Sales','Sep-2025 Total Profit',
                  'Total Sales','Total Profit','Overall GP']
    for col in sales_cols:
        if col in filtered_df.columns:
            filtered_df[col] = filtered_df[col].where(filtered_df[col].notna(), None)
        else:
            filtered_df[col] = None

    # Category column
    if 'Category' not in filtered_df.columns:
        filtered_df['Category'] = 'Unknown'
    else:
        filtered_df['Category'] = filtered_df['Category'].fillna('Unknown')

else:
    # Default: show sales data
    filtered_df = sales_df.copy()
    if 'Category' not in filtered_df.columns:
        filtered_df['Category'] = 'Unknown'
    else:
        filtered_df['Category'] = filtered_df['Category'].fillna('Unknown')

# Apply category filter if not 'All' and no item search
if selected_category != "All" and not (item_search or barcode_search):
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# Ensure sales columns exist for aggregation
for col in ['Total Sales','Total Profit']:
    if col not in filtered_df.columns:
        filtered_df[col] = 0
    else:
        filtered_df[col] = filtered_df[col].fillna(0)

# ================================
# Key Metrics
# ================================
if not (item_search or barcode_search):
    # Default sales metrics
    total_sales = filtered_df['Total Sales'].sum()
    total_profit = filtered_df['Total Profit'].sum()
    overall_gp = (total_profit / total_sales) if total_sales != 0 else 0
    st.markdown("### 🔑 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f}")
    col2.metric("Total Profit", f"{total_profit:,.0f}")
    col3.metric("Overall GP", f"{overall_gp:.2%}")
else:
    # Item search: metrics only for actual numeric sales
    total_sales = filtered_df['Total Sales'].dropna().sum()
    total_profit = filtered_df['Total Profit'].dropna().sum()
    overall_gp = (total_profit / total_sales) if total_sales != 0 else 0
    st.markdown("### 🔑 Key Metrics for Searched Items")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f}")
    col2.metric("Total Profit", f"{total_profit:,.0f}")
    col3.metric("Overall GP", f"{overall_gp:.2%}")

# ================================
# Monthly Performance Graph (only if no item search)
# ================================
if not (item_search or barcode_search):
    st.markdown("### 📅 Month-wise Performance")
    months = ['Jul-2025','Aug-2025','Sep-2025']
    month_data = []

    for month in months:
        sales_col = f'{month} Total Sales'
        profit_col = f'{month} Total Profit'
        
        month_sales = filtered_df[sales_col].sum() if sales_col in filtered_df.columns else 0
        month_profit = filtered_df[profit_col].sum() if profit_col in filtered_df.columns else 0
        
        month_data.append({'Month': month, 'Type': 'Sales', 'Value': month_sales})
        month_data.append({'Month': month, 'Type': 'Profit', 'Value': month_profit})

    monthly_df = pd.DataFrame(month_data)

    fig_monthly = px.bar(
        monthly_df, x='Month', y='Value', color='Type', barmode='group',
        text='Value', title="Monthly Sales & Profit"
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# ================================
# Category-wise Analysis (only if no item search)
# ================================
if not (item_search or barcode_search):
    category_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
    category_summary['GP'] = category_summary['Total Profit'] / category_summary['Total Sales'].replace(0,1)

    fig_sales = px.bar(category_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Total Sales by Category")
    st.plotly_chart(fig_sales, use_container_width=True)

    fig_profit = px.bar(category_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Total Profit by Category")
    st.plotly_chart(fig_profit, use_container_width=True)

    fig_gp = px.bar(category_summary, x='Category', y='GP', color='GP', text=category_summary['GP'].apply(lambda x:f"{x:.2%}"), title="Gross Profit % by Category")
    st.plotly_chart(fig_gp, use_container_width=True)

# ================================
# Item-wise Table (always show)
# ================================
st.markdown("### 📝 Item-wise Details")

table_cols = ['Item Bar Code','Item Name','Cost','Selling','Total Sales','Total Profit','Overall GP',
              'Jul-2025 Total Sales','Jul-2025 Total Profit',
              'Aug-2025 Total Sales','Aug-2025 Total Profit',
              'Sep-2025 Total Sales','Sep-2025 Total Profit']

# Ensure all columns exist
for col in table_cols:
    if col not in filtered_df.columns:
        filtered_df[col] = None

st.dataframe(filtered_df[table_cols].sort_values('Total Sales', ascending=False))
