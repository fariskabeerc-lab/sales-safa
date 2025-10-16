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

sales_file = "july to sep safa2025.Xlsx"  # replace with your file
price_file = "price list(1).xlsx"          # replace with your file

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# Fill missing sales columns if not in sales
for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = 0

# ================================
# Sidebar Filters (global)
# ================================
st.sidebar.header("Filters")
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Bar Code")

all_categories = sales_df['Category'].dropna().unique().tolist()
all_categories.sort()
all_categories.insert(0, "All")
selected_category = st.sidebar.selectbox("Select Category", all_categories)

# ================================
# Filter Logic (global)
# ================================
if item_search or barcode_search:
    search_base = price_df.copy()
    if item_search:
        search_base = search_base[search_base['Item Name'].str.contains(item_search, case=False, na=False)]
    if barcode_search:
        search_base = search_base[search_base['Item Bar Code'].str.contains(barcode_search, case=False, na=False)]

    filtered_df = pd.merge(search_base, sales_df, left_on='Item Bar Code', right_on='Item Code', how='left')

    sales_cols = ['Jul-2025 Total Sales','Jul-2025 Total Profit',
                  'Aug-2025 Total Sales','Aug-2025 Total Profit',
                  'Sep-2025 Total Sales','Sep-2025 Total Profit']
    for col in sales_cols:
        if col not in filtered_df.columns:
            filtered_df[col] = 0
        else:
            filtered_df[col] = filtered_df[col].fillna(0)

    if 'Category' not in filtered_df.columns:
        filtered_df['Category'] = 'Unknown'
    else:
        filtered_df['Category'] = filtered_df['Category'].fillna('Unknown')

    if filtered_df.empty:
        st.warning("❌ Item not found in the data. Showing all items instead.")
        filtered_df = sales_df.copy()
        if 'Category' not in filtered_df.columns:
            filtered_df['Category'] = 'Unknown'
        else:
            filtered_df['Category'] = filtered_df['Category'].fillna('Unknown')

else:
    filtered_df = sales_df.copy()
    if 'Category' not in filtered_df.columns:
        filtered_df['Category'] = 'Unknown'
    else:
        filtered_df['Category'] = filtered_df['Category'].fillna('Unknown')

if selected_category != "All" and not (item_search or barcode_search):
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# ================================
# Ensure required columns exist
# ================================
for col in ['Stock', 'Total Sales', 'Cost', 'Selling']:
    if col not in filtered_df.columns:
        filtered_df[col] = 0

# ================================
# Compute Totals for main page
# ================================
def compute_row_totals(row):
    sales_cols = ['Jul-2025 Total Sales','Aug-2025 Total Sales','Sep-2025 Total Sales']
    profit_cols = ['Jul-2025 Total Profit','Aug-2025 Total Profit','Sep-2025 Total Profit']

    total_sales = sum([row[col] if pd.notna(row[col]) else 0 for col in sales_cols])
    total_profit = sum([row[col] if pd.notna(row[col]) else 0 for col in profit_cols])
    gp = (total_profit / total_sales) if total_sales != 0 else 0
    return pd.Series([total_sales, total_profit, gp])

filtered_df[['Total Sales','Total Profit','GP']] = filtered_df.apply(compute_row_totals, axis=1)

# ================================
# Add Product GP = Selling / Cost
# ================================
filtered_df['Product GP'] = filtered_df.apply(lambda x: (x['Selling'] / x['Cost'] - 1) if x['Cost'] != 0 else 0, axis=1)
filtered_df['Product GP'] = filtered_df['Product GP'].apply(lambda x: f"{x:.2%}")

