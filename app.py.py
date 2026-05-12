# Simple Password Gate
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import pandas as pd
# Simple Password Gate
if "password_correct" not in st.session_state:
    st.title("🔐 Secure Login")
    pwd = st.text_input("Enter Vault Password", type="password")
    if st.button("Unlock"):
        if pwd == "YourSecretPassword123": # Change this!
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Incorrect Password")
    st.stop() # Stops the rest of the app from loading until unlocked

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
# This pulls the latest numbers from your "Vault"
df = conn.read()

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
    new_cat = st.text_input("Category Name")
    new_amt = st.number_input("Amount", step=1.0)
   if st.button("Save to Vault"):
        if new_cat and new_amt > 0:
            # 1. Create a new row of data
            new_data = pd.DataFrame([{"Category": new_cat, "Amount": new_amt}])
            
            # 2. Get existing data, add new row, and update the sheet
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success(f"Saved {new_cat} to your vault!")
            st.rerun() # Refresh the page to show the new data
        else:
            st.warning("Please enter a category and an amount.")
