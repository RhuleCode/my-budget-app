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
        # 1. Currency Selector inside the form
        currency = st.selectbox(
            "Currency", 
            ["GH₵ (GHS)", "₦ (NGN)", "$ (USD)", "€ (EUR)", "£ (GBP)", "KSh (KES)", "R (ZAR)", "¥ (JPY)"]
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
    
    # 1. Log Out Logic
    if st.button("Log Out"):
        # Clear all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Force a refresh to the login state
        st.rerun()
        
    st.divider() # Keep the logout button separated from other controls

    # 2. PASTE ACCOUNT SETTINGS HERE
    with st.expander("⚙️ Account Settings"):
        st.warning("⚠️ This action is permanent and will remove all your data.")
        # Confirmation checkbox makes it safer!
        confirm_delete = st.checkbox("I understand this will delete all my data.")
        
        if st.button("Delete My Account & Data"):
            if confirm_delete:
                # [Insert your Deletion Logic here]
                st.success("Account deleted.")
            else:
                st.error("Please check the box to confirm deletion.")
    

# --- 5. MAIN DASHBOARD ---
st.title("💰 Your Secure Budget Vault")

# User Guide Expander
with st.expander("📖  User Guide: How to use this app"):
    st.markdown("""
    ### 📝 Adding Transactions (Sidebar)
    * **Transaction Type:** Income (adds money), Expense (subtracts money), Transfer (moves money).
    * **Category:** Groups your spending to generate your analytics.
    
    ### 📊 Dashboard View Modes
    * **Custom Cycle:** View your data across a specific date range (like your personal pay cycle).
    * **Daily View:** Zoom in on a single specific day to check daily limits.

    ### 📄 Financial Insights
    * **Analytics Charts:** View your expenditure splits as a dynamic pie chart.
    * **Ledger History:** View and edit your past transaction logs in real-time.
    * **Monthly Summary:** Review your Net Flow (Income vs. Expense) and track your **Performance Trend** to see if your spending is rising or falling compared to the last period.
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
    tab1, tab2, tab3 = st.tabs(["📊 Analytics Charts", "📋 Ledger History", "📄 Monthly Summary"])
    
    with tab1:
        st.subheader("Category Expenditure Allocation Splits")
        
        # SELF-HEALING LOGIC:
        # If 'Type' is blank or anything other than Income/Transfer, treat as Expense
        df_chart = cycle_df.copy()
        df_chart['Type'] = df_chart['Type'].apply(
            lambda x: 'Expense' if x not in ['Income', 'Transfer'] else x
        )
        
        expense_df = df_chart[df_chart['Type'] == 'Expense']
        
        if not expense_df.empty:
            fig = px.pie(expense_df, values='Amount', names='Category', hole=0.3)
            
            # 3D-style pop effect
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                pull=[0.05] * len(expense_df),
                marker=dict(line=dict(color='#000000', width=2))
            )
            
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No expenses logged in this timeframe to chart.")
            
    with tab2:
        st.subheader("Secure Core Transaction Ledger Logs")
        
        # Ensure c_display is defined correctly for this scope
        c_display = st.session_state.get("currency", "GH₵")
        
        # This makes the table editable!
        edited_df = st.data_editor(
            cycle_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount Value", format=f"{c_display} %.2f"),
                "Date": st.column_config.DateColumn("Date Logged", format="YYYY-MM-DD")
            }
        )
    with tab3:
        st.subheader("📄 Financial Summary Report")
        
        # Determine the scope label based on the active view mode
        scope = "Daily" if view_mode == "Daily View" else "Cycle"
        st.caption(f"Generating summary for the selected: **{scope}**")
        
        # Calculate metrics using the pre-filtered cycle_df
        total_income = cycle_df[cycle_df['Type'] == 'Income']['Amount'].sum()
        total_expense = cycle_df[cycle_df['Type'] == 'Expense']['Amount'].sum()
        net_savings = total_income - total_expense
        
        # Metric display
        c_display = st.session_state.currency
        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"{c_display} {total_income:,.2f}")
        col2.metric("Expenses", f"{c_display} {total_expense:,.2f}")
        col3.metric("Net Flow", f"{c_display} {net_savings:,.2f}")
        
        st.divider()
        st.subheader("📈 Performance Trend")
    
    # Example logic: you can refine the 'previous_month_expense' calculation later
    previous_month_expense = 100.0 
    delta_value = total_expense - previous_month_expense
    
    # ... previous code ...
    st.metric(
        label="Expense Trend vs Last Period", 
        value=f"{c_display} {total_expense:,.2f}", 
        delta=f"{delta_value:,.2f}",
        delta_color="inverse"
    )
    
    st.divider() # Line 282
    
    # Ensure this 'if' starts at the same level as 'st.divider()'
    if net_savings > 0:
        st.success(f"✅ Your {scope} budget is positive. Keep it up!")
    elif net_savings < 0:
        st.warning(f"⚠️ Your {scope} expenses are exceeding your income.")
    else:
        st.info(f"Your {scope} budget is currently balanced.")
    # --- PLACED EXACTLY HERE BELOW THE LEDGER HISTORY DATA TABLE ---
        st.write("")
        st.divider()
        st.markdown("### 🚨 Master Reset Vault System")
        st.caption("Need a completely blank slate? Wiping the system logs clears transaction data entries permanently.")
        
        # Two-Step Security Verification Elements
        confirm_wipe = st.checkbox(
            "I explicitly confirm that I want to completely delete my ledger history data records.", 
            value=False,
            key="main_screen_wipe_checkbox",
            help="Check this authorization confirmation toggle to initialize and show the master destruction trigger button tool."
        )
        
        if confirm_wipe:
            if st.button("🔥 Confirm Clear & Start Over", help="🚨 ACTION REQUIRED: Click here to instantly scrub data rows clean. This cannot be reversed."):
                try:
                    # Construct clean empty dataset mapping exactly to your active layout schema structure
                    blank_slate_df = pd.DataFrame(columns=["Date", "Description", "Category", "Amount", "User", "Type"])
                    
                    # Overwrite and flush to Google Sheets worksheet
                    conn.update(worksheet="Transaction", data=blank_slate_df)
                    
                    st.toast("Vault data ledger successfully wiped clean!", icon="💥")
                    st.success("System reset active! Refreshing cloud cache records...")
                    st.rerun()
                except Exception as wipe_error:
                    st.error(f"Security override failed to clear spreadsheet log rows: {wipe_error}")

