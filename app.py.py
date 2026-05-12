import streamlit as st
from bud import Category, create_spend_chart

st.set_page_config(page_title="Budget App", layout="wide")
st.title("💰 My Personal Budget App")

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