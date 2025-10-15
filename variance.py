import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- Configuration and Setup ---
st.set_page_config(layout="wide", page_title="Financial Performance Dashboard")

# --- Global Configuration ---
DATA_FILE_PATH = 'july to sep safa2025.Xlsx'

# Initialize session state for view management
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = 'All Categories' # Default to All Categories
if 'df_data' not in st.session_state:
    st.session_state.df_data = None
if 'df_category_agg' not in st.session_state:
    st.session_state.df_category_agg = None
if 'monthly_metrics' not in st.session_state:
    st.session_state.monthly_metrics = []

# --- Data Loading and Processing Functions ---

@st.cache_data
def load_data(file_path):
    """Reads the specified data file into a DataFrame."""
    try:
        # Check file extension (assuming Excel based on user input, but handling CSV fallback)
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            # Assuming Excel (.xlsx or .xls)
            # Use 'openpyxl' engine which is required for .xlsx
            df = pd.read_excel(file_path, engine='openpyxl') 
        
        # Standardize column names (strip whitespace and ensure correct capitalization for matching)
        df.columns = df.columns.str.strip()
        # Remove non-alphanumeric characters except spaces and hyphens for cleaner matching
        df.columns = df.columns.str.replace(r'[^a-zA-Z0-9\s-]', '', regex=True) 

        return df
    except FileNotFoundError:
        st.error(f"Error: File '{file_path}' not found. Please ensure the file is in the same directory as this script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading file '{file_path}': {e}")
        return pd.DataFrame()

def process_and_aggregate_data(df):
    """Identifies metric columns, calculates totals, and aggregates by category."""
    
    # 1. Identify monthly metric columns
    # We look for columns containing 'Total Sales' or 'Total Profit'
    metric_cols = [col for col in df.columns if re.search(r'(Total Sales|Total Profit)$', col, re.IGNORECASE)]
    
    if not metric_cols:
        st.error("Could not find required metric columns (e.g., 'Jul-2025 Total Sales', 'Aug-2025 Total Profit'). Please check your column names.")
        return pd.DataFrame(), pd.DataFrame(), []

    # 2. Convert identified columns to numeric, coercing errors to 0
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 3. Calculate Item-level overall totals
    sales_cols = [col for col in metric_cols if 'Total Sales' in col]
    profit_cols = [col for col in metric_cols if 'Total Profit' in col]

    df['Total Sales'] = df[sales_cols].sum(axis=1)
    df['Total Profit'] = df[profit_cols].sum(axis=1)
    
    # NEW: Calculate Item-level Gross Profit (GP) Margin (Profit / Sales)
    df['GP'] = df.apply(
        lambda row: (row['Total Profit'] / row['Total Sales']) if row['Total Sales'] != 0 else 0,
        axis=1
    )
    
    # 4. Clean 'Category' and filter
    if 'Category' not in df.columns:
        st.error("The 'Category' column is missing.")
        return pd.DataFrame(), pd.DataFrame(), []

    df['Category'] = df['Category'].astype(str).str.strip()
    df_clean = df[df['Category'] != ''].copy()

    if df_clean.empty:
        st.error("No valid rows found after filtering out empty categories.")
        return pd.DataFrame(), pd.DataFrame(), []

    # 5. Aggregate by Category
    df_category_agg = df_clean.groupby('Category').agg(
        Total_Sales=('Total Sales', 'sum'),
        Total_Profit=('Total Profit', 'sum')
    ).reset_index()

    # NEW: Calculate aggregated GP for categories
    df_category_agg['GP'] = df_category_agg.apply(
        lambda row: (row['Total_Profit'] / row['Total_Sales']) if row['Total_Sales'] != 0 else 0,
        axis=1
    )

    return df_clean, df_category_agg, metric_cols

# --- Sidebar Controls ---

