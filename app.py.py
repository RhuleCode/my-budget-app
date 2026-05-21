import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. INITIAL SETUP & CONNECTION ---
st.set_page_config(page_title="Secure Budget Vault", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. AUTHENTICATION GATING ---
if "username" in st.session_state:
    
    # --- SIDEBAR CONTENT ---
    with st.sidebar:
        st.header(f"👋 Welcome, {st.session_state.username}!")
        
        st.subheader("📝 Add Transaction")
        tx_type = st.radio("Transaction Type", ["Expense", "Income", "Transfer"], horizontal=True, help="Select the type of movement.")
        new_date = st.date_input("Date")
        new_desc = st.text_input("Description", placeholder="e.g., Uber, Salary, Rent...")
        new_cat = st.text_input("Category Name", placeholder="e.g., Transport, Food...")
        new_amt = st.number_input("Amount", value=0.0, step=1.0)
        
        if st.button("Save to Vault"):
            if new_cat and new_amt > 0:
                new_entry = pd.DataFrame([{
                    "Date": str(new_date),
                    "Type": tx_type,
                    "Description": new_desc,
                    "Category": new_cat,
                    "Amount": new_amt,
                    "User": st.session_state.username
                }])
                all_data = conn.read(worksheet="Transaction", ttl=0)
                updated_vault = pd.concat([all_data, new_entry], ignore_index=True)
                conn.update(worksheet="Transaction", data=updated_vault)
                st.success(f"✅ Saved!")
                st.rerun()
                
        st.divider()
        st.subheader("⚙️ Preferences")
        currency_map = {"USD ($)": "$", "GHS (₵)": "₵", "EUR (€)": "€", "GBP (£)": "£", "NGN (₦)": "₦"}
        selected_curr_label = st.selectbox("Local Currency", list(currency_map.keys()))
        st.session_state.currency = currency_map[selected_curr_label]
        
        st.divider()
        if st.button("Log Out"):
            del st.session_state["username"]
            st.rerun()
        
        if st.button("Delete My Account"):
            users_df = conn.read(worksheet="Users", ttl=0)
            updated_users = users_df[users_df['Username'] != st.session_state.username]
            conn.update(worksheet="Users", data=updated_users)
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- MAIN DASHBOARD CONTENT ---
    st.title("💰 Your Secure Budget Vault")
    # --- NEW: IN-APP USER GUIDE ---
    with st.expander("📖 User Guide: How to use this app"):
        st.markdown("""
        ### 📝 Adding Transactions (Sidebar)
        * **Transaction Type:** * **Income:** Money earned (increases balance).
          * **Expense:** Money spent (decreases balance).
          * **Transfer:** Moving money between accounts (ignored in profit/loss).
        * **Date & Description:** Log *when* and *what* occurred (e.g., "Uber to campus").
        * **Category:** Groups your spending (e.g., "Transport", "Food") to generate your pie charts.
        
        ### 📊 Dashboard View Modes
        * **Custom Cycle:** View your data across a specific date range (like your personal pay cycle). Generates an interactive timeline chart.
        * **Daily View:** Zoom in on a single specific day to check your daily limits. Generates a daily breakdown bar chart.
        
        ### ⚙️ Account & Exports
        * **Local Currency:** Change your display symbol in the sidebar Preferences.
        * **Export to CSV:** Go to the **Ledger History** tab to securely download your currently filtered data as a spreadsheet file.
        """)
    all_data = conn.read(worksheet="Transaction", ttl=0)
    df = all_data[all_data['User'] == st.session_state.username]
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df['Type'] = df['Type'].fillna('Expense')
        
    # --- NEW FEATURE: VIEW MODE TOGGLE ---
        st.markdown("### 📊 Dashboard View Mode")
        view_mode = st.radio("How would you like to view your data?", ["Custom Cycle", "Daily View"], horizontal=True)

        if view_mode == "Custom Cycle":
            selected_dates = st.date_input("Select your cycle:", value=(datetime.date.today().replace(day=1), datetime.date.today()))
            if len(selected_dates) == 2:
                start, end = selected_dates
                cycle_df = df[(df['Date'] >= start) & (df['Date'] <= end)]
            else: cycle_df = pd.DataFrame()
        else: # "Daily View"
            selected_day = st.date_input("Select a specific day:", value=datetime.date.today())
            cycle_df = df[df['Date'] == selected_day]    
            
            if not cycle_df.empty:
                tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Analytics Charts", "📋 Ledger History"])
                curr = st.session_state.currency
                
                with tab1:
                    inc = cycle_df[cycle_df['Type'] == 'Income']['Amount'].sum()
                    exp = cycle_df[cycle_df['Type'] == 'Expense']['Amount'].sum()
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Income", f"{curr}{inc:,.2f}")
                    col2.metric("Expenses", f"{curr}{exp:,.2f}")
                    col3.metric("Balance", f"{curr}{inc-exp:,.2f}")
                
                with tab2:
                    exp_df = cycle_df[cycle_df['Type'] == 'Expense']
                    if not exp_df.empty:
                        c1, c2 = st.columns(2)
                        fig1 = px.pie(exp_df, values='Amount', names='Category', hole=0.4, template="plotly_dark")
                        c1.plotly_chart(fig1, use_container_width=True, key="p1")
                        fig2 = px.line(exp_df.groupby('Date')['Amount'].sum().reset_index(), x='Date', y='Amount', template="plotly_dark")
                        c2.plotly_chart(fig2, use_container_width=True, key="p2")
                
                with tab3:
                    st.download_button("📥 Export CSV", cycle_df.to_csv(index=False), "vault.csv", "text/csv")
                    st.dataframe(cycle_df, use_container_width=True)
            else: st.info("No data in this cycle.")
    else: st.info("Add your first transaction!")

# --- CASE B: UNAUTHENTICATED ---
else:
    st.title("🌱 Personal Wealth Vault")
    auth_mode = st.radio("Access", ["Log In", "Create an Account"], horizontal=True)
    input_user = st.text_input("Username").strip()
    input_pass = st.text_input("Password", type="password")
    if st.button("Submit"):
        users_df = conn.read(worksheet="Users", ttl=0)
        users_df.columns = users_df.columns.str.strip()
        hashed = hashlib.sha256(input_pass.encode()).hexdigest()
        if auth_mode == "Log In":
            if not users_df[(users_df['Username'] == input_user) & (users_df['Password'].astype(str) == hashed)].empty:
                st.session_state.username = input_user
                st.rerun()
            else: st.error("Invalid credentials.")
        else:
            if input_user not in users_df['Username'].values:
                new_user = pd.DataFrame([{"Username": input_user, "Password": hashed}])
                conn.update(worksheet="Users", data=pd.concat([users_df, new_user]))
                st.success("Account created!")
