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
    # Fill missing categories
    df['Category'] = df['Category'].fillna('Unknown')
    # Calculate total sales and total profit
    df['Total Sales'] = df[['Jul-2025 Total Sales', 'Aug-2025 Total Sales', 'Sep-2025 Total Sales']].sum(axis=1)
    df['Total Profit'] = df[['Jul-2025 Total Profit', 'Aug-2025 Total Profit', 'Sep-2025 Total Profit']].sum(axis=1)
    # Calculate GP%
    df['GP%'] = (df['Total Profit'] / df['Total Sales'] * 100).round(2)
    return df

# ============================
# Load your file
# ============================
file_path = "july to sep safa2025.Xlsx"
df = load_data(file_path)

# ============================
# Filters
# ============================
categories = df['Category'].unique().tolist()
selected_categories = st.multiselect("Select Categories", options=categories, default=categories)

gp_options = ["<5%", "5-10%", "10-20%", "20-30%", "30%+"]
selected_gp = st.multiselect("Select GP% Range", options=gp_options, default=gp_options)

# Filter by category
filtered_df = df[df['Category'].isin(selected_categories)]

# Filter by GP%
gp_filtered = pd.DataFrame()
for gp_range in selected_gp:
    if gp_range == "<5%":
        gp_filtered = pd.concat([gp_filtered, filtered_df[filtered_df['GP%'] < 5]])
    elif gp_range == "5-10%":
        gp_filtered = pd.concat([gp_filtered, filtered_df[(filtered_df['GP%'] >= 5) & (filtered_df['GP%'] < 10)]])
    elif gp_range == "10-20%":
        gp_filtered = pd.concat([gp_filtered, filtered_df[(filtered_df['GP%'] >= 10) & (filtered_df['GP%'] < 20)]])
    elif gp_range == "20-30%":
        gp_filtered = pd.concat([gp_filtered, filtered_df[(filtered_df['GP%'] >= 20) & (filtered_df['GP%'] < 30)]])
    elif gp_range == "30%+":
        gp_filtered = pd.concat([gp_filtered, filtered_df[filtered_df['GP%'] >= 30]])

# ============================
# Display Table
# ============================
st.dataframe(gp_filtered.reset_index(drop=True))

# ============================
# Summary KPIs
# ============================
st.markdown("### Summary")
total_sales = gp_filtered['Total Sales'].sum()
total_profit = gp_filtered['Total Profit'].sum()
avg_gp = gp_filtered['GP%'].mean().round(2)
st.metric("Total Sales", f"${total_sales:,.2f}")
st.metric("Total Profit", f"${total_profit:,.2f}")
st.metric("Average GP%", f"{avg_gp}%")