def render_sidebar_controls(df_category_agg):
    """Renders the Category filter and search bars in the sidebar."""
    
    st.sidebar.title("Data Filters")
    st.sidebar.markdown("---")
    
    # 1. Category Filter (Select Box)
    categories = ['All Categories'] + sorted(df_category_agg['Category'].tolist())
    
    selected_category = st.sidebar.selectbox(
        "Filter by Category",
        options=categories,
        key='sidebar_category_select'
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Item Search (Applies to Item View)")
    
    # 2. Search Filters
    search_name = st.sidebar.text_input("Search by Item Name", key='sidebar_search_name').lower()
    search_code = st.sidebar.text_input("Search by Item Code/Barcode", key='sidebar_search_code').lower()

    return selected_category, search_name, search_code

# --- Visualization Functions ---

def create_category_chart(df_agg):
    """Generates a bar chart for Sales vs Profit by Category."""
    df_sorted = df_agg.sort_values(by='Total_Sales', ascending=False)
    
    fig = go.Figure()

    # Sales Bar Chart
    fig.add_trace(go.Bar(
        x=df_sorted['Category'],
        y=df_sorted['Total_Sales'],
        name='Total Sales',
        marker_color='rgb(59, 130, 246)' # Tailwind blue-500
    ))

    # Profit Bar Chart 
    fig.add_trace(go.Bar(
        x=df_sorted['Category'],
        y=df_sorted['Total_Profit'],
        name='Total Profit',
        marker_color='rgb(16, 185, 129)' # Tailwind emerald-500
    ))

    fig.update_layout(
        title_text='Total Sales and Profit by Category',
        xaxis_title='Category',
        yaxis_title='Amount',
        barmode='group',
        hovermode="x unified",
        height=450
    )
    return fig

def create_item_monthly_chart(df_item, category_name):
    """Generates a line chart for monthly trend of Sales and Profit for a category's items."""
    
    monthly_sales_cols = [col for col in st.session_state.monthly_metrics if 'Total Sales' in col]
    monthly_profit_cols = [col for col in st.session_state.monthly_metrics if 'Total Profit' in col]

    # Calculate category monthly totals
    monthly_sales = df_item[monthly_sales_cols].sum()
    monthly_profit = df_item[monthly_profit_cols].sum()
    
    # Extract month labels (e.g., 'Jul-2025')
    # Use only the date part of the column name for the X-axis labels
    months = [col.replace(' Total Sales', '').replace(' Total Profit', '') for col in monthly_sales_cols]

    # Create Plotly Line Chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months,
        y=monthly_sales.values,
        mode='lines+markers',
        name='Monthly Sales',
        line=dict(color='rgb(59, 130, 246)', width=3),
        marker=dict(size=8)
    ))

    fig.add_trace(go.Scatter(
        x=months,
        y=monthly_profit.values,
        mode='lines+markers',
        name='Monthly Profit',
        line=dict(color='rgb(16, 185, 129)', width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title_text=f"Monthly Sales and Profit Trend for {category_name}",
        xaxis_title='Month',
        yaxis_title='Amount',
        hovermode="x unified",
        height=450
    )
    return fig

# --- Layout and Rendering ---

def render_category_view(df_category_agg):
    """Displays the main Category overview, now including overall GP metric."""
    st.subheader("Category Overview: Total Sales, Profit, and GP Margin")
    
    # 1. Metrics - REMOVED '$'
    total_sales = df_category_agg['Total_Sales'].sum()
    total_profit = df_category_agg['Total_Profit'].sum()
    
    # Calculate Company Gross Profit Margin
    total_gp = (total_profit / total_sales) if total_sales != 0 else 0

    # Changed to 4 columns to include GP
    col1, col2, col3, col4 = st.columns(4) 
    
    with col1:
        st.metric(label="Total Company Sales (All Months)", 
                  value=f"{total_sales:,.2f}", 
                  delta_color="off")
    with col2:
        st.metric(label="Total Company Profit (All Months)", 
                  value=f"{total_profit:,.2f}", 
                  delta_color="off")
    with col3: # New column for GP
        st.metric(label="Total Company GP Margin", 
                  value=f"{total_gp:.2%}", # Format as percentage
                  delta_color="off")
    with col4: 
        st.metric(label="Total Categories", 
                  value=f"{len(df_category_agg):,}", 
                  delta_color="off")

    st.markdown("---")
    
    # 2. Chart
    st.plotly_chart(create_category_chart(df_category_agg), use_container_width=True)

    st.markdown("---")

    # 3. Table 
    st.subheader("Category Performance Table")
    
    # Display GP in the category table
    df_display = df_category_agg.copy()
    # Updated column list to include 'GP'
    df_display.columns = ['Category', 'Total Sales', 'Total Profit', 'GP'] 
    
    # Format GP as percentage
    df_display['GP'] = df_display['GP'].map('{:.2%}'.format) 
    # Format Sales/Profit as numbers (removed $)
    df_display['Total Sales'] = df_display['Total Sales'].map('{:,.2f}'.format)
    df_display['Total Profit'] = df_display['Total Profit'].map('{:,.2f}'.format)
    
    st.dataframe(df_display, 
                 column_config={
                     "Category": st.column_config.TextColumn("Category"),
                     "Total Sales": st.column_config.TextColumn("Total Sales", help="Overall sales across all months."),
                     "Total Profit": st.column_config.TextColumn("Total Profit", help="Overall profit across all months."),
                     # Added GP Column Config
                     "GP": st.column_config.TextColumn("GP Margin", help="Gross Profit Margin (Profit/Sales)") 
                 },
                 hide_index=True, 
                 use_container_width=True)
                 
    st.info("Use the **Filter by Category** dropdown in the sidebar to drill down to item details.")


def render_item_view(df_data, category_name, search_name, search_code):
    """
    Displays the item-level detail for the selected category, 
    applying search filters passed from the sidebar. Now includes item GP.
    """
    
    # Filter data for the selected category
    df_category_items = df_data[df_data['Category'] == category_name].copy()

    st.header(f"Items in: {category_name}")
    
    st.markdown("---")
    
    # Apply filters using the values passed from the sidebar
    df_filtered = df_category_items
    
    # Find the actual name column by inference
    name_col = next((col for col in df_filtered.columns if re.search(r'items|item name', col, re.IGNORECASE) and 'code' not in col.lower()), None)
    
    if search_name and name_col:
         df_filtered = df_filtered[df_filtered[name_col].astype(str).str.lower().str.contains(search_name, na=False)]
    elif search_name and not name_col:
        st.warning("Could not find a clear 'Items'/'Item Name' column for name search.")

    # Find the actual code column by inference
    code_col = next((col for col in df_filtered.columns if re.search(r'item code|barcode', col, re.IGNORECASE)), None)
    
    if search_code and code_col:
        df_filtered = df_filtered[df_filtered[code_col].astype(str).str.lower().str.contains(search_code, na=False)]
    elif search_code and not code_col:
        st.warning("Could not find a clear 'Item Code'/'Barcode' column for code search.")
            
    st.info(f"Showing {len(df_filtered)} of {len(df_category_items)} items in this category.")
    st.markdown("---")

    # 2. Monthly Trend Chart (based on the original category items, not the filtered set)
    st.plotly_chart(create_item_monthly_chart(df_category_items, category_name), use_container_width=True)
    st.markdown("---")

    # 3. Item-level Detailed Table
    st.subheader("Item Performance Details")
    
    display_cols = []
    
    # Prioritize inferred Item Code and Item Name columns
    if code_col and code_col in df_filtered.columns: display_cols.append(code_col)
    if name_col and name_col in df_filtered.columns: display_cols.append(name_col)
    
    # Ensure mandatory Total columns are present, including GP
    display_cols.extend(['Total Sales', 'Total Profit', 'GP']) 
    
    # Add monthly metrics
    display_cols.extend(st.session_state.monthly_metrics)
    
    # Filter for columns that actually exist and remove duplicates
    final_cols = [c for c in display_cols if c in df_filtered.columns]
    final_cols = list(pd.unique(final_cols))
    
    df_table = df_filtered[final_cols].copy()
    
    # Format the 'GP' column as percentage 
    df_table['GP'] = df_table['GP'].map('{:.2%}'.format)

    # Define column configurations for formatting totals and monthly metrics 
    column_config = {
        'Total Sales': st.column_config.NumberColumn("Total Sales", format="%.2f"),
        'Total Profit': st.column_config.NumberColumn("Total Profit", format="%.2f"),
        # Updated GP format for the table
        'GP': st.column_config.TextColumn("GP Margin", help="Gross Profit Margin (Profit/Sales)"), 
    }
    
    for col in st.session_state.monthly_metrics:
         column_config[col] = st.column_config.NumberColumn(col, format="%.2f")

    st.dataframe(
        df_table, 
        column_config=column_config,
        hide_index=True, 
        use_container_width=True
    )


# --- Main Application Logic ---

def main():
    st.title("💰 Sales and Profit Analyzer")
    st.markdown(f"Loading data directly from **{DATA_FILE_PATH}**. Ensure this file is in the same directory as the script.")
    
    # Check if data is already loaded in session state (first run only)
    if st.session_state.df_data is None:
        with st.spinner(f"Attempting to load data from {DATA_FILE_PATH}..."):
            df_raw = load_data(DATA_FILE_PATH) # Direct call with path
            
            if not df_raw.empty:
                # Only proceed if data was loaded without FileNotFoundError
                df_data, df_category_agg, monthly_metrics = process_and_aggregate_data(df_raw)
                
                if not df_data.empty:
                    st.session_state.df_data = df_data
                    st.session_state.df_category_agg = df_category_agg
                    st.session_state.monthly_metrics = monthly_metrics
                    # Initial category view is now 'All Categories' by default
                    st.session_state.selected_category = 'All Categories'
                    st.success("Data loaded and processed successfully!")
                else:
                    st.error("Failed to process data. Check console/file content for structure issues.")
                    st.session_state.df_data = None 
            else:
                # File not found or read error already handled in load_data
                st.session_state.df_data = None
                
    # Display the correct view based on state
    if st.session_state.df_data is not None:
        
        # New: Render Sidebar Controls and get filter selections
        selected_category, search_name, search_code = render_sidebar_controls(st.session_state.df_category_agg)
        
        # Logic to determine which view to render based on sidebar selection
        if selected_category == 'All Categories':
            # View 1: Category Overview
            render_category_view(st.session_state.df_category_agg)
        else:
            # View 2: Item Detail for selected category, applying sidebar search filters
            render_item_view(st.session_state.df_data, selected_category, search_name, search_code)
    
    # Add a note if data failed to load
    elif st.session_state.df_data is None and DATA_FILE_PATH:
        st.markdown(f"Please ensure **{DATA_FILE_PATH}** is present and contains correct columns.")


if __name__ == "__main__":
    main()
