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
    """Render main navigation menu with working buttons"""
    st.markdown("""
    <style>
    .main-nav {
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        padding: 0.5rem 0;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .nav-brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 1rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Brand
    st.markdown('<div class="nav-brand">📊 Portfolio Tracker</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.page = "dashboard"
    
    with col2:
        if st.button("💼 Portfolio", use_container_width=True, key="nav_portfolio"):
            st.session_state.page = "portfolio"
    
    with col3:
        if st.button("💳 Transactions", use_container_width=True, key="nav_transactions"):
            st.session_state.page = "transactions"
    
    with col4:
        if st.button("📈 Analytics", use_container_width=True, key="nav_analytics"):
            st.session_state.page = "analytics"
    
    with col5:
        if st.button("🎯 Goals", use_container_width=True, key="nav_goals"):
            st.session_state.page = "goals"
    
    with col6:
        if st.button("⚙️ Settings", use_container_width=True, key="nav_settings"):
            st.session_state.page = "settings"
    
    st.markdown("---")

def render_navigation_menu():
    """Legacy function - now redirects to main navigation"""
    render_main_navigation()

def load_custom_css():
    """Professional minimalist CSS with 3-color layout"""
    st.markdown("""
    <style>
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
        }
        
        .main {
            padding: 2rem;
            background: #f9fafb;
        }
        
        .block-container {
            background: transparent;
        }
        
        /* Metrics cards - professional card style */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #111827;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            color: #6b7280;
            font-weight: 500;
            letter-spacing: 0.3px;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.75rem;
            font-weight: 500;
        }
        /* Custom metric card container */
        .stMetric {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .stMetric:hover {
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
            transform: translateY(-2px);
            border-color: #2563eb;
        }
        
        /* Buttons - professional blue */
        .stButton>button {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
            transform: translateY(-1px);
        }
        
        .stButton>button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
        }
        
        /* Secondary buttons */
        button[kind="secondary"] {
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
            color: white !important;
        }
        
        /* Dataframes - professional table style */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
        }
        
        /* Info boxes */
        .stAlert {
            border-radius: 8px;
        }
        
        h1 {
            color: #111827;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        h2 {
            color: #111827;
            font-weight: 600;
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        h3 {
            color: #374151;
            font-weight: 600;
            font-size: 1.125rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }
        
        hr {
            border: none;
            height: 1px;
            background: #e5e7eb;
            margin: 2rem 0;
        }
        
        .asset-card {
            background: #ffffff;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        .asset-card-profit {
            border-left: 3px solid #10b981;
        }
        
        .asset-card-loss {
            border-left: 3px solid #ef4444;
        }
        
        .asset-card-neutral {
            border-left: 3px solid #6b7280;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: #ffffff;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-success {
            background: #dcfce7;
            color: #166534;
        }
        
        .status-warning {
            background: #fef3c7;
            color: #92400e;
        }
        
        .status-error {
            background: #fee2e2;
            color: #991b1b;
        }
        
        /* Data card */
        .data-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        
        /* Caption styling */
        .caption-text {
            color: #6b7280;
            font-size: 0.875rem;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render simplified sidebar with essential controls"""
    with st.sidebar:
        st.markdown("### ⚙️ Ustawienia")
        
        # Currency selector
        currency = st.selectbox(
            "Waluta", 
            ["USD", "PLN"], 
            index=0,
            key="sidebar_currency"
        )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Odśwież dane", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Exchange status
        st.markdown("### 📊 Status giełd")
        from config import Config
        try:
            missing = Config.validate()
            
            if 'Binance' not in missing:
                st.success("✅ Binance")
            else:
                st.error("❌ Binance")
                
            if 'Bybit' not in missing:
                st.success("✅ Bybit")
            else:
                st.error("❌ Bybit")
                
            if 'XTB' not in missing:
                st.success("✅ XTB")
            else:
                st.warning("⚠️ XTB (opcjonalne)")
        except Exception as e:
            st.error(f"Błąd konfiguracji: {e}")
        
        st.markdown("---")
        
        # Last update time
        import time
        st.caption(f"Ostatnia aktualizacja: {time.strftime('%H:%M:%S')}")
        
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