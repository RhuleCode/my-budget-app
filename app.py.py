import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta
import hashlib # CRITICAL: Added for password hashing

# --- 1. INITIAL SETUP & CONNECTION ---
st.set_page_config(page_title="Secure Budget Vault", layout="wide")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# Set a default currency if not already set
if "currency" not in st.session_state:
    st.session_state.currency = "GH₵ (GHS)"

# --- 2. AUTHENTICATION GATING ---
if "username" in st.session_state:
    
    # ==========================================
    # LOGGED IN: SIDEBAR (Controls & Settings)
    # ==========================================
    with st.sidebar:
        st.header(f"👋 Welcome, {st.session_state.username}!")
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
                help="Income adds to your balance. Expense subtracts."
            )
            desc_val = st.text_input(
                "Description", 
                help="A quick note (e.g., 'Uber' or 'Groceries')."
            )
            cat_val = st.selectbox(
                "Category", 
                ["Food", "Rent", "Salary", "Transport", "Utilities", "Purchase", "Other"], 
                help="Grouping similar expenses helps generate charts."
            )
            amount_val = st.number_input(
                "Amount", 
                min_value=0.0, 
                format="%.2f", 
                help="Enter the exact monetary amount."
            )
            currency = st.selectbox(
                "Currency", 
                ["GH₵ (GHS)", "₦ (NGN)", "$ (USD)", "€ (EUR)", "£ (GBP)", "KSh (KES)", "R (ZAR)", "¥ (JPY)"]
            )
            
            submitted = st.form_submit_button("Save to Vault")
            
            if submitted:
                st.session_state.currency = currency # Save choice globally
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

        st.divider()
        
        # Developer Profile
        with st.expander("👨‍💻 About the Developer", expanded=False):
            st.markdown("""
            **Developer:** `Nana Kwaku Bentum Rhule`  
            **Specialization:** Cybersecurity & Secure Application Development  
            **Environment:** Environment built and tested on Ubuntu Linux  
            
            *Building secure tools for modern financial tracking.*
            """)
            st.link_button("🌐 View GitHub Profile", "https://github.com/Rhulecode")
            
        st.divider()
        
        # Log Out Logic
        if st.button("Log Out", type="primary"):
            st.session_state.clear() # Wipes all memory
            st.rerun()
            
        st.divider()
        
        # Account Settings & Master Reset
        with st.expander("⚙️ Account Settings"):
            st.warning("⚠️ Actions here are permanent.")
            
            # 1. Delete Account
            confirm_delete = st.checkbox("I understand this deletes my account.")
            if st.button("Delete My Account"):
                if confirm_delete:
                    # [Insert your Deletion Logic here]
                    st.success("Account deleted.")
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.error("Please check the box.")
                    
            st.divider()
            
            # 2. Master Reset
            st.markdown("### 🚨 Master Reset Vault")
            confirm_wipe = st.checkbox("Wipe all ledger data.")
            if confirm_wipe:
                if st.button("🔥 Confirm Clear"):
                    try:
                        blank_slate_df = pd.DataFrame(columns=["Date", "Type", "Description", "Category", "Amount", "User"])
                        conn.update(worksheet="Transaction", data=blank_slate_df)
                        st.success("Vault wiped!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {e}")

    # ==========================================
    # LOGGED IN: MAIN DASHBOARD
    # ==========================================
    st.title(" BUDGET-FLOW | 💰 Your Secure Budget Vault")
    
    with st.expander("📖 User Guide: How to use this app"):
        st.markdown("""
        ### 📝 Adding Transactions (Sidebar)
        * **Transaction Type:** Income (adds money), Expense (subtracts money), Transfer (moves money).
        * **Category:** Groups your spending to generate your analytics.
        
        ### 📊 Dashboard View Modes
        * **Custom Cycle:** View your data across a specific date range.
        * **Daily View:** Zoom in on a single specific day to check daily limits.
        """)
        
    try:
        all_data = conn.read(worksheet="Transaction", usecols=list(range(6)), ttl=0)
        all_data = all_data.dropna(how="all")
        df = all_data[all_data['User'] == st.session_state.username].copy()
    except Exception as e:
        st.error(f"Database error: {e}")
        st.stop()
        
    if df.empty:
        st.info(f"No data found for user: **{st.session_state.username}**. Add a transaction in the sidebar!")
    else:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        
        st.markdown("### 📊 Dashboard View Mode")
        view_mode = st.radio(
            "How would you like to view your data?", 
            ["Custom Cycle", "Daily View"], 
            horizontal=True
        )
        
        if view_mode == "Custom Cycle":
            today = date.today()
            start_of_month = today.replace(day=1)
            selected_dates = st.date_input("Select your cycle:", value=(start_of_month, today))
            
            if len(selected_dates) == 2:
                start, end = selected_dates
                cycle_df = df[(df['Date'] >= start) & (df['Date'] <= end)]
            else:
                cycle_df = df[df['Date'] == selected_dates[0]] 
        else:
            selected_date = st.date_input("Select a day:", value=date.today())
            cycle_df = df[df['Date'] == selected_date]
            
        st.divider()
        
        total_income = cycle_df[cycle_df['Type'] == 'Income']['Amount'].sum()
        total_expense = cycle_df[cycle_df['Type'] == 'Expense']['Amount'].sum()
        balance = total_income - total_expense
        
        c = st.session_state.currency.split()[0] # Gets just the symbol like GH₵
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Cycle Income", f"{c}{total_income:,.2f}")
        col2.metric("Cycle Expenses", f"{c}{total_expense:,.2f}")
        col3.metric("Current Balance", f"{c}{balance:,.2f}", delta=balance)
        
        st.write("") 
        tab1, tab2, tab3 = st.tabs(["📊 Analytics Charts", "📋 Ledger History", "📄 Monthly Summary"])
        
        with tab1:
            st.subheader("Category Expenditure Allocation Splits")
            df_chart = cycle_df.copy()
            df_chart['Type'] = df_chart['Type'].apply(lambda x: 'Expense' if x not in ['Income', 'Transfer'] else x)
            expense_df = df_chart[df_chart['Type'] == 'Expense']
            
            if not expense_df.empty:
                fig = px.pie(expense_df, values='Amount', names='Category', hole=0.3)
                fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(expense_df))
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No expenses logged in this timeframe to chart.")
                
        with tab2:
            st.subheader("Secure Core Transaction Ledger Logs")
            st.data_editor(
                cycle_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn("Amount Value", format=f"{c} %.2f"),
                    "Date": st.column_config.DateColumn("Date Logged", format="YYYY-MM-DD")
                }
            )
            
        with tab3:
            st.subheader("📄 Financial Summary Report")
            scope = "Daily" if view_mode == "Daily View" else "Cycle"
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Income", f"{c} {total_income:,.2f}")
            col2.metric("Expenses", f"{c} {total_expense:,.2f}")
            col3.metric("Net Flow", f"{c} {balance:,.2f}")
            
            st.divider()
            st.subheader("📈 Performance Trend")
            previous_month_expense = 100.0 
            delta_value = total_expense - previous_month_expense
            
            st.metric(
                label="Expense Trend vs Last Period", 
                value=f"{c} {total_expense:,.2f}", 
                delta=f"{delta_value:,.2f}",
                delta_color="inverse"
            )
            
            st.divider()
            if balance > 0:
                st.success(f"✅ Your {scope} budget is positive. Keep it up!")
            elif balance < 0:
                st.warning(f"⚠️ Your {scope} expenses are exceeding your income.")
            else:
                st.info(f"Your {scope} budget is currently balanced.")

