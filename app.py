import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import io
import base64
import os
import json

# ============================================
# PAGE CONFIGURATION - MUST BE FIRST
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
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        return conn
    except Exception as e:
        st.error(f"Supabase connection error: {str(e)}")
        return None

# ============================================
# PDF GENERATION
# ============================================
from fpdf import FPDF
import tempfile

class PDFReport(FPDF):
    def header(self):
        # Get settings from session state
        settings = st.session_state.get('settings', {})
        
        # Store Name
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, settings.get('store_name', 'Medical Store'), 0, 0, 'C')
        self.ln(10)
        
        # Header Text
        self.set_font('Arial', 'I', 10)
        self.cell(80)
        self.cell(30, 10, settings.get('header_text', 'Daily Report'), 0, 0, 'C')
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
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'current_shift' not in st.session_state:
        st.session_state.current_shift = None
    
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'store_name': 'Medical Store',
            'owner_name': 'Owner',
            'primary_color': '#2E86AB',
            'secondary_color': '#A23B72',
            'header_text': 'Medical Store Management System',
            'footer_text': 'Powered by Streamlit'
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Demo credentials
    st.info("👆 Demo Credentials: admin / admin123 or owner / owner123")

# ============================================
# DASHBOARD
# ============================================
def main_dashboard():
    """Main dashboard after login"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role.upper()}")
        st.markdown("---")
        
        # Navigation
        pages = ["📝 Record Entry", "📊 Reports", "📒 Ledgers"]
        if st.session_state.user_role == 'admin':
            pages.append("⚙️ Settings")
        
        page = st.radio("Navigation", pages, index=0)
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            for key in ['authenticated', 'user_role', 'username', 'user_id', 'current_shift']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content
    if page == "📝 Record Entry":
        show_record_entry()
    elif page == "📊 Reports":
        show_reports()
    elif page == "📒 Ledgers":
        show_ledgers()
    elif page == "⚙️ Settings" and st.session_state.user_role == 'admin':
        show_settings()

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
            
            # Withdrawal Section
            st.markdown("### 🏧 Withdrawal (Personal)")
            withdrawal_amt = st.number_input("Withdrawal Amount (₹)", min_value=0.0, key="withdraw_amt")
            withdrawal_desc = st.text_input("Withdrawal Description", key="withdraw_desc")
            
            st.markdown("---")
            
            # Submit Button
            submitted = st.form_submit_button("✅ Save Shift Data", use_container_width=True)
            
            if submitted:
                conn = init_supabase()
                if conn:
                    try:
                        # Get shift ID
                        shift_response = conn.table("shifts").select("id").eq("shift_name", st.session_state.current_shift).execute()
                        if shift_response.data and len(shift_response.data) > 0:
                            shift_id = shift_response.data[0]['id']
                        else:
                            shift_id = 1  # Default to Morning
                        
                        # Create daily shift record
                        shift_data = {
                            'shift_id': shift_id,
                            'date': entry_date.isoformat(),
                            'user_id': st.session_state.user_id,
                            'cash_sales': cash_sales,
                            'upi_sales': upi_sales,
                            'card_sales': card_sales,
                            'notes': f"{st.session_state.current_shift} shift entry"
                        }
                        
                        shift_response = conn.table("daily_shifts").insert(shift_data).execute()
                        
                        if shift_response.data and len(shift_response.data) > 0:
                            daily_shift_id = shift_response.data[0]['id']
                            
                            # Save expenses
                            for exp in expenses:
                                # Get head ID
                                head_response = conn.table("expense_heads").select("id").eq("head_name", exp['head']).execute()
                                head_id = head_response.data[0]['id'] if head_response.data else 1
                                
                                exp_data = {
                                    'daily_shift_id': daily_shift_id,
                                    'expense_head_id': head_id,
                                    'description': exp['description'],
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
                            
                            # Calculate closing cash
                            expenses_from_sales = sum(e['amount'] for e in expenses if e['source'] == 'sales')
                            closing_cash = cash_sales - expenses_from_sales - withdrawal_amt
                            
                            conn.table("daily_shifts").update({'closing_cash': closing_cash}).eq('id', daily_shift_id).execute()
                            
                            st.success("✅ Shift data saved successfully!")
                        else:
                            st.error("Failed to create shift record")
                            
                    except Exception as e:
                        st.error(f"Error saving data: {str(e)}")
                else:
                    st.error("Database connection not available")

# ============================================
# REPORTS PAGE
# ============================================
def show_reports():
    """Show reports with PDF download"""
    
    st.title("📊 Reports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Daily Summary", "Category-wise Expense"]
    )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    conn = init_supabase()
    if not conn:
        st.error("Database connection not available")
        return
    
    if report_type == "Daily Summary":
        try:
            # Get daily summary data
            response = conn.table("daily_shifts").select("*, shifts(shift_name)").gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).order("date", desc=True).execute()
            
            if response.data and len(response.data) > 0:
                df = pd.DataFrame(response.data)
                
                # Format for display
                display_data = []
                for row in response.data:
                    shift_name = row['shifts']['shift_name'] if row.get('shifts') else 'Unknown'
                    display_data.append({
                        'Date': row['date'],
                        'Shift': shift_name,
                        'Cash Sales': row['cash_sales'],
                        'UPI Sales': row['upi_sales'],
                        'Card Sales': row['card_sales'],
                        'Total Sales': row['cash_sales'] + row['upi_sales'] + row['card_sales'],
                        'Closing Cash': row.get('closing_cash', 0)
                    })
                
                df_display = pd.DataFrame(display_data)
                st.dataframe(df_display, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Sales", f"₹{df_display['Total Sales'].sum():,.2f}")
                with col2:
                    st.metric("Total Cash", f"₹{df_display['Cash Sales'].sum():,.2f}")
                with col3:
                    st.metric("Total UPI", f"₹{df_display['UPI Sales'].sum():,.2f}")
                
                # PDF Download
                if st.button("📥 Download PDF Report"):
                    headers = ['Date', 'Shift', 'Cash Sales', 'UPI Sales', 'Card Sales', 'Total', 'Closing Cash']
                    data = df_display.values.tolist()
                    
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
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    elif report_type == "Category-wise Expense":
        try:
            # Get expense data
            response = conn.table("expenses").select("*, expense_heads(head_name), daily_shifts!inner(date)").gte("daily_shifts.date", start_date.isoformat()).lte("daily_shifts.date", end_date.isoformat()).execute()
            
            if response.data and len(response.data) > 0:
                df = pd.DataFrame(response.data)
                
                # Extract head names
                df['head_name'] = df['expense_heads'].apply(lambda x: x['head_name'] if x else 'Unknown')
                
                # Group by head
                category_summary = df.groupby('head_name')['amount'].sum().reset_index()
                
                # Bar chart
                fig = px.bar(category_summary, x='head_name', y='amount', 
                            title="Expenses by Category",
                            color='head_name',
                            color_discrete_sequence=['#2E86AB'] * len(category_summary))
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(category_summary, use_container_width=True)
                
                # Pie chart
                fig2 = px.pie(category_summary, values='amount', names='head_name',
                             title="Expense Distribution",
                             color_discrete_sequence=px.colors.sequential.Blues_r)
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
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

# ============================================
# LEDGERS PAGE
# ============================================
def show_ledgers():
    """Show all ledgers"""
    
    st.title("📒 Ledgers")
    
    tab1, tab2 = st.tabs(["📒 Vendor Ledger", "💰 Personal Ledger"])
    
    conn = init_supabase()
    if not conn:
        st.error("Database connection not available")
        return
    
    with tab1:
        st.subheader("Vendor Ledger")
        
        try:
            # Get all vendors
            vendors = conn.table("vendors").select("*").eq("is_active", True).order("name").execute()
            
            if vendors.data and len(vendors.data) > 0:
                for vendor in vendors.data:
                    with st.expander(f"{vendor['name']} - Balance: ₹{vendor.get('current_balance', 0):,.2f}"):
                        # Get transactions for this vendor
                        trans = conn.table("vendor_transactions")\
                            .select("*")\
                            .eq("vendor_id", vendor['id'])\
                            .order("created_at", desc=True)\
                            .limit(50)\
                            .execute()
                        
                        if trans.data and len(trans.data) > 0:
                            df = pd.DataFrame(trans.data)
                            display_cols = ['created_at', 'transaction_type', 'amount', 'payment_mode', 'balance_after', 'description']
                            available_cols = [col for col in display_cols if col in df.columns]
                            st.dataframe(df[available_cols], use_container_width=True)
                        else:
                            st.info("No transactions found")
            else:
                st.info("No vendors found")
        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")
    
    with tab2:
        st.subheader("Personal Ledger")
        
        try:
            # Get withdrawals
            withdrawals = conn.table("withdrawals")\
                .select("*, daily_shifts!inner(date)")\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            if withdrawals.data and len(withdrawals.data) > 0:
                df = pd.DataFrame(withdrawals.data)
                st.dataframe(df[['created_at', 'amount', 'description']], use_container_width=True)
                
                # Total withdrawals
                total = df['amount'].sum()
                st.metric("Total Withdrawals", f"₹{total:,.2f}")
            else:
                st.info("No withdrawal data found")
        except Exception as e:
            st.error(f"Error loading withdrawals: {str(e)}")

# ============================================
# SETTINGS PAGE
# ============================================
def show_settings():
    """Settings page (admin only)"""
    
    st.title("⚙️ Settings")
    
    conn = init_supabase()
    if not conn:
        st.error("Database connection not available")
        return
    
    tab1, tab2, tab3 = st.tabs(["🏪 Store Settings", "👥 Users", "🏢 Vendors"])
    
    with tab1:
        st.subheader("Store Settings")
        
        with st.form("store_settings_form"):
            store_name = st.text_input("Store Name", value=st.session_state.settings.get('store_name', ''))
            owner_name = st.text_input("Owner Name", value=st.session_state.settings.get('owner_name', ''))
            header_text = st.text_input("Header Text", value=st.session_state.settings.get('header_text', ''))
            footer_text = st.text_input("Footer Text", value=st.session_state.settings.get('footer_text', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                primary_color = st.color_picker("Primary Color", value=st.session_state.settings.get('primary_color', '#2E86AB'))
            with col2:
                secondary_color = st.color_picker("Secondary Color", value=st.session_state.settings.get('secondary_color', '#A23B72'))
            
            submitted = st.form_submit_button("Save Settings")
            
            if submitted:
                st.session_state.settings.update({
                    'store_name': store_name,
                    'owner_name': owner_name,
                    'header_text': header_text,
                    'footer_text': footer_text,
                    'primary_color': primary_color,
                    'secondary_color': secondary_color
                })
                st.success("Settings saved successfully!")
    
    with tab2:
        st.subheader("User Management")
        
        # Get all users
        users = conn.table("users").select("*").order("username").execute()
        
        if users.data and len(users.data) > 0:
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
                
                if submitted and username and password:
                    try:
                        user_data = {
                            'username': username,
                            'password': password,
                            'full_name': full_name,
                            'role': role,
                            'is_active': True
                        }
                        conn.table("users").insert(user_data).execute()
                        st.success(f"User {username} added successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("Vendor Management")
        
        # Get all vendors
        vendors = conn.table("vendors").select("*").order("name").execute()
        
        if vendors.data and len(vendors.data) > 0:
            df = pd.DataFrame(vendors.data)
            st.dataframe(df[['name', 'phone', 'current_balance', 'is_active']], use_container_width=True)
        
        # Add new vendor
        with st.expander("➕ Add New Vendor"):
            with st.form("new_vendor_form"):
                name = st.text_input("Vendor Name")
                phone = st.text_input("Phone")
                opening_balance = st.number_input("Opening Balance", value=0.0)
                
                submitted = st.form_submit_button("Add Vendor")
                
                if submitted and name:
                    try:
                        vendor_data = {
                            'name': name,
                            'phone': phone,
                            'opening_balance': opening_balance,
                            'current_balance': opening_balance,
                            'is_active': True
                        }
                        conn.table("vendors").insert(vendor_data).execute()
                        st.success(f"Vendor {name} added successfully!")
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
