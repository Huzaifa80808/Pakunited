import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Medical Store Management",
    page_icon="🏥",
    layout="wide"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    /* Main */
    .main { padding: 0rem 1rem; }
    h1 { color: #2E86AB; font-weight: 600; }
    h2 { color: #A23B72; }
    
    /* Buttons */
    .stButton > button {
        background-color: #2E86AB;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #A23B72;
        transform: translateY(-2px);
    }
    
    /* Login */
    .login-container {
        max-width: 400px;
        margin: 5rem auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #2E86AB, #A23B72);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Tables */
    .dataframe th {
        background-color: #2E86AB;
        color: white;
        padding: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SUPABASE CONNECTION
# ============================================
try:
    from st_supabase_connection import SupabaseConnection
except ImportError:
    st.error("Installing required packages...")
    st.stop()

@st.cache_resource
def init_supabase():
    """Initialize Supabase connection"""
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        return conn
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
    st.session_state.user_id = None
    st.session_state.current_shift = None
    st.session_state.expense_heads = ['Rent', 'Electricity', 'Salary', 'Chai-Paani', 'Cleaning', 'Other']

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    """Render login page"""
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #2E86AB;">🏥 Medical Store Login</h2>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔐 Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            conn = init_supabase()
            if conn:
                try:
                    response = conn.table("users").select("*").eq("username", username).eq("password", password).execute()
                    
                    if response.data and len(response.data) > 0:
                        user = response.data[0]
                        st.session_state.authenticated = True
                        st.session_state.user_role = user['role']
                        st.session_state.username = user.get('full_name', username)
                        st.session_state.user_id = user['id']
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
            else:
                st.error("Database connection failed")
    
    st.info("👆 Demo: admin/admin123 or owner/owner123")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN DASHBOARD
# ============================================
def dashboard():
    """Main dashboard"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role.upper()}")
        st.markdown("---")
        
        # Navigation
        menu_items = ["📝 Record Entry", "📊 Reports", "📒 Ledgers"]
        if st.session_state.user_role == 'admin':
            menu_items.append("⚙️ Settings")
        
        choice = st.radio("Navigation", menu_items)
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            for key in ['authenticated', 'user_role', 'username', 'user_id', 'current_shift']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content
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
    """Shift-wise record entry"""
    
    st.title("📝 Record Entry")
    
    # Shift Selection
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
    
    st.markdown("---")
    
    # Entry form
    if st.session_state.current_shift:
        st.subheader(f"📍 {st.session_state.current_shift} Shift Entry")
        
        with st.form("entry_form"):
            # Date
            entry_date = st.date_input("📅 Date", value=date.today())
            
            # Sales
            st.markdown("### 💰 Sales")
            col1, col2, col3 = st.columns(3)
            with col1:
                cash_sales = st.number_input("Cash (₹)", min_value=0.0, step=100.0)
            with col2:
                upi_sales = st.number_input("UPI (₹)", min_value=0.0, step=100.0)
            with col3:
                card_sales = st.number_input("Card (₹)", min_value=0.0, step=100.0)
            
            total_sales = cash_sales + upi_sales + card_sales
            st.info(f"**Total Sales: ₹{total_sales:,.2f}**")
            
            st.markdown("---")
            
            # Expenses
            st.markdown("### 💸 Expenses")
            expenses = []
            num_expenses = st.number_input("Number of Expenses", min_value=0, max_value=5, value=0)
            
            for i in range(num_expenses):
                st.markdown(f"**Expense #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input(f"Amount", min_value=0.0, key=f"exp_amt_{i}")
                with col2:
                    source = st.selectbox(f"Source", ["Sales", "Pocket"], key=f"exp_src_{i}")
                
                if amount > 0:
                    expenses.append({
                        'amount': amount,
                        'source': source.lower()
                    })
            
            st.markdown("---")
            
            # Withdrawal
            st.markdown("### 🏧 Withdrawal")
            withdrawal_amt = st.number_input("Withdrawal Amount (₹)", min_value=0.0)
            withdrawal_desc = st.text_input("Description")
            
            st.markdown("---")
            
            # Submit
            submitted = st.form_submit_button("✅ Save Shift", use_container_width=True)
            
            if submitted:
                conn = init_supabase()
                if conn:
                    try:
                        # Get shift ID
                        shift_response = conn.table("shifts").select("id").eq("shift_name", st.session_state.current_shift).execute()
                        shift_id = shift_response.data[0]['id'] if shift_response.data else 1
                        
                        # Calculate closing cash
                        expenses_from_sales = sum(e['amount'] for e in expenses if e['source'] == 'sales')
                        closing_cash = cash_sales - expenses_from_sales - withdrawal_amt
                        
                        # Save shift
                        shift_data = {
                            'shift_id': shift_id,
                            'date': entry_date.isoformat(),
                            'user_id': st.session_state.user_id,
                            'cash_sales': cash_sales,
                            'upi_sales': upi_sales,
                            'card_sales': card_sales,
                            'closing_cash': closing_cash
                        }
                        
                        shift_response = conn.table("daily_shifts").insert(shift_data).execute()
                        
                        if shift_response.data:
                            daily_shift_id = shift_response.data[0]['id']
                            
                            # Save expenses
                            for exp in expenses:
                                exp_data = {
                                    'daily_shift_id': daily_shift_id,
                                    'amount': exp['amount'],
                                    'payment_source': exp['source']
                                }
                                conn.table("expenses").insert(exp_data).execute()
                            
                            # Save withdrawal
                            if withdrawal_amt > 0:
                                wt_data = {
                                    'daily_shift_id': daily_shift_id,
                                    'amount': withdrawal_amt,
                                    'description': withdrawal_desc
                                }
                                conn.table("withdrawals").insert(wt_data).execute()
                            
                            st.success("✅ Shift data saved!")
                            st.session_state.current_shift = None
                            st.rerun()
                        else:
                            st.error("Failed to save")
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================
# REPORTS
# ============================================
def show_reports():
    """Show reports"""
    
    st.title("📊 Reports")
    
    # Report type
    report_type = st.selectbox("Select Report", ["Daily Summary", "Expense Summary"])
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To", date.today())
    
    conn = init_supabase()
    if not conn:
        return
    
    if report_type == "Daily Summary":
        try:
            # Get data
            response = conn.table("daily_shifts").select("*, shifts(shift_name)").gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).order("date", desc=True).execute()
            
            if response.data:
                # Convert to DataFrame
                data = []
                for row in response.data:
                    shift_name = row['shifts']['shift_name'] if row.get('shifts') else 'Unknown'
                    data.append({
                        'Date': row['date'],
                        'Shift': shift_name,
                        'Cash': row['cash_sales'],
                        'UPI': row['upi_sales'],
                        'Card': row['card_sales'],
                        'Total': row['cash_sales'] + row['upi_sales'] + row['card_sales'],
                        'Closing': row.get('closing_cash', 0)
                    })
                
                df = pd.DataFrame(data)
                
                # Show table
                st.dataframe(df, use_container_width=True)
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Sales", f"₹{df['Total'].sum():,.2f}")
                with col2:
                    st.metric("Total Cash", f"₹{df['Cash'].sum():,.2f}")
                with col3:
                    st.metric("Total UPI", f"₹{df['UPI'].sum():,.2f}")
                
                # Chart
                fig = px.bar(df, x='Date', y='Total', color='Shift', title="Daily Sales")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data found")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    else:  # Expense Summary
        try:
            # Get expenses
            response = conn.table("expenses").select("*, daily_shifts!inner(date)").gte("daily_shifts.date", start_date.isoformat()).lte("daily_shifts.date", end_date.isoformat()).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Group by source
                summary = df.groupby('payment_source')['amount'].sum().reset_index()
                
                # Chart
                fig = px.pie(summary, values='amount', names='payment_source', title="Expenses by Source")
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(df[['amount', 'payment_source']], use_container_width=True)
                
                # Total
                st.metric("Total Expenses", f"₹{df['amount'].sum():,.2f}")
            else:
                st.info("No expense data")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================
# LEDGERS
# ============================================
def show_ledgers():
    """Show ledgers"""
    
    st.title("📒 Ledgers")
    
    conn = init_supabase()
    if not conn:
        return
    
    tab1, tab2 = st.tabs(["💰 Withdrawals", "🏢 Vendors"])
    
    with tab1:
        try:
            response = conn.table("withdrawals").select("*, daily_shifts!inner(date)").order("created_at", desc=True).limit(100).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                st.dataframe(df[['amount', 'description']], use_container_width=True)
                st.metric("Total Withdrawn", f"₹{df['amount'].sum():,.2f}")
            else:
                st.info("No withdrawals")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        try:
            response = conn.table("vendors").select("*").execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                st.dataframe(df[['name', 'phone', 'current_balance']], use_container_width=True)
            else:
                st.info("No vendors")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================
# SETTINGS
# ============================================
def show_settings():
    """Settings page"""
    
    st.title("⚙️ Settings")
    
    conn = init_supabase()
    if not conn:
        return
    
    tab1, tab2 = st.tabs(["👥 Users", "🏢 Vendors"])
    
    with tab1:
        st.subheader("Add New User")
        with st.form("add_user"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["owner", "admin"])
            
            if st.form_submit_button("Add User"):
                try:
                    data = {
                        'username': username,
                        'password': password,
                        'full_name': full_name,
                        'role': role,
                        'is_active': True
                    }
                    conn.table("users").insert(data).execute()
                    st.success(f"User {username} added!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Add New Vendor")
        with st.form("add_vendor"):
            name = st.text_input("Vendor Name")
            phone = st.text_input("Phone")
            balance = st.number_input("Opening Balance", value=0.0)
            
            if st.form_submit_button("Add Vendor"):
                try:
                    data = {
                        'name': name,
                        'phone': phone,
                        'opening_balance': balance,
                        'current_balance': balance,
                        'is_active': True
                    }
                    conn.table("vendors").insert(data).execute()
                    st.success(f"Vendor {name} added!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================
# MAIN
# ============================================
def main():
    """Main app"""
    
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()
