import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import io
import base64
from PIL import Image
import os
import json

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Medical Store Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CUSTOM CSS STYLING
# ============================================
def load_css():
    st.markdown("""
    <style>
        /* Main container */
        .main {
            padding: 0rem 1rem;
        }
        
        /* Headers */
        h1 {
            color: #2E86AB;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        h2 {
            color: #A23B72;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 500;
        }
        
        h3 {
            color: #F18F01;
            font-family: 'Segoe UI', sans-serif;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #2E86AB;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #A23B72;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Cards */
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }
        
        .metric-card h4 {
            color: white;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .metric-card p {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: #f8f9fa;
            padding: 0.5rem;
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        /* Forms */
        .stTextInput > div > div > input {
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }
        
        .stSelectbox > div > div > select {
            border-radius: 6px;
        }
        
        /* Tables */
        .dataframe {
            border-collapse: collapse;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .dataframe th {
            background-color: #2E86AB;
            color: white;
            font-weight: 500;
            padding: 0.75rem;
        }
        
        .dataframe td {
            padding: 0.75rem;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .dataframe tr:hover {
            background-color: #f5f5f5;
        }
        
        /* Alerts */
        .success-alert {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }
        
        .warning-alert {
            background-color: #fff3cd;
            color: #856404;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        }
        
        /* Login Form */
        .login-container {
            max-width: 400px;
            margin: 5rem auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .login-title {
            text-align: center;
            color: #2E86AB;
            margin-bottom: 2rem;
        }
        
        /* Settings Panel */
        .settings-section {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        /* PDF Download Button */
        .pdf-btn {
            background-color: #dc3545 !important;
            color: white !important;
        }
        
        .pdf-btn:hover {
            background-color: #c82333 !important;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: #6c757d;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# SUPABASE CONNECTION
# ============================================
from st_supabase_connection import SupabaseConnection

@st.cache_resource
def init_supabase():
    """Initialize Supabase connection"""
    return st.connection("supabase", type=SupabaseConnection)

# ============================================
# PDF GENERATION
# ============================================
from fpdf import FPDF
import tempfile

class PDFReport(FPDF):
    def header(self):
        # Get settings from session state
        settings = st.session_state.get('settings', {})
        
        # Logo
        if settings.get('logo_url'):
            try:
                self.image(settings['logo_url'], 10, 8, 33)
            except:
                pass
        
        # Store Name
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, settings.get('store_name', 'Medical Store'), 0, 0, 'C')
        self.ln(10)
        
        # Header Text
        self.set_font('Arial', 'I', 10)
        self.cell(80)
        self.cell(30, 10, settings.get('header_text', ''), 0, 0, 'C')
        self.ln(20)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        settings = st.session_state.get('settings', {})
        self.cell(0, 10, settings.get('footer_text', 'Page ') + str(self.page_no()), 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(46, 134, 171)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 8, body)
        self.ln()
    
    def add_table(self, headers, data):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(46, 134, 171)
        self.set_text_color(255, 255, 255)
        
        # Calculate column widths
        col_width = self.w / (len(headers) + 1)
        
        # Headers
        for header in headers:
            self.cell(col_width, 10, header, 1, 0, 'C', 1)
        self.ln()
        
        # Data
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        
        for row in data:
            for item in row:
                self.cell(col_width, 8, str(item), 1, 0, 'C')
            self.ln()

def generate_pdf_report(title, headers, data, filename="report.pdf"):
    """Generate PDF report"""
    pdf = PDFReport()
    pdf.add_page()
    pdf.chapter_title(title)
    pdf.add_table(headers, data)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
def init_session_state():
    """Initialize all session state variables"""
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if 'current_shift' not in st.session_state:
        st.session_state.current_shift = None
    
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'store_name': 'Medical Store',
            'owner_name': 'Owner',
            'primary_color': '#2E86AB',
            'secondary_color': '#A23B72',
            'header_text': 'Medical Store Management System',
            'footer_text': 'Powered by Streamlit',
            'logo_url': None
        }
    
    if 'expense_heads' not in st.session_state:
        st.session_state.expense_heads = [
            'Rent', 'Electricity', 'Staff Salary', 'Chai-Paani',
            'Cleaning', 'Stationery', 'Maintenance', 'Transport', 'Miscellaneous'
        ]

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    """Render login page"""
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">🏥 Medical Store Login</h2>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔐 Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            # Simple authentication (as requested - no hashing)
            conn = init_supabase()
            response = conn.table("users").select("*").eq("username", username).eq("password", password).execute()
            
            if response.data:
                user = response.data[0]
                st.session_state.authenticated = True
                st.session_state.user_role = user['role']
                st.session_state.username = user['full_name']
                st.session_state.user_id = user['id']
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Demo credentials
    st.info("👆 Demo Credentials: admin / admin123 or owner / owner123")

# ============================================
# MAIN DASHBOARD
# ============================================
def main_dashboard():
    """Main dashboard after login"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/pharmacy-shop.png", width=80)
        st.markdown(f"### Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role.upper()}")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📝 Record Entry", "📊 Reports", "📒 Ledgers", "⚙️ Settings"],
            index=0
        )
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            for key in ['authenticated', 'user_role', 'username', 'user_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content based on selection
    if page == "📝 Record Entry":
        show_record_entry()
    elif page == "📊 Reports":
        show_reports()
    elif page == "📒 Ledgers":
        show_ledgers()
    elif page == "⚙️ Settings" and st.session_state.user_role == 'admin':
        show_settings()
    else:
        st.error("⛔ Access Denied: Only admin can access settings")

# ============================================
# RECORD ENTRY PAGE
# ============================================
def show_record_entry():
    """Shift-wise record entry"""
    
    st.title("📝 Record Entry")
    
    # Shift Selection
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌅 Morning Shift", use_container_width=True):
            st.session_state.current_shift = "Morning"
    with col2:
        if st.button("☀️ Evening Shift", use_container_width=True):
            st.session_state.current_shift = "Evening"
    with col3:
        if st.button("🌙 Night Shift", use_container_width=True):
            st.session_state.current_shift = "Night"
    
    st.markdown("---")
    
    # Show entry form if shift selected
    if st.session_state.current_shift:
        st.subheader(f"📍 {st.session_state.current_shift} Shift Entry")
        
        with st.form("shift_entry_form"):
            # Date
            entry_date = st.date_input("📅 Date", value=date.today())
            
            # Sales Section
            st.markdown("### 💰 Sales")
            col1, col2, col3 = st.columns(3)
            with col1:
                cash_sales = st.number_input("Cash Sales (₹)", min_value=0.0, step=100.0)
            with col2:
                upi_sales = st.number_input("UPI Sales (₹)", min_value=0.0, step=100.0)
            with col3:
                card_sales = st.number_input("Card Sales (₹)", min_value=0.0, step=100.0)
            
            total_sales = cash_sales + upi_sales + card_sales
            st.info(f"**Total Sales: ₹{total_sales:,.2f}**")
            
            st.markdown("---")
            
            # Expenses Section
            st.markdown("### 💸 Expenses")
            
            expenses = []
            num_expenses = st.number_input("Number of Expenses", min_value=0, max_value=10, value=0)
            
            for i in range(num_expenses):
                st.markdown(f"**Expense #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    head = st.selectbox(f"Head {i+1}", options=st.session_state.expense_heads, key=f"exp_head_{i}")
                    amount = st.number_input(f"Amount {i+1}", min_value=0.0, key=f"exp_amt_{i}")
                with col2:
                    source = st.radio(f"Source {i+1}", ["Sales", "Pocket"], horizontal=True, key=f"exp_src_{i}")
                    desc = st.text_input(f"Description {i+1}", key=f"exp_desc_{i}")
                
                if amount > 0:
                    expenses.append({
                        'head': head,
                        'amount': amount,
                        'source': source.lower(),
                        'description': desc
                    })
                st.markdown("---")
            
            # Vendor Payments Section
            st.markdown("### 💳 Vendor Payments")
            
            vendor_payments = []
            num_payments = st.number_input("Number of Vendor Payments", min_value=0, max_value=10, value=0, key="num_pay")
            
            # Get vendors from database
            conn = init_supabase()
            vendors_response = conn.table("vendors").select("id,name").eq("is_active", True).execute()
            vendors = vendors_response.data if vendors_response.data else []
            vendor_options = {v['name']: v['id'] for v in vendors}
            
            for i in range(num_payments):
                st.markdown(f"**Payment #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    vendor_name = st.selectbox(f"Vendor {i+1}", options=list(vendor_options.keys()), key=f"vendor_{i}")
                    vendor_id = vendor_options.get(vendor_name)
                    amount = st.number_input(f"Amount {i+1}", min_value=0.0, key=f"pay_amt_{i}")
                with col2:
                    source = st.radio(f"Source {i+1}", ["Sales", "Pocket"], horizontal=True, key=f"pay_src_{i}")
                    desc = st.text_input(f"Note {i+1}", key=f"pay_desc_{i}")
                
                if amount > 0 and vendor_id:
                    vendor_payments.append({
                        'vendor_id': vendor_id,
                        'vendor_name': vendor_name,
                        'amount': amount,
                        'source': source.lower(),
                        'description': desc
                    })
                st.markdown("---")
            
            # Purchase/Return Section
            st.markdown("### 📦 Purchase/Return")
            
            col1, col2 = st.columns(2)
            with col1:
                trans_type = st.radio("Transaction Type", ["Purchase", "Return"], horizontal=True)
            with col2:
                if trans_type == "Purchase":
                    payment_mode = st.radio("Payment Mode", ["Cash", "Credit"], horizontal=True)
            
            if vendor_options:
                vendor_name = st.selectbox("Select Vendor", options=list(vendor_options.keys()), key="purchase_vendor")
                vendor_id = vendor_options.get(vendor_name)
                amount = st.number_input("Amount (₹)", min_value=0.0, key="purchase_amt")
                
                if trans_type == "Purchase" and payment_mode == "Cash":
                    cash_source = st.radio("Cash Source", ["Sales", "Pocket"], horizontal=True)
                else:
                    cash_source = None
                
                description = st.text_input("Description (Optional)")
            else:
                st.warning("No vendors found. Please add vendors in Settings.")
                vendor_id = None
            
            st.markdown("---")
            
            # Withdrawal Section
            st.markdown("### 🏧 Withdrawal (Personal)")
            withdrawal_amt = st.number_input("Withdrawal Amount (₹)", min_value=0.0, key="withdraw_amt")
            withdrawal_desc = st.text_input("Withdrawal Description", key="withdraw_desc")
            
            st.markdown("---")
            
            # Submit Button
            submitted = st.form_submit_button("✅ Save Shift Data", use_container_width=True)
            
            if submitted:
                # Save to database
                try:
                    conn = init_supabase()
                    
                    # 1. Create daily shift record
                    shift_id = conn.table("shifts").select("id").eq("shift_name", st.session_state.current_shift).execute().data[0]['id']
                    
                    shift_data = {
                        'shift_id': shift_id,
                        'date': entry_date.isoformat(),
                        'user_id': st.session_state.user_id,
                        'opening_cash': 0,  # Get from previous closing
                        'cash_sales': cash_sales,
                        'upi_sales': upi_sales,
                        'card_sales': card_sales,
                        'notes': f"{st.session_state.current_shift} shift entry"
                    }
                    
                    shift_response = conn.table("daily_shifts").insert(shift_data).execute()
                    daily_shift_id = shift_response.data[0]['id']
                    
                    # 2. Save expenses
                    for exp in expenses:
                        head_response = conn.table("expense_heads").select("id").eq("head_name", exp['head']).execute()
                        head_id = head_response.data[0]['id']
                        
                        exp_data = {
                            'daily_shift_id': daily_shift_id,
                            'expense_head_id': head_id,
                            'description': exp['description'],
                            'amount': exp['amount'],
                            'payment_source': exp['source']
                        }
                        conn.table("expenses").insert(exp_data).execute()
                        
                        # Update personal ledger if source is pocket
                        if exp['source'] == 'pocket':
                            # Get current balance
                            balance_response = conn.table("personal_ledger").select("balance_after").order("id", desc=True).limit(1).execute()
                            current_balance = balance_response.data[0]['balance_after'] if balance_response.data else 0
                            
                            pl_data = {
                                'daily_shift_id': daily_shift_id,
                                'transaction_type': 'add',
                                'amount': exp['amount'],
                                'description': f"Expense: {exp['head']} - {exp['description']}",
                                'balance_after': current_balance + exp['amount']
                            }
                            conn.table("personal_ledger").insert(pl_data).execute()
                    
                    # 3. Save vendor payments
                    for pay in vendor_payments:
                        # Get vendor current balance
                        vendor_response = conn.table("vendors").select("current_balance").eq("id", pay['vendor_id']).execute()
                        current_balance = vendor_response.data[0]['current_balance']
                        
                        vt_data = {
                            'daily_shift_id': daily_shift_id,
                            'vendor_id': pay['vendor_id'],
                            'transaction_type': 'payment',
                            'amount': pay['amount'],
                            'payment_mode': 'cash',
                            'cash_source': pay['source'],
                            'balance_before': current_balance,
                            'balance_after': current_balance - pay['amount'],
                            'description': pay['description']
                        }
                        conn.table("vendor_transactions").insert(vt_data).execute()
                        
                        # Update personal ledger if source is pocket
                        if pay['source'] == 'pocket':
                            balance_response = conn.table("personal_ledger").select("balance_after").order("id", desc=True).limit(1).execute()
                            current_pl = balance_response.data[0]['balance_after'] if balance_response.data else 0
                            
                            pl_data = {
                                'daily_shift_id': daily_shift_id,
                                'transaction_type': 'add',
                                'amount': pay['amount'],
                                'description': f"Vendor Payment: {pay['vendor_name']} - {pay['description']}",
                                'balance_after': current_pl + pay['amount']
                            }
                            conn.table("personal_ledger").insert(pl_data).execute()
                    
                    # 4. Save purchase/return
                    if vendor_id and amount > 0:
                        # Get vendor current balance
                        vendor_response = conn.table("vendors").select("current_balance").eq("id", vendor_id).execute()
                        current_balance = vendor_response.data[0]['current_balance']
                        
                        if trans_type == "Purchase":
                            vt_data = {
                                'daily_shift_id': daily_shift_id,
                                'vendor_id': vendor_id,
                                'transaction_type': 'purchase',
                                'amount': amount,
                                'payment_mode': payment_mode.lower(),
                                'cash_source': cash_source.lower() if cash_source else None,
                                'balance_before': current_balance,
                                'balance_after': current_balance + amount if payment_mode == 'Credit' else current_balance,
                                'description': description
                            }
                            
                            conn.table("vendor_transactions").insert(vt_data).execute()
                            
                            # If cash purchase from pocket, update personal ledger
                            if payment_mode == 'Cash' and cash_source == 'Pocket':
                                balance_response = conn.table("personal_ledger").select("balance_after").order("id", desc=True).limit(1).execute()
                                current_pl = balance_response.data[0]['balance_after'] if balance_response.data else 0
                                
                                pl_data = {
                                    'daily_shift_id': daily_shift_id,
                                    'transaction_type': 'add',
                                    'amount': amount,
                                    'description': f"Purchase from {vendor_name} - {description}",
                                    'balance_after': current_pl + amount
                                }
                                conn.table("personal_ledger").insert(pl_data).execute()
                        
                        elif trans_type == "Return":
                            vt_data = {
                                'daily_shift_id': daily_shift_id,
                                'vendor_id': vendor_id,
                                'transaction_type': 'return',
                                'amount': amount,
                                'payment_mode': 'credit',  # Return usually adjusts balance
                                'balance_before': current_balance,
                                'balance_after': current_balance - amount,
                                'description': description
                            }
                            conn.table("vendor_transactions").insert(vt_data).execute()
                    
                    # 5. Save withdrawal
                    if withdrawal_amt > 0:
                        wt_data = {
                            'daily_shift_id': daily_shift_id,
                            'amount': withdrawal_amt,
                            'description': withdrawal_desc
                        }
                        conn.table("withdrawals").insert(wt_data).execute()
                        
                        # Update personal ledger (withdrawal reduces personal contribution)
                        balance_response = conn.table("personal_ledger").select("balance_after").order("id", desc=True).limit(1).execute()
                        current_pl = balance_response.data[0]['balance_after'] if balance_response.data else 0
                        
                        pl_data = {
                            'daily_shift_id': daily_shift_id,
                            'transaction_type': 'withdraw',
                            'amount': withdrawal_amt,
                            'description': withdrawal_desc,
                            'balance_after': current_pl - withdrawal_amt
                        }
                        conn.table("personal_ledger").insert(pl_data).execute()
                    
                    # 6. Calculate and update closing cash
                    # Simple calculation: opening + sales - (expenses from sales) - (vendor payments from sales) - (cash purchases from sales) - withdrawals
                    expenses_from_sales = sum(e['amount'] for e in expenses if e['source'] == 'sales')
                    payments_from_sales = sum(p['amount'] for p in vendor_payments if p['source'] == 'sales')
                    cash_purchases_from_sales = amount if trans_type == 'Purchase' and payment_mode == 'Cash' and cash_source == 'Sales' and vendor_id and amount > 0 else 0
                    
                    closing_cash = 0 + cash_sales - expenses_from_sales - payments_from_sales - cash_purchases_from_sales - withdrawal_amt
                    
                    conn.table("daily_shifts").update({'closing_cash': closing_cash}).eq('id', daily_shift_id).execute()
                    
                    st.success("✅ Shift data saved successfully!")
                    
                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")

# ============================================
# REPORTS PAGE
# ============================================
def show_reports():
    """Show reports with PDF download"""
    
    st.title("📊 Reports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Daily Summary", "Category-wise Expense", "Vendor Ledger", "Personal Ledger"]
    )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    conn = init_supabase()
    
    if report_type == "Daily Summary":
        # Get daily summary data
        response = conn.table("vw_daily_summary").select("*")\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .order("date", desc=True)\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Format for display
            display_df = df[['date', 'shift_name', 'cash_sales', 'upi_sales', 'card_sales', 
                            'total_sales', 'closing_cash', 'total_expenses_from_sales']]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sales", f"₹{df['total_sales'].sum():,.2f}")
            with col2:
                st.metric("Total Expenses", f"₹{df['total_expenses_from_sales'].sum():,.2f}")
            with col3:
                st.metric("Total Withdrawals", f"₹{df['total_withdrawals'].sum():,.2f}")
            with col4:
                st.metric("Net Cash", f"₹{df['closing_cash'].sum():,.2f}")
            
            # PDF Download
            if st.button("📥 Download PDF Report", key="daily_pdf"):
                headers = ['Date', 'Shift', 'Cash Sales', 'UPI Sales', 'Card Sales', 'Total', 'Closing Cash']
                data = df[['date', 'shift_name', 'cash_sales', 'upi_sales', 'card_sales', 
                          'total_sales', 'closing_cash']].values.tolist()
                
                pdf_file = generate_pdf_report(
                    f"Daily Summary Report ({start_date} to {end_date})",
                    headers, data
                )
                
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        "📥 Click to Download PDF",
                        f,
                        file_name=f"daily_summary_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No data found for selected period")
    
    elif report_type == "Category-wise Expense":
        # Get expense data grouped by category
        response = conn.table("expenses")\
            .select("expense_heads(head_name), amount")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['head_name'] = df['expense_heads'].apply(lambda x: x['head_name'])
            
            # Group by head
            category_summary = df.groupby('head_name')['amount'].sum().reset_index()
            
            # Bar chart
            fig = px.bar(category_summary, x='head_name', y='amount', 
                        title="Expenses by Category",
                        color='head_name')
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(category_summary, use_container_width=True)
            
            # Pie chart
            fig2 = px.pie(category_summary, values='amount', names='head_name',
                         title="Expense Distribution")
            st.plotly_chart(fig2, use_container_width=True)
            
            # PDF Download
            if st.button("📥 Download PDF Report", key="category_pdf"):
                headers = ['Category', 'Total Amount (₹)']
                data = category_summary.values.tolist()
                
                pdf_file = generate_pdf_report(
                    f"Category-wise Expense Report ({start_date} to {end_date})",
                    headers, data
                )
                
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        "📥 Click to Download PDF",
                        f,
                        file_name=f"category_expense_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No expense data found")
    
    elif report_type == "Vendor Ledger":
        # Get vendor balances
        response = conn.table("vw_vendor_balances").select("*").execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df, use_container_width=True)
            
            # Vendor transactions
            st.subheader("Vendor Transactions")
            vendor_trans = conn.table("vendor_transactions")\
                .select("*, vendors(name)")\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            if vendor_trans.data:
                trans_df = pd.DataFrame(vendor_trans.data)
                trans_df['vendor_name'] = trans_df['vendors'].apply(lambda x: x['name'])
                st.dataframe(trans_df[['created_at', 'vendor_name', 'transaction_type', 
                                      'amount', 'payment_mode', 'balance_after']], 
                           use_container_width=True)
    
    elif report_type == "Personal Ledger":
        # Get personal ledger entries
        response = conn.table("personal_ledger")\
            .select("*")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .order("created_at", desc=True)\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df[['created_at', 'transaction_type', 'amount', 'description', 'balance_after']], 
                        use_container_width=True)
            
            # Summary
            total_added = df[df['transaction_type'] == 'add']['amount'].sum()
            total_withdrawn = df[df['transaction_type'] == 'withdraw']['amount'].sum()
            current_balance = df.iloc[0]['balance_after'] if not df.empty else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Added (Pocket to Store)", f"₹{total_added:,.2f}")
            with col2:
                st.metric("Total Withdrawn (Store to Pocket)", f"₹{total_withdrawn:,.2f}")
            with col3:
                st.metric("Current Balance in Store", f"₹{current_balance:,.2f}")

