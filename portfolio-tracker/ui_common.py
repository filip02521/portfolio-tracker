"""
Common code for all Streamlit pages - professional and consistent design
"""
import streamlit as st
import pandas as pd

def _safe_switch_page(page_name: str):
    """Switch to another page if supported by Streamlit, otherwise fall back.

    If `st.switch_page` is available (newer Streamlit), use it. Otherwise set a
    query param and rerun to allow manual handling in pages.
    """
    try:
        if hasattr(st, "switch_page"):
            st.switch_page(page_name)
        else:
            # Fallback: set a query param and rerun. Pages can read this if needed.
            try:
                st.experimental_set_query_params(_page=page_name)
            except Exception:
                # If even experimental_set_query_params isn't available, do nothing
                pass
            # Avoid programmatic rerun here (can cause recursion in some
            # Streamlit/runtime versions). Instead, set a query param so pages
            # can detect navigation intent, and render a link fallback.
            try:
                st.experimental_set_query_params(_page=page_name)
            except Exception:
                pass
            # Provide a clickable link as a last-resort fallback
            st.markdown(f"[Open {page_name}]()")
    except Exception:
        # Prevent any navigation helper from raising inside the UI rendering
        return

def setup_page_config():
    """Setup page configuration"""
    st.set_page_config(
        page_title="Portfolio Tracker Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_navigation_menu():
    """Render professional navigation menu at the top of the page"""
    st.markdown("""
    <style>
    .nav-menu {
        display: flex;
        gap: 0;
        padding: 0;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 2rem;
        background: #ffffff;
    }
    .nav-button {
        padding: 0.75rem 1.5rem;
        border: none;
        background: transparent;
        color: #6b7280;
        cursor: pointer;
        text-decoration: none;
        border-bottom: 3px solid transparent;
        transition: all 0.2s;
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .nav-button:hover {
        color: #111827;
        background: #f9fafb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
    
    with col_nav1:
        if st.button("Dashboard", key="nav_main", use_container_width=True):
            _safe_switch_page("streamlit_app.py")
    
    with col_nav2:
        if st.button("Cryptocurrencies", key="nav_crypto", use_container_width=True):
            _safe_switch_page("pages/1_kryptowaluty.py")
    
    with col_nav3:
        if st.button("Stocks", key="nav_stocks", use_container_width=True):
            _safe_switch_page("pages/2_akcje.py")

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
    """Render sidebar with controls"""
    with st.sidebar:
        st.header("Controls")
        
        st.markdown("### Currency")
        currency = st.selectbox("Select currency", ["USD", "PLN"], index=0, label_visibility="collapsed")
        
        st.markdown("---")
        
        st.markdown("### Refresh")
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        if auto_refresh:
            _refresh_interval = st.slider("Interval (sec)", 10, 300, 60)
        
        if st.button("Refresh Now", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Reset history button
        add_reset_button()
        
        st.markdown("---")
        
        st.markdown("### Status giełd")
        from config import Config
        missing = Config.validate()
        
        exchange_status = {
            'Binance': 'Binance' not in missing,
            'Bybit': 'Bybit' not in missing
        }
        
        for exchange, configured in exchange_status.items():
            if configured:
                st.success(f"{exchange}")
            else:
                st.warning(f"{exchange}")
        
        st.markdown("---")
        import time
        st.markdown("**Ostatnia aktualizacja:**")
        st.markdown(f"*{time.strftime('%H:%M:%S')}*")
    
    return currency

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