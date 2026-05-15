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
# Load only the transaction data
all_data = conn.read(worksheet="Transaction")

# Filter: "Show me only the rows where the 'User' column matches my username"
df = all_data[all_data['User'] == st.session_state.username]
if not df.empty:
    st.subheader("📊 Your Spending Overview")
    
    # Create the Pie Chart using the data from the Google Sheet
    fig = px.pie(df, values='Amount', names='Category', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show the raw ledger
    st.dataframe(df, use_container_width=True)
else:
    st.info("Your vault is currently empty. Add your first transaction in the sidebar!")

# --- 4. SIDEBAR (ADDING DATA) ---
with st.sidebar:
    st.header("Add Transaction")
    # Add the missing inputs to match your sheet headers
    new_date = st.date_input("Date")
    new_desc = st.text_input("Description")
    new_cat = st.text_input("Category Name")
    new_amt = st.number_input("Amount", step=1.0)

    if st.button("Save to Vault"):
        if new_cat and new_amt > 0:
            # 1. Create a row that matches ALL your sheet columns
            new_data = pd.DataFrame([{
                "Date": str(new_date),
                "Description": new_desc,
                "Category": new_cat,
                "Amount": new_amt,
                "User": st.session_state.username  # Keep data private!
            }])

            # 2. Make sure you are reading from and updating the "Transaction" tab
            # You might need: df = conn.read(worksheet="Transaction") before this
            updated_df = pd.concat([df, new_data], ignore_index=True)
            
            # CRITICAL: Specify the worksheet so it doesn't overwrite your "Users" tab
            conn.update(worksheet="Transaction", data=updated_df)
            
            st.success(f"Saved {new_cat} to your vault!")
            st.rerun()
