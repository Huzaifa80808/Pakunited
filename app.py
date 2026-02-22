import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os
import json

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Medical Store",
    page_icon="🏥",
    layout="wide"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    h1 { color: #2E86AB; }
    .stButton > button {
        background-color: #2E86AB;
        color: white;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #A23B72;
    }
    .login-container {
        max-width: 400px;
        margin: 5rem auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SUPABASE CONNECTION
# ============================================
from st_supabase_connection import SupabaseConnection

@st.cache_resource
def init_supabase():
    try:
        return st.connection("supabase", type=SupabaseConnection)
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

# ============================================
# SESSION STATE
# ============================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.current_shift = None

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #2E86AB;">🏥 Medical Store Login</h2>', unsafe_allow_html=True)
    
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            conn = init_supabase()
            if conn:
                try:
                    response = conn.table("users").select("*").eq("username", username).eq("password", password).execute()
                    if response.data:
                        user = response.data[0]
                        st.session_state.authenticated = True
                        st.session_state.user_role = user['role']
                        st.session_state.username = user.get('full_name', username)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except:
                    st.error("Login failed")
    
    st.info("Demo: admin/admin123 or owner/owner123")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN DASHBOARD
# ============================================
def dashboard():
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role.upper()}")
        st.markdown("---")
        
        menu = ["Record Entry", "Reports", "Ledgers"]
        if st.session_state.user_role == 'admin':
            menu.append("Settings")
        
        choice = st.radio("Menu", menu)
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    if choice == "Record Entry":
        show_record_entry()
    elif choice == "Reports":
        show_reports()
    elif choice == "Ledgers":
        show_ledgers()
    elif choice == "Settings":
        show_settings()

# ============================================
# RECORD ENTRY
# ============================================
def show_record_entry():
    st.title("📝 Record Entry")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌅 Morning", use_container_width=True):
            st.session_state.current_shift = "Morning"
    with col2:
        if st.button("☀️ Evening", use_container_width=True):
            st.session_state.current_shift = "Evening"
    with col3:
        if st.button("🌙 Night", use_container_width=True):
            st.session_state.current_shift = "Night"
    
    if st.session_state.current_shift:
        st.subheader(f"{st.session_state.current_shift} Shift")
        
        with st.form("entry_form"):
            date_input = st.date_input("Date", date.today())
            
            st.markdown("### 💰 Sales")
            col1, col2, col3 = st.columns(3)
            with col1:
                cash = st.number_input("Cash", min_value=0.0)
            with col2:
                upi = st.number_input("UPI", min_value=0.0)
            with col3:
                card = st.number_input("Card", min_value=0.0)
            
            st.markdown("### 💸 Expenses")
            num_exp = st.number_input("Number of Expenses", 0, 5, 0)
            expenses = []
            for i in range(num_exp):
                col1, col2 = st.columns(2)
                with col1:
                    amt = st.number_input(f"Amount {i+1}", key=f"exp_amt_{i}")
                with col2:
                    src = st.selectbox(f"Source {i+1}", ["Sales", "Pocket"], key=f"exp_src_{i}")
                if amt > 0:
                    expenses.append({"amount": amt, "source": src.lower()})
            
            st.markdown("### 🏧 Withdrawal")
            withdraw = st.number_input("Withdrawal Amount", 0.0)
            
            if st.form_submit_button("Save"):
                conn = init_supabase()
                if conn:
                    try:
                        shift_id = conn.table("shifts").select("id").eq("shift_name", st.session_state.current_shift).execute().data[0]['id']
                        
                        shift_data = {
                            'shift_id': shift_id,
                            'date': date_input.isoformat(),
                            'cash_sales': cash,
                            'upi_sales': upi,
                            'card_sales': card,
                            'closing_cash': cash - sum(e['amount'] for e in expenses if e['source'] == 'sales') - withdraw
                        }
                        
                        conn.table("daily_shifts").insert(shift_data).execute()
                        st.success("✅ Saved!")
                        st.session_state.current_shift = None
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================
# REPORTS
# ============================================
def show_reports():
    st.title("📊 Reports")
    
    report_type = st.selectbox("Report Type", ["Daily Summary", "Expense Summary"])
    start = st.date_input("From", date.today() - timedelta(days=30))
    end = st.date_input("To", date.today())
    
    conn = init_supabase()
    if not conn:
        return
    
    if report_type == "Daily Summary":
        try:
            response = conn.table("daily_shifts").select("*, shifts(shift_name)").gte("date", start.isoformat()).lte("date", end.isoformat()).execute()
            if response.data:
                df = pd.DataFrame(response.data)
                df['shift'] = df['shifts'].apply(lambda x: x['shift_name'] if x else 'Unknown')
                df['total'] = df['cash_sales'] + df['upi_sales'] + df['card_sales']
                
                st.dataframe(df[['date', 'shift', 'cash_sales', 'upi_sales', 'card_sales', 'total', 'closing_cash']])
                
                fig = px.bar(df, x='date', y='total', title="Daily Sales")
                st.plotly_chart(fig)
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================
# LEDGERS
# ============================================
def show_ledgers():
    st.title("📒 Ledgers")
    
    tab1, tab2 = st.tabs(["Vendors", "Withdrawals"])
    
    conn = init_supabase()
    if not conn:
        return
    
    with tab1:
        try:
            vendors = conn.table("vendors").select("*").execute()
            if vendors.data:
                st.dataframe(pd.DataFrame(vendors.data))
        except:
            st.info("No vendors found")
    
    with tab2:
        try:
            withdrawals = conn.table("withdrawals").select("*, daily_shifts!inner(date)").execute()
            if withdrawals.data:
                df = pd.DataFrame(withdrawals.data)
                st.dataframe(df[['amount', 'description']])
                st.metric("Total", f"₹{df['amount'].sum():,.2f}")
        except:
            st.info("No withdrawals found")

# ============================================
# SETTINGS
# ============================================
def show_settings():
    st.title("⚙️ Settings")
    
    conn = init_supabase()
    if not conn:
        return
    
    tabs = st.tabs(["Users", "Vendors"])
    
    with tabs[0]:
        st.subheader("Add User")
        with st.form("add_user"):
            username = st.text_input("Username")
            password = st.text_input("Password")
            role = st.selectbox("Role", ["owner", "admin"])
            if st.form_submit_button("Add"):
                try:
                    conn.table("users").insert({
                        'username': username,
                        'password': password,
                        'role': role,
                        'full_name': username
                    }).execute()
                    st.success("User added")
                except:
                    st.error("Failed")
    
    with tabs[1]:
        st.subheader("Add Vendor")
        with st.form("add_vendor"):
            name = st.text_input("Vendor Name")
            phone = st.text_input("Phone")
            if st.form_submit_button("Add"):
                try:
                    conn.table("vendors").insert({
                        'name': name,
                        'phone': phone,
                        'current_balance': 0
                    }).execute()
                    st.success("Vendor added")
                except:
                    st.error("Failed")

# ============================================
# MAIN
# ============================================
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()
