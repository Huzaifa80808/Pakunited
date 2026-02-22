import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os
from supabase import create_client, Client

# ============================================
# PAGE CONFIG
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
    h1 { color: #2E86AB; font-weight: 600; }
    .stButton > button {
        background-color: #2E86AB;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
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
# SUPABASE CLIENT
# ============================================
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
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
        username = st.text_input("👤 Username")
        password = st.text_input("🔐 Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            supabase = init_supabase()
            if supabase:
                try:
                    response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
                    if response.data:
                        user = response.data[0]
                        st.session_state.authenticated = True
                        st.session_state.user_role = user['role']
                        st.session_state.username = user.get('full_name', username)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
    
    st.info("👆 Demo: admin/admin123 or owner/owner123")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# DASHBOARD
# ============================================
def dashboard():
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role.upper()}")
        st.markdown("---")
        
        menu = ["📝 Record Entry", "📊 Reports", "📒 Ledgers"]
        if st.session_state.user_role == 'admin':
            menu.append("⚙️ Settings")
        
        choice = st.radio("Navigation", menu)
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    if choice == "📝 Record Entry":
        show_record_entry()
    elif choice == "📊 Reports":
        show_reports()
    elif choice == "📒 Ledgers":
        show_ledgers()
    elif choice == "⚙️ Settings":
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
        st.subheader(f"📍 {st.session_state.current_shift} Shift")
        
        with st.form("entry_form"):
            entry_date = st.date_input("📅 Date", date.today())
            
            st.markdown("### 💰 Sales")
            col1, col2, col3 = st.columns(3)
            with col1:
                cash = st.number_input("Cash (₹)", 0.0, step=100.0)
            with col2:
                upi = st.number_input("UPI (₹)", 0.0, step=100.0)
            with col3:
                card = st.number_input("Card (₹)", 0.0, step=100.0)
            
            total = cash + upi + card
            st.info(f"**Total: ₹{total:,.2f}**")
            
            st.markdown("### 💸 Expenses")
            num_exp = st.number_input("Number of Expenses", 0, 5, 0)
            expenses = []
            for i in range(num_exp):
                col1, col2 = st.columns(2)
                with col1:
                    amt = st.number_input(f"Amount {i+1}", 0.0, key=f"amt_{i}")
                with col2:
                    src = st.selectbox(f"Source {i+1}", ["Sales", "Pocket"], key=f"src_{i}")
                if amt > 0:
                    expenses.append({"amount": amt, "source": src.lower()})
            
            st.markdown("### 🏧 Withdrawal")
            withdraw = st.number_input("Withdrawal Amount", 0.0)
            
            if st.form_submit_button("✅ Save"):
                supabase = init_supabase()
                if supabase:
                    try:
                        # Get shift ID
                        shift_res = supabase.table("shifts").select("id").eq("shift_name", st.session_state.current_shift).execute()
                        shift_id = shift_res.data[0]['id'] if shift_res.data else 1
                        
                        # Calculate closing
                        exp_sales = sum(e['amount'] for e in expenses if e['source'] == 'sales')
                        closing = cash - exp_sales - withdraw
                        
                        # Save shift
                        data = {
                            'shift_id': shift_id,
                            'date': entry_date.isoformat(),
                            'cash_sales': cash,
                            'upi_sales': upi,
                            'card_sales': card,
                            'closing_cash': closing
                        }
                        
                        res = supabase.table("daily_shifts").insert(data).execute()
                        
                        if res.data:
                            st.success("✅ Saved!")
                            st.session_state.current_shift = None
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================
# REPORTS
# ============================================
def show_reports():
    st.title("📊 Reports")
    
    report = st.selectbox("Report Type", ["Daily Summary", "Expense Summary"])
    start = st.date_input("From", date.today() - timedelta(days=30))
    end = st.date_input("To", date.today())
    
    supabase = init_supabase()
    if not supabase:
        return
    
    if report == "Daily Summary":
        try:
            res = supabase.table("daily_shifts").select("*, shifts(shift_name)").gte("date", start.isoformat()).lte("date", end.isoformat()).order("date", desc=True).execute()
            
            if res.data:
                data = []
                for r in res.data:
                    shift = r['shifts']['shift_name'] if r.get('shifts') else 'Unknown'
                    data.append({
                        'Date': r['date'],
                        'Shift': shift,
                        'Cash': r['cash_sales'],
                        'UPI': r['upi_sales'],
                        'Card': r['card_sales'],
                        'Total': r['cash_sales'] + r['upi_sales'] + r['card_sales']
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                fig = px.bar(df, x='Date', y='Total', title="Daily Sales")
                st.plotly_chart(fig)
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================
# LEDGERS
# ============================================
def show_ledgers():
    st.title("📒 Ledgers")
    
    supabase = init_supabase()
    if not supabase:
        return
    
    tab1, tab2 = st.tabs(["Withdrawals", "Vendors"])
    
    with tab1:
        try:
            res = supabase.table("withdrawals").select("*").order("created_at", desc=True).limit(100).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                st.dataframe(df[['amount', 'description']])
                st.metric("Total", f"₹{df['amount'].sum():,.2f}")
        except:
            st.info("No withdrawals")
    
    with tab2:
        try:
            res = supabase.table("vendors").select("*").execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data))
        except:
            st.info("No vendors")

# ============================================
# SETTINGS
# ============================================
def show_settings():
    st.title("⚙️ Settings")
    
    supabase = init_supabase()
    if not supabase:
        return
    
    tab1, tab2 = st.tabs(["Add User", "Add Vendor"])
    
    with tab1:
        with st.form("add_user"):
            username = st.text_input("Username")
            password = st.text_input("Password")
            role = st.selectbox("Role", ["owner", "admin"])
            if st.form_submit_button("Add"):
                try:
                    supabase.table("users").insert({
                        'username': username,
                        'password': password,
                        'role': role,
                        'full_name': username
                    }).execute()
                    st.success("User added")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        with st.form("add_vendor"):
            name = st.text_input("Vendor Name")
            phone = st.text_input("Phone")
            if st.form_submit_button("Add"):
                try:
                    supabase.table("vendors").insert({
                        'name': name,
                        'phone': phone,
                        'current_balance': 0
                    }).execute()
                    st.success("Vendor added")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

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
