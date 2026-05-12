import streamlit as st
from bud import Category, create_spend_chart
import plotly.express as px  # 
import pandas as pd          # 
st.set_page_config(
    page_title="Rhule's Budget Dashboard", 
    page_icon="💰", 
    layout="wide"
)
st.title("💰 My Personal Budget App")

# --- ADD THIS SECTION ---
st.markdown("""
### Welcome to your financial dashboard!
This application helps you manage your money using **Category-based budgeting**. 
* **Create** custom categories like Food, Rent, or Entertainment.
* **Track** deposits and withdrawals with detailed descriptions.
* **Analyze** your spending habits with an automated visual chart.
""")
st.divider()

    
    # --- PRO CHART SECTION ---
    # 1. First, check if categories even exist
if 'categories' in st.session_state and st.session_state.categories:
        st.subheader("📊 Spending Breakdown")
        
        # 2. Prepare the data
        chart_data = {
            "Category": [cat.name for cat in st.session_state.categories.values()],
            "Spent": [sum(-item['amount'] for item in cat.ledger if item['amount'] < 0) 
                      for cat in st.session_state.categories.values()]
        }
        
        # 3. Only draw the chart if money has actually been spent
        if sum(chart_data["Spent"]) > 0:
            fig = px.pie(chart_data, values='Spent', names='Category', hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Tip: Add a 'Withdrawal' to see your spending breakdown here!")

# ------------------------

# Initialize data storage
if 'categories' not in st.session_state:
    st.session_state.categories = {}

# Sidebar for adding categories
with st.sidebar:
    st.header("Settings")
    name = st.text_input("Category Name")
    if st.button("Add Category"):
        if name and name not in st.session_state.categories:
            st.session_state.categories[name] = Category(name)
            st.success(f"Added {name}")
    st.divider()
    st.info("""
    **Project Info:** Built with Python & Streamlit.  
    Logic based on the *freeCodeCamp* Budget App certification.
    """)

# Main app logic
if st.session_state.categories:
    cat_list = list(st.session_state.categories.keys())
    choice = st.selectbox("Select Category", cat_list)
    obj = st.session_state.categories[choice]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Transactions")
        amount = st.number_input("Amount", min_value=0.0)
        desc = st.text_input("Description")
        if st.button("Deposit"):
            obj.deposit(amount, desc)
            st.rerun()
        if st.button("Withdraw"):
            if obj.withdraw(amount, desc):
                st.rerun()
            else:
                st.error("Insufficient Funds!")

    with col2:
        st.subheader("Ledger View")
        st.code(str(obj)) # This runs your FCC __str__ code!
    
    st.divider()
    if st.button("Generate Spend Chart"):
        chart = create_spend_chart(list(st.session_state.categories.values()))
        st.code(chart)
else:
    st.info("👈 Use the sidebar to add your first category (e.g., Food, Rent)!")
