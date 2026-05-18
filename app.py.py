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
        
        # --- NEW CATCHY VISUAL CAPTION ---
        st.markdown(
            """
            <div style="background-color: #0F172A; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 3px solid #10B981;">
                <p style="color: #94A3B8; font-size: 13px; line-height: 1.4; margin: 0;">
                    💡 <b>Vault Ledger Entry:</b> Use the form below to document an expense. Submitting will instantly encrypt the transaction records and sync them directly to your private backend database.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
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
    # Initialize onboarding step for first-time users if not already present
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1  # Start at step 1 for a fresh login session

    # --- AUTOMATED FEATURE HIGHLIGHT TOUR ---
    # This banner will guide them through 3 quick steps and then disappear forever!
    if st.session_state.onboarding_step <= 3:
        if st.session_state.onboarding_step == 1:
            st.markdown(
                """
                <div style="background-color: #1E293B; padding: 18px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 20px;">
                    <h4 style="color: #F8FAFC; margin-top:0;">🚀 Step 1 of 3: The Transaction Sidebar</h4>
                    <p style="color: #94A3B8; font-size: 14px; margin-bottom: 10px;">
                        Look over to the left! The sidebar is your data entry command station. Whenever you spend money, type the category and amount there, hit save, and watch your cloud ledger update instantly.
                    </p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Next Tip ➡️", key="tour_1"):
                st.session_state.onboarding_step = 2
                st.rerun()

        elif st.session_state.onboarding_step == 2:
            st.markdown(
                """
                <div style="background-color: #1E293B; padding: 18px; border-radius: 10px; border-left: 5px solid #10B981; margin-bottom: 20px;">
                    <h4 style="color: #F8FAFC; margin-top:0;">📊 Step 2 of 3: Live Summary Cards</h4>
                    <p style="color: #94A3B8; font-size: 14px; margin-bottom: 10px;">
                        Right below this banner, you will find your high-level financial health cards. They automatically calculate your total expenses, transaction velocity, and average spending habits on the fly.
                    </p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Next Tip ➡️", key="tour_2"):
                st.session_state.onboarding_step = 3
                st.rerun()

        elif st.session_state.onboarding_step == 3:
            st.markdown(
                """
                <div style="background-color: #1E293B; padding: 18px; border-radius: 10px; border-left: 5px solid #F59E0B; margin-bottom: 20px;">
                    <h4 style="color: #F8FAFC; margin-top:0;">🍕 Step 3 of 3: Interactive Analytics</h4>
                    <p style="color: #94A3B8; font-size: 14px; margin-bottom: 10px;">
                        Scroll down to find your interactive breakdown pie chart and raw history table. You can hover over the slices to look into specific budget slices or sort the table rows directly.
                    </p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Got it, Let's Go! 🎉", key="tour_3"):
                st.session_state.onboarding_step = 4  # Moves past 3, hiding the tour completely
                st.rerun()
    
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
    # 1. Catchy, welcoming title
    st.title("🌱 Personal Wealth Vault")
    
    # 2. Convincing, non-technical introduction card
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
    
    # Center the auth panel cleanly on the main workspace
    auth_col, _ = st.columns([2, 1])
    
    with auth_col:
        # User-friendly toggle phrasing
        auth_mode = st.radio("Account Options", ["Log In", "Create an Account"], horizontal=True)
        
        input_user = st.text_input("Username").strip()
        input_pass = st.text_input("Password", type="password")
        
        # --- AUTOMATED LOGIN PROCESSING ---
        if auth_mode == "Log In":
            if st.button("Unlock My Dashboard"):
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
                        st.success("🔓 Access Granted! Loading your financial vault...")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect username or password. Please try again.")
                else:
                    st.warning("Please enter your username and password to log in.")
                    
        # --- AUTOMATED SIGN UP PROCESSING ---
        elif auth_mode == "Create an Account":
            if st.button("Get Started For Free"):
                if input_user and input_pass:
                    users_df = conn.read(worksheet="Users", ttl=0)
                    users_df.columns = users_df.columns.str.strip()
                    
                    if input_user in users_df['Username'].values:
                        st.error("⚠️ That username is already taken. Try another one!")
                    else:
                        hashed_new_pass = hashlib.sha256(input_pass.encode()).hexdigest()
                        
                        new_user_entry = pd.DataFrame([{
                            "Username": input_user,
                            "Password": hashed_new_pass
                        }])
                        
                        updated_users = pd.concat([users_df, new_user_entry], ignore_index=True)
                        conn.update(worksheet="Users", data=updated_users)
                        
                        st.success("🎉 Your vault is ready! Switch over to 'Log In' to get started.")
                else:
                    st.warning("Please choose a username and password to sign up.")
    # CASE B: NO ONE IS LOGGED IN -> Show a clean, premium landing and auth interface
   
