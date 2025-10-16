import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Selection
# ================================
page = st.sidebar.radio("Select Page", ["Sales & Profit Insights", "Zero Stock Items", "Stock but No Sales"])

# ================================
# Load Data
# ================================
@st.cache_data
def load_data(sales_file, price_file):
    # Load sales
    sales_df = pd.read_excel(sales_file)
    sales_df['Item Code'] = sales_df['Item Code'].astype(str)
    for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
                'Aug-2025 Total Sales','Aug-2025 Total Profit',
                'Sep-2025 Total Sales','Sep-2025 Total Profit']:
        if col not in sales_df.columns:
            sales_df[col] = 0
        else:
            sales_df[col] = sales_df[col].fillna(0)

    # Load price
    price_df = pd.read_excel(price_file)
    price_df['Item Bar Code'] = price_df['Item Bar Code'].astype(str)
    for col in ['Cost','Selling','Stock']:
        if col not in price_df.columns:
            price_df[col] = 0
        else:
            price_df[col] = price_df[col].fillna(0)

    # Merge
    merged_df = pd.merge(price_df, sales_df, left_on='Item Bar Code', right_on='Item Code', how='left')

    # Fill sales/profit
    for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
                'Aug-2025 Total Sales','Aug-2025 Total Profit',
                'Sep-2025 Total Sales','Sep-2025 Total Profit']:
        merged_df[col] = merged_df[col].fillna(0)

    # Category
    if 'Category' not in merged_df.columns:
        merged_df['Category'] = 'Unknown'
    else:
        merged_df['Category'] = merged_df['Category'].fillna('Unknown')

    # Precompute Totals and GP
    sales_cols = ['Jul-2025 Total Sales','Aug-2025 Total Sales','Sep-2025 Total Sales']
    profit_cols = ['Jul-2025 Total Profit','Aug-2025 Total Profit','Sep-2025 Total Profit']

    merged_df['Total Sales'] = merged_df[sales_cols].sum(axis=1)
    merged_df['Total Profit'] = merged_df[profit_cols].sum(axis=1)
    merged_df['GP'] = merged_df.apply(lambda x: (x['Total Profit']/x['Total Sales']) if x['Total Sales'] !=0 else 0, axis=1)
    merged_df['Product GP'] = merged_df.apply(lambda x: (x['Selling']/x['Cost'] -1) if x['Cost'] !=0 else 0, axis=1)

    return merged_df

# ================================
# Load all data at once
# ================================
sales_file = "july to sep safa2025.Xlsx"
price_file = "price list(1).xlsx"
df = load_data(sales_file, price_file)

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("Filters")
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Bar Code")
categories = df['Category'].dropna().unique().tolist()
categories.sort()
categories.insert(0, "All")
selected_category = st.sidebar.selectbox("Select Category", categories)

# ================================
# Filter Data Function
# ================================
def apply_filters(df):
    filtered = df.copy()
    if item_search:
        filtered = filtered[filtered['Item Name'].str.contains(item_search, case=False, na=False)]
    if barcode_search:
        filtered = filtered[filtered['Item Bar Code'].str.contains(barcode_search, case=False, na=False)]
    if selected_category != "All":
        filtered = filtered[filtered['Category']==selected_category]
    return filtered

filtered_df = apply_filters(df)

# ================================
# --- Page: Sales & Profit Insights ---
# ================================
if page == "Sales & Profit Insights":
    st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
    st.title("📊 Sales & Profit Insights (Jul-Sep)")

    # Key Metrics
    total_sales = filtered_df['Total Sales'].sum()
    total_profit = filtered_df['Total Profit'].sum()
    overall_gp = (total_profit/total_sales) if total_sales !=0 else 0

    st.markdown("### 🔑 Key Metrics")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Sales", f"{total_sales:,.0f}")
    c2.metric("Total Profit", f"{total_profit:,.0f}")
    c3.metric("GP", f"{overall_gp:.2%}")

    # Monthly Performance
    months = ['Jul-2025','Aug-2025','Sep-2025']
    month_data = []
    for month in months:
        month_data.append({'Month':month,'Type':'Sales','Value':filtered_df[f'{month} Total Sales'].sum()})
        month_data.append({'Month':month,'Type':'Profit','Value':filtered_df[f'{month} Total Profit'].sum()})
    month_df = pd.DataFrame(month_data)
    fig = px.bar(month_df, x='Month', y='Value', color='Type', barmode='group', text='Value', title="Monthly Sales & Profit")
    st.plotly_chart(fig, use_container_width=True)

    # Category Analysis
    cat_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
    cat_summary['GP'] = cat_summary.apply(lambda x: x['Total Profit']/x['Total Sales'] if x['Total Sales']!=0 else 0, axis=1)
    fig1 = px.bar(cat_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Sales by Category")
    fig2 = px.bar(cat_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Profit by Category")
    fig3 = px.bar(cat_summary, x='Category', y='GP', color='GP', text=cat_summary['GP'].apply(lambda x:f"{x:.2%}"), title="GP by Category")
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

    # Item-wise Table
    table_cols = ['Item Bar Code','Item Name','Cost','Selling','Stock','Total Sales','Total Profit','GP','Product GP',
                  'Jul-2025 Total Sales','Jul-2025 Total Profit','Aug-2025 Total Sales','Aug-2025 Total Profit','Sep-2025 Total Sales','Sep-2025 Total Profit']
    filtered_df_display = filtered_df.copy()
    filtered_df_display['GP'] = filtered_df_display['GP'].apply(lambda x: f"{x:.2%}")
    filtered_df_display['Product GP'] = filtered_df_display['Product GP'].apply(lambda x: f"{x:.2%}")
    st.dataframe(filtered_df_display[table_cols].sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Zero Stock Items ---
# ================================
if page == "Zero Stock Items":
    st.title("📦 Items with Zero Stock (Had Sales)")
    zero_df = df[(df['Stock']==0) & (df['Total Sales']>0)]
    zero_df_display = zero_df.copy()
    zero_df_display['GP'] = zero_df_display['GP'].apply(lambda x: f"{x:.2%}")
    zero_df_display['Product GP'] = zero_df_display['Product GP'].apply(lambda x: f"{x:.2%}")
    st.markdown(f"**Total Items:** {len(zero_df)}")
    st.dataframe(zero_df_display.sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Stock but No Sales ---
# ================================
if page == "Stock but No Sales":
    st.title("🛒 Items with Stock but No Sales")
    stock_df = df[(df['Stock']>0) & (df['Total Sales']==0)]
    stock_df_display = stock_df.copy()
    stock_df_display['GP'] = stock_df_display['GP'].apply(lambda x: f"{x:.2%}")
    stock_df_display['Product GP'] = stock_df_display['Product GP'].apply(lambda x: f"{x:.2%}")
    st.markdown(f"**Total Items:** {len(stock_df)}")
    st.dataframe(stock_df_display.sort_values('Stock', ascending=False))
