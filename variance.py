import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Selection
# ================================
page = st.sidebar.radio("Select Page", ["Sales & Profit Insights", "Zero Stock Items", "Stock but No Sales"])

# ================================
# Load Data (global so all pages can use it)
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

sales_file = "july to sep safa2025.Xlsx"  
price_file = "price list(1).xlsx"          

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# Fill missing sales columns
for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = 0

# ================================
# Merge price + sales data globally
# ================================
merged_df = pd.merge(price_df, sales_df, left_on='Item Bar Code', right_on='Item Code', how='left')

# Fill missing numeric columns
for col in ['Cost','Selling','Stock',
            'Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in merged_df.columns:
        merged_df[col] = 0
    else:
        merged_df[col] = merged_df[col].fillna(0)

# Category
if 'Category' not in merged_df.columns:
    merged_df['Category'] = 'Unknown'
else:
    merged_df['Category'] = merged_df['Category'].fillna('Unknown')

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("Filters")
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Bar Code")
all_categories = merged_df['Category'].dropna().unique().tolist()
all_categories.sort()
all_categories.insert(0, "All")
selected_category = st.sidebar.selectbox("Select Category", all_categories)

# ================================
# Filter Logic
# ================================
if item_search or barcode_search:
    filtered_df = merged_df.copy()
    if item_search:
        filtered_df = filtered_df[filtered_df['Item Name'].str.contains(item_search, case=False, na=False)]
    if barcode_search:
        filtered_df = filtered_df[filtered_df['Item Bar Code'].str.contains(barcode_search, case=False, na=False)]

    if filtered_df.empty:
        st.warning("❌ Item not found. Showing all items.")
        filtered_df = merged_df.copy()
else:
    filtered_df = merged_df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# ================================
# Compute Totals GP
# ================================
def compute_totals(row):
    sales_cols = ['Jul-2025 Total Sales','Aug-2025 Total Sales','Sep-2025 Total Sales']
    profit_cols = ['Jul-2025 Total Profit','Aug-2025 Total Profit','Sep-2025 Total Profit']
    total_sales = sum([row[col] for col in sales_cols])
    total_profit = sum([row[col] for col in profit_cols])
    gp = (total_profit / total_sales) if total_sales != 0 else 0
    return pd.Series([total_sales, total_profit, gp])

filtered_df[['Total Sales','Total Profit','GP']] = filtered_df.apply(compute_totals, axis=1)

# ================================
# Product GP
# ================================
filtered_df['Product GP'] = filtered_df.apply(lambda x: (x['Selling']/x['Cost'] -1) if x['Cost'] !=0 else 0, axis=1)
filtered_df['Product GP'] = filtered_df['Product GP'].apply(lambda x: f"{x:.2%}")

# ================================
# --- Page: Sales & Profit Insights ---
# ================================
if page == "Sales & Profit Insights":
    st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
    st.title("📊 Sales & Profit Insights (Jul-Sep)")

    total_sales = filtered_df['Total Sales'].sum()
    total_profit = filtered_df['Total Profit'].sum()
    overall_gp = (total_profit/total_sales) if total_sales != 0 else 0

    st.markdown("### 🔑 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f}")
    col2.metric("Total Profit", f"{total_profit:,.0f}")
    col3.metric("GP", f"{overall_gp:.2%}")

    # Monthly Graph
    months = ['Jul-2025','Aug-2025','Sep-2025']
    month_data = []
    for month in months:
        sales_col = f"{month} Total Sales"
        profit_col = f"{month} Total Profit"
        month_sales = filtered_df[sales_col].sum()
        month_profit = filtered_df[profit_col].sum()
        month_data.append({'Month':month,'Type':'Sales','Value':month_sales})
        month_data.append({'Month':month,'Type':'Profit','Value':month_profit})
    monthly_df = pd.DataFrame(month_data)
    fig = px.bar(monthly_df, x='Month', y='Value', color='Type', barmode='group', text='Value', title="Monthly Sales & Profit")
    st.plotly_chart(fig, use_container_width=True)

    # Category-wise
    cat_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
    cat_summary['GP'] = cat_summary['Total Profit']/cat_summary['Total Sales'].replace(0,1)
    fig1 = px.bar(cat_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Sales by Category")
    fig2 = px.bar(cat_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Profit by Category")
    fig3 = px.bar(cat_summary, x='Category', y='GP', color='GP', text=cat_summary['GP'].apply(lambda x:f"{x:.2%}"), title="GP by Category")
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

    # Table
    table_cols = ['Item Bar Code','Item Name','Cost','Selling','Stock','Total Sales','Total Profit','GP','Product GP',
                  'Jul-2025 Total Sales','Jul-2025 Total Profit','Aug-2025 Total Sales','Aug-2025 Total Profit','Sep-2025 Total Sales','Sep-2025 Total Profit']
    st.dataframe(filtered_df[table_cols].sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Zero Stock Items ---
# ================================
if page == "Zero Stock Items":
    st.title("📦 Items with Zero Stock (Had Sales)")
    zero_stock_df = merged_df.copy()
    zero_stock_df = zero_stock_df[(zero_stock_df['Stock']==0) & (zero_stock_df['Total Sales']>0)]
    st.markdown(f"**Total Items:** {len(zero_stock_df)}")
    st.dataframe(zero_stock_df.sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Stock but No Sales ---
# ================================
if page == "Stock but No Sales":
    st.title("🛒 Items with Stock but No Sales")
    stock_no_sales_df = merged_df.copy()
    stock_no_sales_df = stock_no_sales_df[(stock_no_sales_df['Stock']>0) & (stock_no_sales_df['Total Sales']==0)]
    st.markdown(f"**Total Items:** {len(stock_no_sales_df)}")
    st.dataframe(stock_no_sales_df.sort_values('Stock', ascending=False))