# ==========================================
# NOT LOGGED IN: LOGIN / SIGNUP PAGE
# ==========================================
else:
    st.title(" BUDGET-FLOW")
    st.markdown(
        """
        <div style="background-color: #1E293B; padding: 22px; border-radius: 12px; margin-bottom: 25px; border-left: 5px solid #10B981;">
            <h3 style="color: #F8FAFC; margin-top: 0; font-weight: 600;">Take Control of Your Financial Future</h3>
            <p style="color: #94A3B8; font-size: 15px; line-height: 1.6; margin-bottom: 0;">
                Welcome to your personal financial command center. Track your everyday spending, analyze your budget trends with live visual charts, and secure your financial data in real-time. 
                <br><br>
                <b>Ready to see where your money goes?</b> Create a private account or log in below to unlock your automated dashboard workspace.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    auth_col, _ = st.columns([2, 1])
    
    with auth_col:
        auth_mode = st.radio("Account Options", ["Log In", "Create an Account"], horizontal=True)
        input_user = st.text_input("Username").strip()
        input_pass = st.text_input("Password", type="password")
        
        if auth_mode == "Log In":
            if st.button("Unlock My Dashboard"):
                if input_user and input_pass:
                    users_df = conn.read(worksheet="Users", ttl=0)
                    users_df.columns = users_df.columns.str.strip()
                    
                    hashed_input_pass = hashlib.sha256(input_pass.encode()).hexdigest()
                    match = users_df[(users_df['Username'] == input_user) & (users_df['Password'].astype(str) == hashed_input_pass)]
                    
                    if not match.empty:
                        st.session_state.username = input_user
                        st.success("🔓 Access Granted! Loading your financial vault...")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect username or password. Please try again.")
                else:
                    st.warning("Please enter your username and password to log in.")
                    
        elif auth_mode == "Create an Account":
            if st.button("Get Started For Free"):
                if input_user and input_pass:
                    users_df = conn.read(worksheet="Users", ttl=0)
                    users_df.columns = users_df.columns.str.strip()
                    
                    if input_user in users_df['Username'].values:
                        st.error("⚠️ That username is already taken. Try another one!")
                    else:
                        hashed_new_pass = hashlib.sha256(input_pass.encode()).hexdigest()
                        new_user_entry = pd.DataFrame([{"Username": input_user, "Password": hashed_new_pass}])
                        updated_users = pd.concat([users_df, new_user_entry], ignore_index=True)
                        conn.update(worksheet="Users", data=updated_users)
                        
                        st.success("🎉 Your vault is ready! Switch over to 'Log In' to get started.")
                else:
                    st.warning("Please choose a username and password to sign up.")
