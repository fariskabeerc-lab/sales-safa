import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Sales & Inventory Dashboard", layout="wide")
st.title("📊 Sales, Profit & Inventory Insights")

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None

file_path = st.file_uploader("📂 Upload your Excel file", type=["xlsx"])

if file_path:
    df = load_data(file_path)

    if df is None or df.empty:
        st.error("❌ Failed to load data or file is empty.")
    else:
        # ===================================================
        # CATEGORY FILTER
        # ===================================================
        categories = sorted(df["Category"].dropna().unique())
        selected_category = st.selectbox("🔍 Filter by Category", ["All"] + list(categories))

        if selected_category != "All":
            filtered_df = df[df["Category"] == selected_category].copy()
        else:
            filtered_df = df.copy()

        # ===================================================
        # COMPUTE TOTALS (FIXED VERSION)
        # ===================================================
        def compute_row_totals(row):
            try:
                sales_cols = [col for col in row.index if "Sales" in col]
                profit_cols = [col for col in row.index if "Profit" in col or "GP" in col]

                total_sales = row[sales_cols].sum(skipna=True) if sales_cols else 0
                total_profit = row[profit_cols].sum(skipna=True) if profit_cols else 0
                overall_gp = (total_profit / total_sales * 100) if total_sales != 0 else 0

                return pd.Series([total_sales, total_profit, overall_gp])
            except Exception:
                return pd.Series([0, 0, 0])

        filtered_df[["Total Sales", "Total Profit", "Overall GP"]] = filtered_df.apply(
            compute_row_totals, axis=1
        )

        # ===================================================
        # MAIN TABLE (ITEMWISE)
        # ===================================================
        st.subheader("📦 Itemwise Overview")
        st.dataframe(
            filtered_df[
                [
                    "Item Name",
                    "Item Bar Code",
                    "Category",
                    "Cost",
                    "Selling",
                    "Stock",
                    "Margin%",
                    "Stock Value",
                    "Total Sales",
                    "Total Profit",
                    "Overall GP",
                ]
            ],
            use_container_width=True,
        )

        # ===================================================
        # INSIGHTS TABLE: ZERO SALES ITEMS
        # ===================================================
        zero_sales_df = filtered_df[filtered_df["Total Sales"] == 0]
        st.subheader("🛑 Items with Stock Value but Zero Sales")
        st.write(f"Total such items: {len(zero_sales_df)}")
        st.dataframe(
            zero_sales_df[
                [
                    "Item Name",
                    "Category",
                    "Stock",
                    "Stock Value",
                    "Selling",
                    "Margin%",
                ]
            ],
            use_container_width=True,
        )

        # ===================================================
        # CATEGORY SUMMARY
        # ===================================================
        st.subheader("📈 Category Summary")
        category_summary = (
            filtered_df.groupby("Category")[["Total Sales", "Total Profit", "Stock Value"]]
            .sum()
            .reset_index()
        )
        st.dataframe(category_summary, use_container_width=True)

        # ===================================================
        # CHARTS
        # ===================================================
        st.subheader("📊 Top Performing Items (By Sales)")
        top_sales = (
            filtered_df.sort_values("Total Sales", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )
        fig_sales = px.bar(
            top_sales,
            x="Item Name",
            y="Total Sales",
            color="Category",
            title="Top 20 Items by Sales",
        )
        st.plotly_chart(fig_sales, use_container_width=True)

        st.subheader("💰 Top Profitable Items")
        top_profit = (
            filtered_df.sort_values("Total Profit", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )
        fig_profit = px.bar(
            top_profit,
            x="Item Name",
            y="Total Profit",
            color="Category",
            title="Top 20 Items by Profit",
        )
        st.plotly_chart(fig_profit, use_container_width=True)

else:
    st.info("👆 Please upload your Excel file to start.")
