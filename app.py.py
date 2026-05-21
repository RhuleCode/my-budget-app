import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- PAGE SETUP ---
st.set_page_config(page_title="Secure Budget Vault", page_icon="💰", layout="wide")

# --- SESSION STATE (LOGIN) ---
if "username" not in st.session_state:
    st.session_state.username = "nkb" # Sets your default username

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SIDEBAR: CONTROLS & INPUTS ---
with st.sidebar:
    st.header("🔐 Vault Access")
    # This automatically updates the session state when you type a new name
    st.session_state.username = st.text_input("Username", value=st.session_state.username)
    
    st.divider()
    
    st.header("📝 New Transaction")
    # Using a form prevents the indentation crash you experienced!
    with st.form("transaction_form", clear_on_submit=True):
        date_val = st.date_input("Date")
        type_val = st.selectbox("Type", ["Income", "Expense", "Transfer"])
        desc_val = st.text_input("Description")
        cat_val = st.selectbox("Category", ["Food", "Rent", "Salary", "Transport", "Utilities", "Other"])
        amount_val = st.number_input("Amount", min_value=0.0, format="%.2f")
        
        # The form submit button
        submitted = st.form_submit_button("Save to Vault")
        
        if submitted:
            # 1. Pull current data
            existing_data = conn.read(worksheet="Transaction", usecols=list(range(6)), ttl=0)
            existing_data = existing_data.dropna(how="all") # Clean up empty rows
            
            # 2. Package the new data
            new_row = pd.DataFrame([{
                "Date": date_val.strftime("%Y-%m-%d"),
                "Type": type_val,
                "Description": desc_val,
                "Category": cat_val,
                "Amount": amount_val,
                "User": st.session_state.username # Stamps the transaction with the active user
            }])
            
            # 3. Save to Google Sheets
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Transaction", data=updated_df)
            st.success("Transaction securely saved to the Vault!")

# --- MAIN DASHBOARD CONTENT ---
st.title("💰 Your Secure Budget Vault")

# --- IN-APP USER GUIDE ---
with st.expander("📖 User Guide: How to use this app"):
    st.markdown("""
    ### 📝 Adding Transactions (Sidebar)
    * **Type:** Select Income (adds money), Expense (subtracts money), or Transfer.
    * **Category:** Groups your spending to generate your pie charts.
    
    ### 📊 Dashboard Features
    * **Private Vault:** You will only see data logged under your current Username. To see other data, change the username in the sidebar.
    * **Ledger:** View and verify your raw data in the Ledger tab.
    """)

# --- FETCH & FILTER DATA ---
try:
    all_data = conn.read(worksheet="Transaction", usecols=list(range(6)), ttl=0)
    all_data = all_data.dropna(how="all")
    
    # SECURITY FILTER: Only keep rows where the User matches the sidebar input
    df = all_data[all_data['User'] == st.session_state.username]
    
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# --- RENDER DASHBOARD ---
if df.empty:
    st.info(f"No data found for user: **{st.session_state.username}**. Add a transaction in the sidebar to populate your dashboard!")
else:
    # Ensure math works correctly
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    
    # Calculate totals based on the 'Type' column
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense
    
    # Draw top metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${total_income:,.2f}")
    col2.metric("Total Expenses", f"${total_expense:,.2f}")
    col3.metric("Current Balance", f"${balance:,.2f}", delta=balance)
    
    st.divider()
    
    # Draw Tabs for Charts and Data
    tab1, tab2 = st.tabs(["📊 Analytics", "📋 Ledger History"])
    
    with tab1:
        st.subheader("Spending by Category")
        expense_df = df[df['Type'] == 'Expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, values='Amount', names='Category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No expenses logged yet to chart.")
            
    with tab2:
        st.subheader("Secure Ledger")
        st.dataframe(df, use_container_width=True, hide_index=True)
