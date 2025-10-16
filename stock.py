import streamlit as st
import pandas as pd

# ============================
# Page Config
# ============================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊 Sales & Profit Insights (Jul-Sep 2025)")

# ============================
# Load Data
# ============================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    df['Category'] = df['Category'].fillna('Unknown')
    df['Total Sales'] = df[['Jul-2025 Total Sales', 'Aug-2025 Total Sales', 'Sep-2025 Total Sales']].sum(axis=1)
    df['Total Profit'] = df[['Jul-2025 Total Profit', 'Aug-2025 Total Profit', 'Sep-2025 Total Profit']].sum(axis=1)
    df['GP%'] = (df['Total Profit'] / df['Total Sales'] * 100).round(2)
    return df

# ============================
# Load File
# ============================
file_path = "july to sep safa2025.Xlsx"
df = load_data(file_path)

# ============================
# Sidebar Filters
# ============================
st.sidebar.header("Filters")

# Category filter (single selection with "All")
categories = ['All'] + df['Category'].unique().tolist()
selected_category = st.sidebar.selectbox("Select Category", options=categories, index=0)

# Exclude category (multiselect, can exclude multiple)
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
avg_gp = filtered_df['GP%'].mean().round(2)