# ============================================
# LEDGERS PAGE
# ============================================
def show_ledgers():
    """Show all ledgers"""
    
    st.title("📒 Ledgers")
    
    tab1, tab2, tab3 = st.tabs(["📒 Vendor Ledger", "💰 Personal Ledger", "📋 Expense Heads"])
    
    conn = init_supabase()
    
    with tab1:
        st.subheader("Vendor Ledger")
        
        # Get all vendors
        vendors = conn.table("vendors").select("*").eq("is_active", True).order("name").execute()
        
        if vendors.data:
            for vendor in vendors.data:
                with st.expander(f"{vendor['name']} - Balance: ₹{vendor['current_balance']:,.2f}"):
                    # Get transactions for this vendor
                    trans = conn.table("vendor_transactions")\
                        .select("*")\
                        .eq("vendor_id", vendor['id'])\
                        .order("created_at", desc=True)\
                        .limit(50)\
                        .execute()
                    
                    if trans.data:
                        df = pd.DataFrame(trans.data)
                        st.dataframe(df[['created_at', 'transaction_type', 'amount', 
                                       'payment_mode', 'balance_after', 'description']],
                                   use_container_width=True)
                    else:
                        st.info("No transactions found")
        else:
            st.info("No vendors found")
    
    with tab2:
        st.subheader("Personal Ledger")
        
        # Get personal ledger entries
        pl = conn.table("personal_ledger")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(100)\
            .execute()
        
        if pl.data:
            df = pd.DataFrame(pl.data)
            st.dataframe(df[['created_at', 'transaction_type', 'amount', 'description', 'balance_after']],
                        use_container_width=True)
            
            # Current balance
            current_balance = df.iloc[0]['balance_after'] if not df.empty else 0
            st.metric("Current Personal Balance in Store", f"₹{current_balance:,.2f}")
    
    with tab3:
        st.subheader("Expense Heads")
        
        # Get expense heads
        heads = conn.table("expense_heads").select("*").order("head_name").execute()
        
        if heads.data:
            df = pd.DataFrame(heads.data)
            st.dataframe(df[['head_name', 'description', 'is_active']], use_container_width=True)

