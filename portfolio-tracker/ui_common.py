"""
Common code for all Streamlit pages - professional and consistent design
"""
import streamlit as st
import pandas as pd

def _safe_switch_page(page_name: str):
    """Switch to another page using session state.
    
    This is a compatibility function that works with all Streamlit versions.
    """
    # Map page names to session state values
    page_mapping = {
        "streamlit_app.py": "dashboard",
        "pages/portfolio.py": "portfolio", 
        "pages/transactions.py": "transactions",
        "pages/analytics.py": "analytics",
        "pages/goals_alerts.py": "goals",
        "pages/settings.py": "settings",
        "pages/1_kryptowaluty.py": "crypto",
        "pages/2_akcje.py": "stocks"
    }
    
    if page_name in page_mapping:
        st.session_state.page = page_mapping[page_name]
    else:
        st.error(f"Unknown page: {page_name}")

def setup_page_config():
    """Setup page configuration"""
    st.set_page_config(
        page_title="Portfolio Tracker Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_main_navigation():
    """Render modern, minimalist navigation menu"""
    st.markdown("""
    <style>
    .main-nav {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    .nav-brand {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1.5rem;
        text-align: center;
        letter-spacing: -0.5px;
    }
    .nav-button {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: #ffffff;
        font-weight: 500;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    .nav-button:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-nav">', unsafe_allow_html=True)
    st.markdown('<div class="nav-brand">Portfolio Tracker</div>', unsafe_allow_html=True)
    
    # Navigation buttons with modern styling
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("Dashboard", use_container_width=True, key="nav_dashboard", help="Main dashboard overview"):
            st.session_state.page = "dashboard"
    
    with col2:
        if st.button("Portfolio", use_container_width=True, key="nav_portfolio", help="Portfolio composition"):
            st.session_state.page = "portfolio"
    
    with col3:
        if st.button("Transactions", use_container_width=True, key="nav_transactions", help="Transaction history"):
            st.session_state.page = "transactions"
    
    with col4:
        if st.button("Analytics", use_container_width=True, key="nav_analytics", help="Performance analytics"):
            st.session_state.page = "analytics"
    
    with col5:
        if st.button("Goals", use_container_width=True, key="nav_goals", help="Goals and alerts"):
            st.session_state.page = "goals"
    
    with col6:
        if st.button("Settings", use_container_width=True, key="nav_settings", help="Application settings"):
            st.session_state.page = "settings"
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_navigation_menu():
    """Legacy function - now redirects to main navigation"""
    render_main_navigation()

def load_custom_css():
    """Modern minimalist CSS with professional design"""
    st.markdown("""
    <style>
        /* Global Styles */
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
        }
        
        .main {
            padding: 1rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .block-container {
            background: transparent;
            padding: 0;
        }
        
        /* Modern Metric Cards */
        [data-testid="stMetricValue"] {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1a202c;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            letter-spacing: -0.5px;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
        }
        
        /* Card Containers */
        .stMetric {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 2rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            backdrop-filter: blur(10px);
        }
        
        .stMetric:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* DataFrames */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        
        /* Charts */
        .js-plotly-plot {
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1a202c;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 2rem;
            margin-bottom: 0.75rem;
        }
        
        h3 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        /* Status Badges */
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-success {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
        }
        
        .status-warning {
            background: linear-gradient(135deg, #ed8936, #dd6b20);
            color: white;
        }
        
        .status-error {
            background: linear-gradient(135deg, #f56565, #e53e3e);
            color: white;
        }
        
        /* Info Boxes */
        .stAlert {
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        
        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #5a67d8, #6b46c1);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main {
                padding: 0.5rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.8rem;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render modern, minimalist sidebar"""
    with st.sidebar:
        st.markdown("""
        <style>
        .sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .sidebar-section {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-header"><h3>Settings</h3></div>', unsafe_allow_html=True)
        
        # Currency selector
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        currency = st.selectbox(
            "Currency", 
            ["USD", "PLN"], 
            index=0,
            key="sidebar_currency",
            help="Select display currency"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Refresh button
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.button("Refresh Data", type="primary", use_container_width=True, help="Reload all portfolio data"):
            st.cache_data.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Exchange status
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**Exchange Status**")
        from config import Config
        try:
            missing = Config.validate()
            
            if 'Binance' not in missing:
                st.markdown('<span class="status-badge status-success">Binance ✓</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-error">Binance ✗</span>', unsafe_allow_html=True)
            
            if 'Bybit' not in missing:
                st.markdown('<span class="status-badge status-success">Bybit ✓</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-error">Bybit ✗</span>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Config error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return currency

def render_footer():
    """Render footer according to sitemap"""
    st.markdown("""
    <style>
    .footer {
        background: #f8fafc;
        border-top: 1px solid #e5e7eb;
        padding: 2rem 0;
        margin-top: 4rem;
    }
    .footer-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    .footer-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin-bottom: 2rem;
    }
    .footer-section h3 {
        color: #111827;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .footer-section ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .footer-section li {
        margin-bottom: 0.5rem;
    }
    .footer-section a {
        color: #6b7280;
        text-decoration: none;
        font-size: 0.875rem;
    }
    .footer-section a:hover {
        color: #2563eb;
    }
    .footer-bottom {
        border-top: 1px solid #e5e7eb;
        padding-top: 1rem;
        text-align: center;
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .nav-container {
            flex-direction: column;
            padding: 0 1rem;
        }
        .nav-links {
            flex-direction: column;
            gap: 0.5rem;
            width: 100%;
            margin-top: 1rem;
        }
        .nav-link {
            text-align: center;
            padding: 0.75rem 1rem;
        }
        .hero-title {
            font-size: 2rem !important;
        }
        .hero-subtitle {
            font-size: 1rem !important;
        }
        .metric-card {
            margin-bottom: 1rem;
        }
        .footer-content {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .nav-brand {
            font-size: 1.25rem;
        }
        .hero-title {
            font-size: 1.75rem !important;
        }
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        <div class="footer-container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>Quick Links</h3>
                    <ul>
                        <li><a href="#">Portfolio</a></li>
                        <li><a href="#">Transactions</a></li>
                        <li><a href="#">Analytics</a></li>
                        <li><a href="#">Goals</a></li>
                        <li><a href="#">Settings</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Support</h3>
                    <ul>
                        <li><a href="#">Help Center</a></li>
                        <li><a href="#">Contact Support</a></li>
                        <li><a href="#">Report Bug</a></li>
                        <li><a href="#">Feature Request</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Legal</h3>
                    <ul>
                        <li><a href="#">Privacy Policy</a></li>
                        <li><a href="#">Terms of Service</a></li>
                        <li><a href="#">Cookie Policy</a></li>
                        <li><a href="#">Disclaimer</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Social</h3>
                    <ul>
                        <li><a href="#">Newsletter</a></li>
                        <li><a href="#">Twitter</a></li>
                        <li><a href="#">LinkedIn</a></li>
                        <li><a href="#">Mobile App</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 Portfolio Tracker. All rights reserved.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def add_reset_button():
    """Dodaje przycisk resetu portfolio history"""
    if st.button("Reset History", type="secondary", use_container_width=True):
        import json
        with open('portfolio_history.json', 'w') as f:
            json.dump([], f)
        st.success("Historia portfolio wyczyszczona")
        st.rerun()

def render_performance_section(title, df_filtered):
    """Renderuje sekcję najlepszych/najgorszych performerów"""
    if df_filtered.empty:
        st.info("Brak danych do wyświetlenia")
        return
    
    # Extract PNL percentage from string column
    if 'PNL %' in df_filtered.columns:
        df_filtered = df_filtered.copy()
        df_filtered['PNL_num'] = pd.to_numeric(df_filtered['PNL %'].str.replace('%', '').str.replace('+', ''), errors='coerce')
        df_sorted = df_filtered.sort_values('PNL_num', ascending=False, na_position='last')
        
        col_perf1, col_perf2 = st.columns(2)
        
        with col_perf1:
            st.markdown("#### Najlepsze")
            if len(df_sorted) > 0:
                best = df_sorted.iloc[0]
                asset = best.get('Aktywo', 'N/A')
                exchange = best.get('Giełda', 'N/A')
                pnl_pct = best.get('PNL_num', 0)
                value = best.get('Wartość USD', '$0')
                st.metric(
                    f"{asset} ({exchange})",
                    f"{pnl_pct:+.2f}%",
                    value
                )
        
        with col_perf2:
            st.markdown("#### Najgorsze")
            if len(df_sorted) > 0:
                worst = df_sorted.iloc[-1]
                asset = worst.get('Aktywo', 'N/A')
                exchange = worst.get('Giełda', 'N/A')
                pnl_pct = worst.get('PNL_num', 0)
                value = worst.get('Wartość USD', '$0')
                st.metric(
                    f"{asset} ({exchange})",
                    f"{pnl_pct:+.2f}%",
                    value
                )
    else:
        st.warning("Nie znaleziono kolumny PNL %")

def render_asset_cards(assets_data, currency='USD', usd_to_pln=4.0):
    """Renderuje kompaktowe karty z aktywami zamiast szerokich tabel"""