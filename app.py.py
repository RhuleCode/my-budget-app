import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Secure Budget Vault", page_icon="💰", layout="wide")

# --- 2. SESSION STATE (MEMORY) ---
if "username" not in st.session_state:
    st.session_state.username = "nkb" # Default user
if "currency" not in st.session_state:
    st.session_state.currency = "$"

# --- 3. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. SIDEBAR: CONTROLS & INPUTS ---
with st.sidebar:
    st.header(f"👋 Welcome, {st.session_state.username}!")
    
    # Account & Settings Row
    col1, col2 = st.columns(2)
    with col1:
        # Currency Selector
        curr_options = ["GH₵ (GHS)", 
            "₦ (NGN)", 
            "$ (USD)", 
            "€ (EUR)", 
            "£ (GBP)", 
            "KSh (KES)", 
            "R (ZAR)", 
            "¥ (JPY)"]
        st.session_state.currency = st.selectbox(
            "Currency", 
            options=curr_options, 
            help="Choose the currency symbol to display on your dashboard."
        )
    with col2:
        # Log Out Button
        st.write("") # Spacing alignment
        st.write("")
        if st.button("Log Out", help="Click to securely clear your session and lock the vault."):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()

    # --- NEW: DEVELOPER PROFILE FIELD ---
    with st.expander("👨‍💻 About the Developer", expanded=False):
        st.markdown("""
        **Developer:** `Nana Kwaku Bentum Rhule`  
        **Specialization:** Cybersecurity & Secure Application Development  
        **Environment:** Environment built and tested on Ubuntu Linux  
        
        *Building secure tools for modern financial tracking.*
        """)
        # Link button directly pointing to your main GitHub account page
        st.link_button("🌐 View GitHub Profile", "https://github.com/Rhulecode")
    
    st.divider()
    
    st.header("📝 New Transaction")
    # Form keeps inputs grouped and prevents spacing crashes
    with st.form("transaction_form", clear_on_submit=True):
        date_val = st.date_input(
            "Date", 
            help="When did this transaction occur?"
        )
        type_val = st.selectbox(
            "Transaction Type", 
            ["Income", "Expense", "Transfer"], 
            help="Income adds to your balance. Expense subtracts. Transfer is ignored in totals."
        )
        desc_val = st.text_input(
            "Description", 
            help="A quick note to remember this by (e.g., 'Uber to campus' or 'Groceries')."
        )
        cat_val = st.selectbox(
            "Category", 
            ["Food", "Rent", "Salary", "Transport", "Utilities", "Purchase", "Other"], 
            help="Grouping similar expenses helps generate accurate pie charts."
        )
        amount_val = st.number_input(
            "Amount", 
            min_value=0.0, 
            format="%.2f", 
            help="Enter the exact monetary amount."
        )
        
        submitted = st.form_submit_button("Save to Vault")
        
        if submitted:
            existing_data = conn.read(worksheet="Transaction", usecols=list(range(6)), ttl=0)
            existing_data = existing_data.dropna(how="all")
            
            new_row = pd.DataFrame([{
                "Date": date_val.strftime("%Y-%m-%d"),
                "Type": type_val,
                "Description": desc_val,
                "Category": cat_val,
                "Amount": amount_val,
                "User": st.session_state.username
            }])
            
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Transaction", data=updated_df)
            st.success(f"✅ Saved: {cat_val} ({type_val})")

# --- 5. MAIN DASHBOARD ---
st.title("💰 Your Secure Budget Vault")

# User Guide Expander
with st.expander("📖 User Guide: How to use this app"):
    st.markdown("""
    ### 📝 Adding Transactions (Sidebar)
    * **Transaction Type:** Income (adds money), Expense (subtracts money), Transfer (moves money).
    * **Category:** Groups your spending to generate your analytics.
    
    ### 📊 Dashboard View Modes
    * **Custom Cycle:** View your data across a specific date range (like your personal pay cycle).
    * **Daily View:** Zoom in on a single specific day to check daily limits.
    """)

# Fetch and Filter Data securely
try:
    all_data = conn.read(worksheet="Transaction", usecols=list(range(6)), ttl=0)
    all_data = all_data.dropna(how="all")
    df = all_data[all_data['User'] == st.session_state.username].copy()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

if df.empty:
    st.info(f"No data found for user: **{st.session_state.username}**. Add a transaction in the sidebar!")
else:
    # Clean the data
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    
    # --- DASHBOARD VIEW MODE TOGGLE ---
    st.markdown("### 📊 Dashboard View Mode")
    view_mode = st.radio(
        "How would you like to view your data?", 
        ["Custom Cycle", "Daily View"], 
        horizontal=True,
        help="Toggle between viewing a span of time or a single day."
    )
    
    # Filter by dates based on toggle
    if view_mode == "Custom Cycle":
        # Default to the first of the current month up to today
        today = date.today()
        start_of_month = today.replace(day=1)
        selected_dates = st.date_input(
            "Select your cycle:", 
            value=(start_of_month, today),
            help="Pick a Start Date and an End Date."
        )
        
        # Ensure two dates are picked before filtering
        if len(selected_dates) == 2:
            start, end = selected_dates
            cycle_df = df[(df['Date'] >= start) & (df['Date'] <= end)]
        else:
            cycle_df = df[df['Date'] == selected_dates[0]] # Fallback if only one clicked
            
    else: # Daily View
        selected_date = st.date_input(
            "Select a day:", 
            value=date.today(),
            help="Pick a specific calendar day to view."
        )
        cycle_df = df[df['Date'] == selected_date]

    # --- CALCULATIONS & METRICS ---
    st.divider()
    
    # Math logic: Note that "Transfer" is naturally ignored here
    total_income = cycle_df[cycle_df['Type'] == 'Income']['Amount'].sum()
    total_expense = cycle_df[cycle_df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense
    
    c = st.session_state.currency # Grab chosen currency symbol
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Cycle Income", f"{c}{total_income:,.2f}")
    col2.metric("Cycle Expenses", f"{c}{total_expense:,.2f}")
    col3.metric("Current Balance", f"{c}{balance:,.2f}", delta=balance)
    
    # --- TABS FOR CHARTS AND DATA ---
    st.write("") # Spacing
    tab1, tab2 = st.tabs(["📊 Analytics Charts", "📋 Ledger History"])
    
    with tab1:
        st.subheader("Spending by Category")
        expense_df = cycle_df[cycle_df['Type'] == 'Expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, values='Amount', names='Category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No expenses logged in this timeframe to chart.")
            
    with tab2:
        st.subheader("Secure Ledger")
        # Format the dataframe to look nice
        st.dataframe(
            cycle_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount", format=f"{c}%.2f")
            }
        )
