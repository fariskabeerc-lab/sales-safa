import streamlit as st
import pandas as pd

# ============================
# Page Config
# ============================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊Shams salem Sales & Profit Insights (Oct 2025)")

# ============================
# Load Data
# ============================
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()  # Return empty DataFrame if error
    # Fill missing categories
    df['Category'] = df['Category'].fillna('Unknown')
    # Calculate total sales and total profit
    sales_cols = [col for col in df.columns if 'Total Sales' in col]
    profit_cols = [col for col in df.columns if 'Total Profit' in col]
    df['Total Sales'] = df[sales_cols].sum(axis=1)
    df['Total Profit'] = df[profit_cols].sum(axis=1)
    # Calculate GP%
    df['GP%'] = (df['Total Profit'] / df['Total Sales'] * 100).round(2)
    # Replace inf or NaN GP% with 0
    df['GP%'] = df['GP%'].replace([float('inf'), -float('inf')], 0).fillna(0)
    return df

# ============================
# Load File
# ============================
file_path = "hilal oct sale.Xlsx"
df = load_data(file_path)

if df.empty:
    st.warning("No data loaded. Please check the file.")
else:
    # ============================
    # Sidebar Filters
    # ============================
    st.sidebar.header("Filters")

    # Category filter (single selection with "All")
    categories = ['All'] + df['Category'].unique().tolist()
    selected_category = st.sidebar.selectbox("Select Category", options=categories, index=0)

    # Exclude category (multiselect)
    exclude_categories = st.sidebar.multiselect("Exclude Categories", options=df['Category'].unique().tolist())

    # GP% filter (single selection with "All")
    gp_options = ['All', "<5%", "5-10%", "10-20%", "20-30%", "30%+"]
    selected_gp = st.sidebar.selectbox("Select GP% Range", options=gp_options, index=0)

    # ============================
    # Apply Filters
    # ============================
    filtered_df = df.copy()

    # Include category filter
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]

    # Exclude categories
    if exclude_categories:
        filtered_df = filtered_df[~filtered_df['Category'].isin(exclude_categories)]

    # Filter by GP%
    if selected_gp != 'All':
        if selected_gp == "<5%":
            filtered_df = filtered_df[filtered_df['GP%'] < 5]
        elif selected_gp == "5-10%":
            filtered_df = filtered_df[(filtered_df['GP%'] >= 5) & (filtered_df['GP%'] < 10)]
        elif selected_gp == "10-20%":
            filtered_df = filtered_df[(filtered_df['GP%'] >= 10) & (filtered_df['GP%'] < 20)]
        elif selected_gp == "20-30%":
            filtered_df = filtered_df[(filtered_df['GP%'] >= 20) & (filtered_df['GP%'] < 30)]
        elif selected_gp == "30%+":
            filtered_df = filtered_df[filtered_df['GP%'] >= 30]

    # ============================
    # Key Insights at Top
    # ============================
    st.markdown("### Key Insights")
    total_sales = filtered_df['Total Sales'].sum()
    total_profit = filtered_df['Total Profit'].sum()
    avg_gp = filtered_df['GP%'].mean().round(2) if not filtered_df.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f}")
    col2.metric("Total Profit", f"{total_profit:,.0f}")
    col3.metric("Average GP%", f"{avg_gp}%")

    # ============================
    # Display Table
    # ============================
    st.markdown("### Filtered Items")
    if filtered_df.empty:
        st.info("No items match the selected filters.")
    else:
        st.dataframe(filtered_df.reset_index(drop=True))
