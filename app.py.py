import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
from streamlit_gsheets import GSheetsConnection

# --- 1. INITIAL SETUP & CONNECTION ---
st.set_page_config(page_title="Secure Budget Vault", layout="wide")

# Initialize your Google Sheets connection correctly
conn = st.connection("gsheets", type=GSheetsConnection)
# --- 2. AUTHENTICATION GATING ---
# CASE A: THE USER IS LOGGED IN -> Show the entire functional application
if "username" in st.session_state:
    
    # --- SIDEBAR CONTENT (ONLY FOR LOGGED-IN USERS) ---
    with st.sidebar:
        st.header(f"👋 Welcome, {st.session_state.username}!")
        st.subheader("📝 Add Transaction")
        
        new_date = st.date_input("Date")
        new_desc = st.text_input("Description")
        new_cat = st.text_input("Category Name")
        new_amt = st.number_input("Amount", value=0.0, step=1.0)
        
        if st.button("Save to Vault"):
            if new_cat and new_amt > 0:
                new_entry = pd.DataFrame([{
                    "Date": str(new_date),
                    "Description": new_desc,
                    "Category": new_cat,
                    "Amount": new_amt,
                    "User": st.session_state.username
                }])
                all_data = conn.read(worksheet="Transaction", ttl=0)
                updated_vault = pd.concat([all_data, new_entry], ignore_index=True)
                conn.update(worksheet="Transaction", data=updated_vault)
                st.success(f"✅ Saved {new_cat} transaction!")
                st.rerun()
            else:
                st.warning("Please enter a valid category name and an amount greater than 0.")
                
        st.divider()
        if st.button("Log Out"):
            del st.session_state["username"]
            st.rerun()

    # --- MAIN DASHBOARD CONTENT (ONLY FOR LOGGED-IN USERS) ---
    st.title("💰 Your Secure Budget Vault")
    
    all_data = conn.read(worksheet="Transaction", ttl=0)
    df = all_data[all_data['User'] == st.session_state.username]
    
    if not df.empty:
        st.subheader("📊 Your Financial Summary")
        
        # Calculate Metrics
        total_spending = df['Amount'].sum()
        total_transactions = len(df)
        avg_spending = df['Amount'].mean() if total_transactions > 0 else 0.0
        
        # Display Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Expenses", value=f"${total_spending:,.2f}")
        with col2:
            st.metric(label="Transactions Logged", value=f"{total_transactions}")
        with col3:
            st.metric(label="Average Spend", value=f"${avg_spending:,.2f}")
            
        st.divider()
        
        # Charts & Dataframe
        st.subheader("🍕 Spending Breakdown")
        fig = px.pie(df, values='Amount', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Transaction History")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your vault is currently empty. Add your first transaction in the sidebar!")

# CASE B: NO ONE IS LOGGED IN -> Show a full-screen welcome and auth interface
else:
    # Main screen splash layout
    st.title("🔒 Cyber Financial Vault")
    
    st.markdown(
        """
        <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; margin-bottom: 25px; border-left: 5px solid #3B82F6;">
            <h3 style="color: #F8FAFC; margin-top: 0;">🛡️ System Access Required</h3>
            <p style="color: #94A3B8; font-size: 15px; line-height: 1.6;">
                Welcome to the independent financial tracking vault. To protect your ledger integrity, all data vectors are cryptographically isolated. Please create an encrypted vault identity or authenticate below to decrypt your dashboard workspace.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Center the login panel cleanly on the main workspace
    auth_col, _ = st.columns([2, 1])
    
    with auth_col:
        auth_mode = st.radio("Access Level Token", ["Log In", "Sign Up"], horizontal=True)
        
        input_user = st.text_input("Vault Username").strip()
        input_pass = st.text_input("Master Password", type="password")
        
        # --- AUTOMATED LOGIN PROCESSING ---
        if auth_mode == "Log In":
            if st.button("Decrypt & Enter Vault"):
                if input_user and input_pass:
                    users_df = conn.read(worksheet="Users", ttl=0)
                    users_df.columns = users_df.columns.str.strip()
                    
                    hashed_input_pass = hashlib.sha256(input_pass.encode()).hexdigest()
                    
                    match = users_df[
                        (users_df['Username'] == input_user) & 
                        (users_df['Password'].astype(str) == hashed_input_pass)
                    ]
                    
                    if not match.empty:
                        st.session_state.username = input_user
                        st.success("🔓 Access Granted. Syncing dashboard matrix...")
                        st.rerun()
                    else:
                        st.error("❌ Access Denied: Invalid credentials profile.")
                else:
                    st.warning("Both verification criteria fields must be populated.")
                    
        # --- AUTOMATED SIGN UP PROCESSING ---
        elif auth_mode == "Sign Up":
            if st.button("Provision New Vault Account"):
                if input_user and input_pass:
                    users_df = conn.read(worksheet="Users", ttl=0)
                    users_df.columns = users_df.columns.str.strip()
                    
                    if input_user in users_df['Username'].values:
                        st.error("⚠️ Conflict: Username identity already registered in database.")
                    else:
                        # Automate the background hashing write
                        hashed_new_pass = hashlib.sha256(input_pass.encode()).hexdigest()
                        
                        new_user_entry = pd.DataFrame([{
                            "Username": input_user,
                            "Password": hashed_new_pass
                        }])
                        
                        updated_users = pd.concat([users_df, new_user_entry], ignore_index=True)
                        conn.update(worksheet="Users", data=updated_users)
                        
                        st.success("🎉 Vault provisioned! Toggle option to 'Log In' to clear security checking.")
                else:
                    st.warning("Both registration criteria fields must be populated.")
