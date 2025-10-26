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
        
        if st.button("Odśwież teraz", type="primary", width='stretch'):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### Status giełd")
        from config import Config
        missing = Config.validate()
        
        exchange_status = {
            'Binance': 'Binance' not in missing,
            'Bybit': 'Bybit' not in missing,
            'XTB': 'XTB' not in missing
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

def render_asset_cards(assets_data, currency='USD', usd_to_pln=4.0):
    """Renderuje kompaktowe karty z aktywami zamiast szerokich tabel"""
    # Convert to DataFrame if needed
    if isinstance(assets_data, list):
        if not assets_data:
            return
        df = pd.DataFrame(assets_data)
    else:
        df = assets_data
    
    # Check if DataFrame is empty
    if df.empty or len(df) == 0:
        return
    
    # Parse PNL percentage for sorting
    def parse_pnl(pnl_str):
        try:
            return float(str(pnl_str).replace('%', '').replace('+', '').replace('-', ''))
        except:
            return 0
    
    if 'PNL %' in df.columns:
        df['pnl_num'] = df['PNL %'].apply(parse_pnl)
        df = df.sort_values('pnl_num', ascending=False)
    
    # Display cards in grid
    cols_per_row = 3
    rows = []
    for idx in range(0, len(df), cols_per_row):
        rows.append(df.iloc[idx:idx+cols_per_row])
    
    for row in rows:
        cols = st.columns(cols_per_row)
        for col_idx, (_, asset) in enumerate(row.iterrows()):
            with cols[col_idx]:
                # Determine card style based on PNL
                status = asset.get('Status', '⚪')
                card_class = "asset-card-neutral"
                if status == '🟢':
                    card_class = "asset-card-profit"
                elif status == '🔴':
                    card_class = "asset-card-loss"
                
                # Format values
                asset_name = asset.get('Aktywo', asset.get('asset', 'N/A'))
                value_usd = asset.get('Wartość USD', asset.get('Wartość', 'N/A'))
                pnl_pct = asset.get('PNL %', '-')
                
                st.markdown(f"""
                <div class="asset-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="font-size: 1.1rem;">{asset_name}</strong>
                        <span style="font-size: 0.9rem; color: #94a3b8;">{asset.get('Giełda', '')}</span>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem; font-weight: 600;">{value_usd}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8; font-size: 0.85rem;">PNL:</span>
                        <span style="font-weight: 600; color: {'#10b981' if pnl_pct != '-' and float(str(pnl_pct).replace('%', '').replace('+', '').replace('-', '')) > 0 else '#ef4444' if pnl_pct != '-' and float(str(pnl_pct).replace('%', '').replace('+', '').replace('-', '')) < 0 else '#94a3b8'};">{pnl_pct}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_performance_section(title, assets_data, top_n=5):
    """Renderuje sekcję Best/Worst Performers"""
    # Convert to DataFrame if needed
    if isinstance(assets_data, list):
        if not assets_data:
            return
        df = pd.DataFrame(assets_data)
    else:
        df = assets_data
    
    # Check if DataFrame is empty
    if df.empty or len(df) == 0:
        return
    
    # Ensure we have PNL data
    if 'PNL %' not in df.columns:
        return
    
    # Parse PNL percentages
    def parse_pnl(pnl_str):
        try:
            return float(str(pnl_str).replace('%', '').replace('+', '').replace('-', ''))
        except:
            return 0
    
    df['pnl_num'] = df['PNL %'].apply(parse_pnl)
    
    # Sort and get top/bottom
    df_sorted = df.sort_values('pnl_num', ascending=False)
    
    # Best performers
    best = df_sorted.head(top_n)
    worst = df_sorted.tail(top_n)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### Top {top_n} Najlepszych")
        for idx, row in best.iterrows():
            pnl_val = row['pnl_num']
            pnl_class = "performance-good" if pnl_val > 0 else "performance-bad"
            st.markdown(f"""
            <div class="performance-card {pnl_class}">
                <strong>{row.get('Aktywo', row.get('asset', 'N/A'))}</strong><br>
                <span style="color: {'#10b981' if pnl_val > 0 else '#ef4444'}">
                    {pnl_val:+.2f}%
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"#### Top {top_n} Najgorszych")
        for idx, row in worst.iterrows():
            pnl_val = row['pnl_num']
            pnl_class = "performance-good" if pnl_val > 0 else "performance-bad"
            st.markdown(f"""
            <div class="performance-card {pnl_class}">
                <strong>{row.get('Aktywo', row.get('asset', 'N/A'))}</strong><br>
                <span style="color: {'#10b981' if pnl_val > 0 else '#ef4444'}">
                    {pnl_val:+.2f}%
                </span>
            </div>
            """, unsafe_allow_html=True)

def render_diversification_analysis(portfolios, crypto_holdings=None, stocks_holdings=None):
    """Renderuje analizę dywersyfikacji"""
    st.markdown("## 🌍 Analiza Dywersyfikacji")
    
    col1, col2, col3 = st.columns(3)
    
    # Exchange diversification
    with col1:
        exchange_values = {}
        for p in portfolios:
            if p['total_value_usdt'] > 0:
                exchange_values[p['exchange']] = p['total_value_usdt']
        
        total_value = sum(exchange_values.values())
        if total_value > 0:
            st.markdown("### 📊 Podział na giełdy")
            for exchange, value in exchange_values.items():
                percentage = (value / total_value) * 100
                st.metric(exchange, f"{percentage:.1f}%", f"${value:,.0f}")
    
    # Crypto vs Stocks
    with col2:
        crypto_value = sum([p['total_value_usdt'] for p in portfolios if p['exchange'] in ['Binance', 'Bybit']])
        stocks_value = sum([p['total_value_usdt'] for p in portfolios if p['exchange'] == 'XTB'])
        total_value = crypto_value + stocks_value
        
        if total_value > 0:
            st.markdown("### 💼 Podział Crypto vs Akcje")
            crypto_pct = (crypto_value / total_value) * 100
            stocks_pct = (stocks_value / total_value) * 100
            st.metric("Kryptowaluty", f"{crypto_pct:.1f}%", f"${crypto_value:,.0f}")
            st.metric("Akcje", f"{stocks_pct:.1f}%", f"${stocks_value:,.0f}")
    
    # Top asset concentration
    with col3:
        st.markdown("### 🎯 Koncentracja")
        all_assets = []
        for p in portfolios:
            for balance in p['balances']:
                # Use value_usdt if available, otherwise skip (we need value, not quantity)
                value_usdt = balance.get('value_usdt', 0)
                if value_usdt > 0:
                    all_assets.append({
                        'asset': balance['asset'],
                        'value': value_usdt
                    })
        
        if all_assets:
            # Calculate concentration
            df_assets = pd.DataFrame(all_assets)
            df_assets = df_assets.groupby('asset')['value'].sum().reset_index()
            df_assets = df_assets.sort_values('value', ascending=False)
            
            if len(df_assets) > 0:
                total_portfolio_value = df_assets['value'].sum()
                top_asset_pct = (df_assets.iloc[0]['value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                st.metric("Największa pozycja", f"{top_asset_pct:.1f}%", df_assets.iloc[0]['asset'])