# ============================================
# SETTINGS PAGE
# ============================================
def show_settings():
    """Settings page (admin only)"""
    
    st.title("⚙️ Settings")
    
    conn = init_supabase()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏪 Store Settings", "👥 Users", "🏢 Vendors", "📋 Expense Heads"])
    
    with tab1:
        st.subheader("Store Settings")
        
        # Get current settings
        settings = conn.table("store_settings").select("*").eq("id", 1).execute()
        current = settings.data[0] if settings.data else {}
        
        with st.form("store_settings_form"):
            col1, col2 = st.columns(2)
            with col1:
                store_name = st.text_input("Store Name", value=current.get('store_name', ''))
                owner_name = st.text_input("Owner Name", value=current.get('owner_name', ''))
                phone = st.text_input("Phone", value=current.get('phone', ''))
            with col2:
                email = st.text_input("Email", value=current.get('email', ''))
                address = st.text_area("Address", value=current.get('address', ''))
            
            st.markdown("### Appearance")
            col1, col2 = st.columns(2)
            with col1:
                primary_color = st.color_picker("Primary Color", value=current.get('primary_color', '#2E86AB'))
            with col2:
                secondary_color = st.color_picker("Secondary Color", value=current.get('secondary_color', '#A23B72'))
            
            header_text = st.text_input("Header Text", value=current.get('header_text', ''))
            footer_text = st.text_input("Footer Text", value=current.get('footer_text', ''))
            
            # Logo upload (simulated)
            logo_url = st.text_input("Logo URL (optional)", value=current.get('logo_url', ''))
            
            submitted = st.form_submit_button("Save Settings")
            
            if submitted:
                settings_data = {
                    'store_name': store_name,
                    'owner_name': owner_name,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'primary_color': primary_color,
                    'secondary_color': secondary_color,
                    'header_text': header_text,
                    'footer_text': footer_text,
                    'logo_url': logo_url,
                    'updated_at': datetime.now().isoformat()
                }
                
                if settings.data:
                    conn.table("store_settings").update(settings_data).eq("id", 1).execute()
                else:
                    settings_data['id'] = 1
                    conn.table("store_settings").insert(settings_data).execute()
                
                # Update session state
                st.session_state.settings.update(settings_data)
                st.success("Settings saved successfully!")
    
    with tab2:
        st.subheader("User Management")
        
        # Get all users
        users = conn.table("users").select("*").order("username").execute()
        
        if users.data:
            df = pd.DataFrame(users.data)
            st.dataframe(df[['username', 'full_name', 'role', 'is_active']], use_container_width=True)
        
        # Add new user
        with st.expander("➕ Add New User"):
            with st.form("new_user_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                role = st.selectbox("Role", ["owner", "admin"])
                
                submitted = st.form_submit_button("Add User")
                
                if submitted:
                    user_data = {
                        'username': username,
                        'password': password,  # As requested - no hashing
                        'full_name': full_name,
                        'role': role,
                        'is_active': True
                    }
                    
                    try:
                        conn.table("users").insert(user_data).execute()
                        st.success(f"User {username} added successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("Vendor Management")
        
        # Get all vendors
        vendors = conn.table("vendors").select("*").order("name").execute()
        
        if vendors.data:
            df = pd.DataFrame(vendors.data)
            st.dataframe(df[['name', 'phone', 'current_balance', 'gst_no', 'is_active']], 
                        use_container_width=True)
        
        # Add new vendor
        with st.expander("➕ Add New Vendor"):
            with st.form("new_vendor_form"):
                name = st.text_input("Vendor Name")
                phone = st.text_input("Phone")
                address = st.text_area("Address")
                gst_no = st.text_input("GST No (Optional)")
                opening_balance = st.number_input("Opening Balance", value=0.0)
                
                submitted = st.form_submit_button("Add Vendor")
                
                if submitted:
                    vendor_data = {
                        'name': name,
                        'phone': phone,
                        'address': address,
                        'gst_no': gst_no,
                        'opening_balance': opening_balance,
                        'current_balance': opening_balance,
                        'is_active': True
                    }
                    
                    try:
                        conn.table("vendors").insert(vendor_data).execute()
                        st.success(f"Vendor {name} added successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab4:
        st.subheader("Expense Heads")
        
        # Get expense heads
        heads = conn.table("expense_heads").select("*").order("head_name").execute()
        
        if heads.data:
            df = pd.DataFrame(heads.data)
            st.dataframe(df[['head_name', 'description', 'is_active']], use_container_width=True)
        
        # Add new head
        with st.expander("➕ Add Expense Head"):
            with st.form("new_head_form"):
                head_name = st.text_input("Head Name")
                description = st.text_input("Description (Optional)")
                
                submitted = st.form_submit_button("Add Head")
                
                if submitted:
                    head_data = {
                        'head_name': head_name,
                        'description': description,
                        'is_active': True
                    }
                    
                    try:
                        conn.table("expense_heads").insert(head_data).execute()
                        st.success(f"Head {head_name} added successfully!")
                        
                        # Update session state
                        st.session_state.expense_heads.append(head_name)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================
# FOOTER
# ============================================
def show_footer():
    """Show footer"""
    settings = st.session_state.get('settings', {})
    st.markdown(f"""
    <div class="footer">
        {settings.get('footer_text', 'Powered by Streamlit')} | {settings.get('store_name', 'Medical Store')}
    </div>
    """, unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================
def main():
    """Main application"""
    
    # Load CSS
    load_css()
    
    # Initialize session state
    init_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()
        show_footer()

if __name__ == "__main__":
    main()
