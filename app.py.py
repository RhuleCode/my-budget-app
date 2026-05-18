import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
#1. BUILD THE CONNECTION FIRST
conn = st.connection("gsheets", type=GSheetsConnection)
# Simple Password Gate
# Create a toggle for Login vs Sign Up

if "password_correct" not in st.session_state:
    mode = st.radio("Choose an option", ["Login", "Sign Up"], horizontal=True)

    st.title(f"🔐 {mode}")
    
    new_user = st.text_input("Username")
    new_pwd = st.text_input("Password", type="password")

    if mode == "Sign Up":
        if st.button("Create Account"):
            try:
                user_df = conn.read(worksheet="Users", ttl=0)
            except Exception:
                # If the sheet is totally empty, create a blank table
                user_df = pd.DataFrame(columns=['Username', 'Password'])
            
            # 2. Check if username exists
            if new_user in user_df['Username'].values:
                st.error("Username already exists!")
            elif new_user and new_pwd:
                # 3. Add to the sheet
                new_acc = pd.DataFrame([{"Username": new_user, "Password": new_pwd}])
                updated_users = pd.concat([user_df, new_acc], ignore_index=True)
                conn.update(worksheet="Users", data=updated_users)
                st.success("Account created! Now switch to 'Login'.")
            else:
                st.warning("Please fill in both fields.")

    elif mode == "Login":
        if st.button("Unlock"):
            # Load users to check credentials
            user_df = conn.read(worksheet="Users")
            
            # Check if the combo exists in your sheet
            if ((user_df['Username'] == new_user) & (user_df['Password'] == new_pwd)).any():
                st.session_state["password_correct"] = True
                st.session_state["current_user"] = new_user # Remember who logged in!
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    st.stop()

# --- 1. SETTINGS & STORAGE ---
st.set_page_config(page_title="Secure Budget Vault", page_icon="💰", layout="wide")

# This connects to the Secret URL you put in the Streamlit Dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. THE DESCRIPTION ---
st.markdown("""
### Welcome to your Secure Financial Dashboard!
*   **Encrypted:** Your data is stored in your private Google Sheet.
*   **Persistent:** Your balance stays saved even after you log out.
""")
st.divider()

# --- 3. LOADING DATA ---
# --- 3. LOADING & DISPLAYING DATA ---
# Everything inside this block only runs IF a user is successfully logged in
if "username" in st.session_state:
    
    # 1. Load the data cleanly from the Google Sheet
    all_data = conn.read(worksheet="Transaction", ttl=0)
    
    # 2. Filter data for the logged-in user
    df = all_data[all_data['User'] == st.session_state.username]
    
    # 3. Display the dashboard elements safely using the filtered 'df'
    if not df.empty:
        st.subheader("📊 Your Spending Overview")
        
        # Create and display the Pie Chart
        fig = px.pie(df, values='Amount', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show the raw transaction ledger
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your vault is currently empty. Add your first transaction in the sidebar!!![Tap the ' >> ' arrow in the top-left corner to open the authentication vault.]")

else:
    # This runs cleanly when no one is logged in yet, preventing any NameErrors
    st.info("🔒 Please log in or sign up in the sidebar to access your secure financial vault.")
# --- 4. SIDEBAR (ADDING DATA) ---
# --- 4. SIDEBAR (ADDING DATA & AUTH) ---
# --- 4. SIDEBAR (ADDING DATA & AUTH) ---
with st.sidebar:
    if "username" in st.session_state:
        st.header(f"👋 Welcome, {st.session_state.username}!")
        st.subheader("📝 Add Transaction")
        
        # Inputs matching your Google Sheet columns perfectly
        new_date = st.date_input("Date")
        new_desc = st.text_input("Description")
        new_cat = st.text_input("Category Name")
        new_amt = st.number_input("Amount", value=0.0, step=1.0)
        
        if st.button("Save to Vault"):
            if new_cat and new_amt > 0:
                # 1. Build a new row containing all 5 necessary ledger attributes
                new_entry = pd.DataFrame([{
                    "Date": str(new_date),
                    "Description": new_desc,
                    "Category": new_cat,
                    "Amount": new_amt,
                    "User": st.session_state.username
                }])
                
                # 2. Pull the entire transaction history from the sheet safely
                all_data = conn.read(worksheet="Transaction", ttl=0)
                
                # 3. Merge the new entry into the dataset safely
                updated_vault = pd.concat([all_data, new_entry], ignore_index=True)
                
                # 4. Write the structural data back to your Google Sheet
                conn.update(worksheet="Transaction", data=updated_vault)
                st.success(f"✅ Saved {new_cat} transaction!")
                st.rerun()
            else:
                st.warning("Please enter a valid category name and an amount greater than 0.")
                
        # Simple logout option
        st.divider()
        if st.button("Log Out"):
            del st.session_state["username"]
            st.rerun()
            
    else:
        # --- MAIN PAGE INITIALIZATION ---
        st.title("💰 Secure Budget Vault")
        
        # Check if user needs to authenticate, and show an explicit hint banner
    if "username" not in st.session_state:
        # --- WELCOME CARD FOR NEW USERS ---
        st.markdown(
            """
            <div style="background-color: #1E293B; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3B82F6;">
                <h4 style="color: #F8FAFC; margin-top: 0;">🛡️ Welcome to the Vault</h4>
                <p style="color: #94A3B8; font-size: 14px; line-height: 1.5; margin-bottom: 0;">
                    This is your personal secure financial workspace. Authenticate to unlock your live spending analysis, update your ledgers, and manage your financial records securely.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.header("🔐 Vault Authentication")
        
        # 1. Login input fields
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        
        if st.button("Log In"):
            if input_user and input_pass:
                # 2. Fetch the credentials database from your 'Users' sheet
                users_df = conn.read(worksheet="Users", ttl=0)
                
                # Clean up column names just in case there are hidden spaces
                users_df.columns = users_df.columns.str.strip()
                
                # 3. Match inputs against the sheet data
                match = users_df[(users_df['Username'] == input_user) & (users_df['Password'].astype(str) == str(input_pass))]
                
                if not match.empty:
                    # Success! Save user to session state and reload the interface
                    st.session_state.username = input_user
                    st.success(f"Welcome back, {input_user}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password.")
            else:
                st.warning("Please fill in both fields.")
