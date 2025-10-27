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
    """Renderuje profesjonalne menu nawigacyjne na górze strony"""
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
    .nav-link {
        padding: 0.75rem 1.5rem;
        color: #6b7280;
        text-decoration: none;
        border-bottom: 3px solid transparent;
        transition: all 0.2s;
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .nav-link:hover {
        color: #111827;
        background: #f9fafb;
    }
    .nav-link.active {
        color: #111827;
        border-bottom-color: #111827;
        font-weight: 600;
    }
    </style>
    
    <div class="nav-menu">
        <a href="streamlit_app.py" class="nav-link" target="_self">Główna</a>
        <a href="pages/1_kryptowaluty.py" class="nav-link" target="_self">Kryptowaluty</a>
        <a href="pages/2_akcje.py" class="nav-link" target="_self">Akcje</a>
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