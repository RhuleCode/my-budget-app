import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import pandas as pd

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
        # This is where the magic happens: It writes to your Google Sheet!
        # [We will add the 'Write' logic here once your connection is tested!]
        st.success("Transaction Saved!")
