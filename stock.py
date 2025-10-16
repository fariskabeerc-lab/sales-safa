import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Config
# ================================
st.set_page_config(page_title="Profit Range Dashboard", layout="wide")
st.title("📊 Items from Price List or Sales Data by Profit Ranges (Jul-Sep)")

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

# ================================
# File paths
# ================================
sales_file = "july to sep safa2025.Xlsx"
price_file = "price list(1).xlsx"

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# Fill missing numeric columns with NaN (so we can display 'Nil' later)
for col in ['Cost','Selling','Stock']:
    if col not in price_df.columns:
        price_df[col] = pd.NA

for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = pd.NA

# ================================
# Full Outer Join: All items in either dataset
# ================================
merged_df = pd.merge(
    price_df,
    sales_df,
    left_on='Item Bar Code',
    right_on='Item Code',
    how='outer'  # full outer join => items in either dataset
)

# Fill missing item names and category
merged_df['Item Name'] = merged_df['Item Name'].fillna('Unknown')
if 'Category' not in merged_df.columns:
    merged_df['Category'] = 'Unknown'
else:
    merged_df['Category'] = merged_df['Category'].fillna('Unknown')

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("Filters")
month_map = {"Jul-2025":"Jul","Aug-2025":"Aug","Sep-2025":"Sep"}
selected_month = st.sidebar.selectbox("Select Month", list(month_map.keys()))

profit_ranges = ["<5%", "5-10%", "10-20%", "20-30%", "30%+"]
selected_range = st.sidebar.selectbox("Select Profit Range", profit_ranges)

# Category Filter
categories = merged_df['Category'].unique().tolist()
categories.sort()
categories.insert(0, "All")
selected_category = st.sidebar.selectbox("Select Category", categories)

# ================================
# Compute Monthly GP
# ================================
sales_col = f"{selected_month} Total Sales"
profit_col = f"{selected_month} Total Profit"

merged_df['Monthly GP'] = merged_df.apply(
    lambda row: (row[profit_col]/row[sales_col]) if pd.notna(row[profit_col]) and pd.notna(row[sales_col]) and row[sales_col] != 0 else pd.NA,
    axis=1
)

# ================================
# Filter by Profit Range
# ================================
def filter_by_profit(df, profit_range):
    if profit_range == "<5%":
        return df[df['Monthly GP'] < 0.05]
    elif profit_range == "5-10%":
        return df[(df['Monthly GP'] >= 0.05) & (df['Monthly GP'] < 0.10)]
    elif profit_range == "10-20%":
        return df[(df['Monthly GP'] >= 0.10) & (df['Monthly GP'] < 0.20)]
    elif profit_range == "20-30%":
        return df[(df['Monthly GP'] >= 0.20) & (df['Monthly GP'] < 0.30)]
    elif profit_range == "30%+":
        return df[df['Monthly GP'] >= 0.30]
    else:
        return df

filtered_df = filter_by_profit(merged_df, selected_range)

# Apply category filter
if selected_category != "All":
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# ================================
# Replace missing numeric values with 'Nil' for display
# ================================
display_cols = ['Cost','Selling','Stock',sales_col,profit_col]
for col in display_cols:
    filtered_df[col] = filtered_df[col].apply(lambda x: 'Nil' if pd.isna(x) else x)

# Replace Monthly GP NaN with 'Nil'
filtered_df['Monthly GP'] = filtered_df['Monthly GP'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else 'Nil')

# ================================
# Key Metrics
# ================================
total_sales = filtered_df[sales_col].replace('Nil', 0).sum()
total_profit = filtered_df[profit_col].replace('Nil', 0).sum()
overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

st.markdown(f"### 🔑 Key Metrics for {selected_month} | Profit Range: {selected_range} | Category: {selected_category}")
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"{total_sales:,.0f}")
col2.metric("Total Profit", f"{total_profit:,.0f}")
col3.metric("GP", f"{overall_gp:.2%}")

# ================================
# Item-wise Table
# ================================
st.markdown(f"### 📝 Item-wise Details ({selected_month})")
table_cols = ['Item Bar Code','Item Name','Category','Cost','Selling','Stock',sales_col,profit_col,'Monthly GP']
st.dataframe(filtered_df[table_cols].sort_values('Monthly GP'))