# ================================
# --- Page: Sales & Profit Insights ---
# ================================
if page == "Sales & Profit Insights":
    st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
    st.title("📊 Sales & Profit Insights (Jul-Sep)")

    total_sales = filtered_df['Total Sales'].sum()
    total_profit = filtered_df['Total Profit'].sum()
    overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

    st.markdown("### 🔑 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f}")
    col2.metric("Total Profit", f"{total_profit:,.0f}")
    col3.metric("GP", f"{overall_gp:.2%}")

    # Monthly Performance
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
    fig_monthly = px.bar(monthly_df, x='Month', y='Value', color='Type', barmode='group', text='Value', title="Monthly Sales & Profit")
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Category-wise Analysis
    category_summary = filtered_df.groupby('Category').agg({'Total Sales':'sum','Total Profit':'sum'}).reset_index()
    category_summary['GP'] = category_summary['Total Profit'] / category_summary['Total Sales'].replace(0,1)
    fig_sales = px.bar(category_summary, x='Category', y='Total Sales', color='Total Sales', text='Total Sales', title="Total Sales by Category")
    fig_profit = px.bar(category_summary, x='Category', y='Total Profit', color='Total Profit', text='Total Profit', title="Total Profit by Category")
    fig_gp = px.bar(category_summary, x='Category', y='GP', color='GP', text=category_summary['GP'].apply(lambda x:f"{x:.2%}"), title="Gross Profit % by Category")
    st.plotly_chart(fig_sales, use_container_width=True)
    st.plotly_chart(fig_profit, use_container_width=True)
    st.plotly_chart(fig_gp, use_container_width=True)

    # Item-wise Table
    st.markdown("### 📝 Item-wise Details")
    table_cols = ['Item Bar Code','Item Name','Cost','Selling','Stock','Total Sales','Total Profit','GP','Product GP',
                  'Jul-2025 Total Sales','Jul-2025 Total Profit','Aug-2025 Total Sales','Aug-2025 Total Profit','Sep-2025 Total Sales','Sep-2025 Total Profit']
    st.dataframe(filtered_df[table_cols].sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Zero Stock Items ---
# ================================
if page == "Zero Stock Items":
    st.title("📦 Items with Zero Stock (Had Sales)")

    zero_stock_df = sales_df.copy()
    for col in ['Stock', 'Total Sales', 'Cost', 'Selling']:
        if col not in zero_stock_df.columns:
            zero_stock_df[col] = 0

    # Product GP = Selling / Cost
    zero_stock_df['Product GP'] = zero_stock_df.apply(lambda x: (x['Selling'] / x['Cost'] - 1) if x['Cost'] != 0 else 0, axis=1)
    zero_stock_df['Product GP'] = zero_stock_df['Product GP'].apply(lambda x: f"{x:.2%}")

    zero_stock_df = zero_stock_df[(zero_stock_df['Stock'] == 0) & (zero_stock_df['Total Sales'] > 0)]
    st.markdown(f"**Total Items:** {len(zero_stock_df)}")
    st.dataframe(zero_stock_df.sort_values('Total Sales', ascending=False))

# ================================
# --- Page: Stock but No Sales ---
# ================================
if page == "Stock but No Sales":
    st.title("🛒 Items with Stock but No Sales")

    stock_no_sales_df = sales_df.copy()
    for col in ['Stock', 'Total Sales', 'Cost', 'Selling']:
        if col not in stock_no_sales_df.columns:
            stock_no_sales_df[col] = 0

    # Product GP = Selling / Cost
    stock_no_sales_df['Product GP'] = stock_no_sales_df.apply(lambda x: (x['Selling'] / x['Cost'] - 1) if x['Cost'] != 0 else 0, axis=1)
    stock_no_sales_df['Product GP'] = stock_no_sales_df['Product GP'].apply(lambda x: f"{x:.2%}")

    stock_no_sales_df = stock_no_sales_df[(stock_no_sales_df['Stock'] > 0) & (stock_no_sales_df['Total Sales'] == 0)]
    st.markdown(f"**Total Items:** {len(stock_no_sales_df)}")
    st.dataframe(stock_no_sales_df.sort_values('Stock', ascending=False))
