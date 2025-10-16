import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Config
# ================================
st.set_page_config(page_title="Profit Range Dashboard", layout="wide")
st.title("📊 Items by Monthly Profit Ranges (Jul-Sep)")

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

# Fill missing sales columns if not in sales
for col in ['Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit',
            'Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col not in sales_df.columns:
        sales_df[col] = 0

# ================================
# Merge sales and price data
# ================================
merged_df = pd.merge(sales_df, price_df[['Item Bar Code','Item Name']],
                     left_on='Item Code', right_on='Item Bar Code', how='left')

# Fill missing values
merged_df['Item Name'] = merged_df['Item Name'].fillna('Unknown')
for col in ['Cost','Selling','Stock','Jul-2025 Total Sales','Jul-2025 Total Profit',
            'Aug-2025 Total Sales','Aug-2025 Total Profit','Sep-2025 Total Sales','Sep-2025 Total Profit']:
    if col in merged_df.columns:
        merged_df[col] = merged_df[col].fillna(0)
    else:
        merged_df[col] = 0

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

# ================================
# Compute Monthly GP
# ================================
sales_col = f"{selected_month} Total Sales"
profit_col = f"{selected_month} Total Profit"
merged_df['Monthly GP'] = merged_df.apply(lambda row: (row[profit_col]/row[sales_col]) if row[sales_col] != 0 else 0, axis=1)

# ================================
# Filter by Monthly GP
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

# ================================
# Key Metrics
# ================================
total_sales = filtered_df[sales_col].sum()
total_profit = filtered_df[profit_col].sum()
overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

st.markdown(f"### 🔑 Key Metrics for {selected_month} | Profit Range: {selected_range}")
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"{total_sales:,.0f}")
col2.metric("Total Profit", f"{total_profit:,.0f}")
col3.metric("GP", f"{overall_gp:.2%}")

# ================================
# Monthly Profit Distribution Graph
# ================================
st.markdown(f"### 📊 Profit Distribution for {selected_month}")
fig = px.histogram(filtered_df, x='Monthly GP', nbins=20,
                   title=f"{selected_month} Profit Distribution",
                   labels={'Monthly GP':'Gross Profit %'}, color='Category')
st.plotly_chart(fig, use_container_width=True)

# ================================
# Item-wise Table
# ================================
st.markdown(f"### 📝 Item-wise Details ({selected_month})")
table_cols = ['Item Bar Code','Item Name','Category','Cost','Selling','Stock',sales_col,profit_col,'Monthly GP']
filtered_df['Monthly GP'] = filtered_df['Monthly GP'].apply(lambda x: f"{x:.2%}")
st.dataframe(filtered_df[table_cols].sort_values('Monthly GP'))
