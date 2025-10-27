"""
Wspólny kod dla wszystkich podstron Streamlit - profesjonalny i spójny design
"""
import streamlit as st
import pandas as pd

def setup_page_config():
    """Setup strony"""
    st.set_page_config(
        page_title="Portfolio Tracker Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_navigation_menu():
    """Renderuje menu nawigacyjne na górze strony"""
    st.markdown("""
    <style>
    .nav-menu {
        display: flex;
        gap: 1rem;
        padding: 1rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .nav-link {
        padding: 0.5rem 1rem;
        color: #6b7280;
        text-decoration: none;
        border-radius: 4px;
        transition: all 0.2s;
    }
    .nav-link:hover {
        background: #f3f4f6;
        color: #111827;
    }
    .nav-link.active {
        background: #111827;
        color: white;
    }
    </style>
    
    <div class="nav-menu">
        <a href="./" class="nav-link">🏠 Główna</a>
        <a href="./1_Kryptowaluty" class="nav-link">💎 Kryptowaluty</a>
        <a href="./2_Akcje" class="nav-link">📈 Akcje</a>
    </div>
    """, unsafe_allow_html=True)

def load_custom_css():
    """Minimalistyczny CSS"""
    st.markdown("""
    <style>
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .main {
            padding: 2rem;
            background: #ffffff;
        }
        
        .block-container {
            background: transparent;
        }
        
        .stMetric {
            background: #ffffff;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
        }
        
        h1 {
            color: #111827;
            font-weight: 600;
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
            font-weight: 500;
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
        
        .stButton>button {
            background: #111827;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        .stButton>button:hover {
            background: #374151;
        }
        
        .asset-card {
            background: #ffffff;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
            margin-bottom: 0.5rem;
        }
        
        .asset-card-profit {
            border-left: 2px solid #10b981;
        }
        
        .asset-card-loss {
            border-left: 2px solid #ef4444;
        }
        
        .asset-card-neutral {
            border-left: 2px solid #e5e7eb;
        }
        
        .performance-card {
            background: #ffffff;
            padding: 0.75rem;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
            margin-bottom: 0.5rem;
        }
        
        .performance-good {
            border-left: 2px solid #10b981;
        }
        
        .performance-bad {
            border-left: 2px solid #ef4444;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar z kontrolami"""
    with st.sidebar:
        st.header("Kontrola")
        
        st.markdown("### Waluta")
        currency = st.selectbox("Wybierz walutę", ["USD", "PLN"], index=0, label_visibility="collapsed")
        
        st.markdown("---")
        
        st.markdown("### Odświeżanie")
        auto_refresh = st.checkbox("Auto-odświeżanie", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Interwał (sek)", 10, 300, 60)
        
        if st.button("Odśwież teraz", type="primary", use_container_width=True):
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
        st.markdown(f"**Ostatnia aktualizacja:**")
        st.markdown(f"*{time.strftime('%H:%M:%S')}*")
    
    return currency

def add_reset_button():
    """Dodaje przycisk resetu portfolio history"""
    if st.button("🗑️ Reset history", type="secondary", use_container_width=True):
        import json
        with open('portfolio_history.json', 'w') as f:
            json.dump([], f)
        st.success("✅ Historia portfolio wyczyszczona")
        st.rerun()

def render_asset_cards(assets_data, currency='USD', usd_to_pln=4.0):
    """Renderuje kompaktowe karty z aktywami zamiast szerokich tabel"""