"""
Podstrona dla kryptowalut - Binance i Bybit
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Try to import modules with error handling
try:
    from portfolio_tracker import PortfolioTracker
    from config import Config
    from utils import get_usd_to_pln_rate, get_top_assets
    from purchase_prices import PurchasePriceTracker
    from transaction_history import TransactionHistory
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"❌ Błąd importu modułów: {e}")
    st.error("Sprawdź czy wszystkie zależności są zainstalowane i API keys są skonfigurowane.")
    IMPORTS_SUCCESSFUL = False

# Setup
st.set_page_config(
    page_title="Kryptowaluty - Portfolio Tracker",
    page_icon="📊",
    layout="wide"
)

from ui_common import load_custom_css, render_sidebar

load_custom_css()

# Title
st.markdown("""
<div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
    <h1 style="margin: 0;">Kryptowaluty</h1>
    <span style="color: #6b7280; font-size: 0.9rem; font-weight: 400;">Binance • Bybit</span>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Check if API keys are configured
try:
    Config.init()
    missing = Config.validate()
    if missing:
        st.warning(f"⚠️ Brakuje kluczy API: {', '.join(missing)}")
        st.info("💡 Dodaj API keys w Settings → Secrets")
        st.markdown("### Jak dodać API keys:")
        st.markdown("1. Kliknij ⚙️ w prawym górnym rogu")
        st.markdown("2. Wybierz 'Settings' → 'Secrets'")
        st.markdown("3. Kliknij 'Edit secrets'")
        st.markdown("4. Wklej swoje klucze API")
        st.markdown("---")
        st.markdown("### 🔧 Debug Info:")
        st.markdown(f"**Missing keys:** {missing}")
        st.markdown("**Możesz kontynuować i użyć przycisku 'Pobierz z API' poniżej**")
        # Don't stop here - let user continue to see the API button
except Exception as e:
    st.error(f"❌ Błąd konfiguracji: {e}")
    st.markdown("---")
    st.markdown("### 🔧 Debug Info:")
    st.markdown(f"**Error:** {str(e)}")
    st.markdown("**Możesz kontynuować i użyć przycisku 'Pobierz z API' poniżej**")
    # Don't stop here - let user continue to see the API button

# Main content
if not IMPORTS_SUCCESSFUL:
    st.error("⚠️ Aplikacja nie może się uruchomić z powodu błędów importu.")
    st.stop()

# Debug info
st.markdown("### 🔧 Debug Info:")
st.markdown(f"**Imports successful:** {IMPORTS_SUCCESSFUL}")
try:
    Config.init()
    missing = Config.validate()
    st.markdown(f"**Missing API keys:** {missing if missing else 'None'}")
    st.markdown(f"**Binance configured:** {'Yes' if Config.BINANCE_API_KEY and Config.BINANCE_SECRET_KEY else 'No'}")
    st.markdown(f"**Bybit configured:** {'Yes' if Config.BYBIT_API_KEY and Config.BYBIT_SECRET_KEY else 'No'}")
except Exception as e:
    st.markdown(f"**Config error:** {e}")

st.markdown("---")

try:
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_portfolio_data():
        tracker = PortfolioTracker()
        return tracker.get_all_portfolio_data()
    
    @st.cache_data(ttl=3600)
    def get_exchange_rate():
        return get_usd_to_pln_rate()
    
    # Use session state to avoid reloading portfolio on navigation
    if 'portfolios' not in st.session_state:
        with st.spinner("⏳ Ładowanie danych portfolio..."):
            st.session_state.portfolios = get_portfolio_data()
    
    portfolios = st.session_state.portfolios
    usd_to_pln = get_exchange_rate()
    transaction_history = TransactionHistory()
    
    if not portfolios:
        st.warning("Brak danych portfolio.")
        
        # Show API sync button even when no portfolio data
        st.markdown("---")
        st.markdown("### 🔄 Synchronizacja z API")
        st.markdown("Pobierz dane z giełd:")
        
        col_sync1, col_sync2 = st.columns(2)
        
        with col_sync1:
            if st.button("Pobierz z API", type="primary", use_container_width=True):
                try:
                    from auto_sync_transactions import sync_all_transactions
                    with st.spinner("Synchronizowanie..."):
                        sync_all_transactions()
                    st.success("Zsynchronizowano!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")
        
        with col_sync2:
            if st.button("Odśwież portfolio", type="secondary", use_container_width=True):
                st.cache_data.clear()
                if 'portfolios' in st.session_state:
                    del st.session_state.portfolios
                st.rerun()
        
        st.markdown("---")
        
        # Show transaction form even when no portfolio data
        st.markdown("### Dodaj transakcję ręcznie")
        with st.form("add_crypto_transaction_form"):
            exchange_t = st.selectbox("Giełda", ["Binance", "Bybit"])
            asset_t = st.text_input("Aktywo (kryptowaluta)", placeholder="np. BTC, ETH, USDT")
            amount_t = st.number_input("Ilość", min_value=0.0, step=0.00000001, format="%.8f")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                price_t = st.number_input("Cena ($)", min_value=0.0, step=0.01)
                transaction_type_t = st.selectbox("Typ", ["kupno", "sprzedaż"])
            
            with col_form2:
                date_t = st.date_input("Data transakcji")
            
            submitted = st.form_submit_button("Dodaj transakcję", type="primary", use_container_width=True)
            
            if submitted and asset_t and amount_t > 0 and price_t > 0:
                tx_type = "buy" if transaction_type_t == "kupno" else "sell"
                transaction_history.add_transaction(
                    exchange=exchange_t,
                    asset=asset_t.upper(),
                    amount=amount_t,
                    price_usd=price_t,
                    transaction_type=tx_type,
                    date=date_t
                )
                st.success(f"Dodano transakcję: {tx_type} {amount_t} {asset_t.upper()} po ${price_t}")
                st.rerun()
    else:
        # Filter crypto portfolios only
        crypto_portfolios = [p for p in portfolios if p['exchange'] in ['Binance', 'Bybit']]
        
        if not crypto_portfolios:
            st.info("Brak kryptowalut w portfolio.")
        else:
            # Calculate crypto totals
            crypto_value_usd = sum(p['total_value_usdt'] for p in crypto_portfolios)
            crypto_value_pln = crypto_value_usd * usd_to_pln
            
            # Metrics
            st.markdown("## Podsumowanie")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                value_display = crypto_value_usd if currency == 'USD' else crypto_value_pln
                alt_value = crypto_value_pln if currency == 'USD' else crypto_value_usd
                alt_symbol = 'zł' if currency == 'USD' else '$'
                st.metric(
                    "Wartość krypto",
                    f"{value_display:,.2f} {currency}",
                    f"{alt_symbol}{alt_value:,.2f}"
                )
            
            with col2:
                top_assets = get_top_assets(crypto_portfolios, top_n=100)
                total_assets = len([a for a in top_assets if a['value_usdt'] > 1.0])
                st.metric("Aktywa", total_assets)
            
            with col3:
                active_exchanges = len([p for p in crypto_portfolios if p['total_value_usdt'] > 0])
                st.metric("Aktywne giełdy", active_exchanges)
            
            with col4:
                # Calculate PNL for crypto
                crypto_pnl = transaction_history.get_all_pnl(crypto_portfolios)
                total_pnl = sum(p['pnl'] for p in crypto_pnl)
                pnl_display = total_pnl if currency == 'USD' else total_pnl * usd_to_pln
                pnl_color = "+" if total_pnl >= 0 else ""
                st.metric("PNL krypto", f"{pnl_color}{pnl_display:,.2f} {currency}")
            
            st.markdown("---")
            
            # Assets list
            st.markdown("## Aktywa")
            
            top_assets = get_top_assets(crypto_portfolios, top_n=100)
            crypto_assets = [a for a in top_assets if a['value_usdt'] > 1.0]
            
            price_tracker = PurchasePriceTracker()
            
            if crypto_assets:
                # Prepare data with PNL
                assets_data = []
                for asset in crypto_assets:
                    current_price = asset['value_usdt'] / asset['total'] if asset['total'] > 0 else 0
                    
                    # Get PNL from transaction history
                    pnl_data = transaction_history.calculate_pnl(
                        asset['exchange'], 
                        asset['asset'], 
                        current_price, 
                        asset['total']
                    )
                    
                    asset_dict = {
                        'Giełda': asset['exchange'],
                        'Aktywo': asset['asset'],
                        'Wartość USD': f"${asset['value_usdt']:,.2f}",
                        'Wartość PLN': f"{asset['value_usdt'] * usd_to_pln:,.2f} zł",
                        'Ilość': f"{asset['total']:.8f}"
                    }
                    
                    if pnl_data:
                        asset_dict['Zainwestowano'] = f"${pnl_data['invested']:,.2f}"
                        asset_dict['PNL całkowity'] = f"${pnl_data['pnl']:+,.2f}"
                        asset_dict['PNL %'] = f"{pnl_data['pnl_percent']:+.2f}%"
                        asset_dict['Status'] = '🟢' if pnl_data['pnl'] > 0 else '🔴' if pnl_data['pnl'] < 0 else '⚪'
                    else:
                        purchase_price = price_tracker.get_purchase_price(asset['exchange'], asset['asset'])
                        if purchase_price:
                            pnl_percent = ((current_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0
                            pnl = asset['value_usdt'] - (asset['total'] * purchase_price)
                            asset_dict['Zainwestowano'] = f"${asset['total'] * purchase_price:,.2f}"
                            asset_dict['PNL całkowity'] = f"${pnl:+,.2f}"
                            asset_dict['PNL %'] = f"{pnl_percent:+.2f}%"
                            asset_dict['Status'] = '🟢' if pnl > 0 else '🔴' if pnl < 0 else '⚪'
                        else:
                            asset_dict['Zainwestowano'] = "Brak"
                            asset_dict['PNL całkowity'] = "-"
                            asset_dict['PNL %'] = "-"
                            asset_dict['Status'] = '❓'
                    
                    assets_data.append(asset_dict)
                
                df_assets = pd.DataFrame(assets_data)
                
                # View mode toggle
                view_mode = st.radio("**Wyświetl jako:**", ["Tabela", "Karty"], horizontal=True, key="crypto_view_mode")
                
                # Filters
                st.markdown("### Filtry i Sortowanie")
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    filter_exchange = st.multiselect(
                        "Giełda",
                        options=["Binance", "Bybit"],
                        default=["Binance", "Bybit"]
                    )
                
                with col_f2:
                    filter_pnl = st.selectbox(
                        "PNL",
                        options=["Wszystkie", "Na plusie", "Na minusie", "Brak danych"]
                    )
                
                with col_f3:
                    sort_by = st.selectbox(
                        "Sortuj według",
                        options=["Wartość USD", "PNL %", "PNL całkowity", "Aktywo"]
                    )
                
                # Apply filters
                df_filtered = df_assets.copy()
                
                if filter_exchange:
                    df_filtered = df_filtered[df_filtered['Giełda'].isin(filter_exchange)]
                
                if filter_pnl == "Na plusie":
                    df_filtered = df_filtered[df_filtered['Status'] == '🟢']
                elif filter_pnl == "Na minusie":
                    df_filtered = df_filtered[df_filtered['Status'] == '🔴']
                elif filter_pnl == "Brak danych":
                    df_filtered = df_filtered[df_filtered['Status'] == '❓']
                
                # Sort
                if sort_by == "PNL %":
                    df_filtered['PNL_num'] = df_filtered['PNL %'].str.replace('%', '').str.replace('+', '').replace('-', '').astype(float, errors='ignore')
                    df_filtered = df_filtered.sort_values('PNL_num', ascending=False, na_position='last')
                    df_filtered = df_filtered.drop('PNL_num', axis=1)
                elif sort_by == "Wartość USD":
                    df_filtered['Wartość_num'] = df_filtered['Wartość USD'].str.replace('$', '').str.replace(',', '').astype(float, errors='ignore')
                    df_filtered = df_filtered.sort_values('Wartość_num', ascending=False, na_position='last')
                    df_filtered = df_filtered.drop('Wartość_num', axis=1)
                elif sort_by == "Aktywo":
                    df_filtered = df_filtered.sort_values('Aktywo')
                
                # Display based on view mode
                if view_mode == "Karty":
                    from ui_common import render_asset_cards
                    render_asset_cards(df_filtered, currency, usd_to_pln)
                else:
                    st.dataframe(df_filtered, hide_index=True, width='stretch')
                
                # Export
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="Eksportuj do CSV",
                    data=csv,
                    file_name=f"crypto_assets_{time.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    width='stretch'
                )
                
                # Performance section
                st.markdown("---")
                st.markdown("## Top Performers")
                from ui_common import render_performance_section
                render_performance_section("Best/Worst Crypto", df_filtered)
                
                # Purchase price management
                st.markdown("---")
                st.markdown("### Zarządzanie cenami zakupu")
                col_set1, col_set2, col_set3, col_set4 = st.columns(4)
                
                with col_set1:
                    exchange_set = st.selectbox("Giełda", ["Binance", "Bybit"], key="set_exchange")
                with col_set2:
                    assets_list = sorted(list(set([a['asset'] for a in crypto_assets])))
                    asset_set = st.selectbox("Aktywo", assets_list, key="set_asset")
                with col_set3:
                    price_set = st.number_input("Cena zakupu ($)", min_value=0.0, step=0.01, key="set_price")
                with col_set4:
                    st.write("")
                    st.write("")
                    if st.button("Zapisz", type="primary", use_container_width=True):
                        if price_set > 0:
                            price_tracker.set_purchase_price(exchange_set, asset_set, price_set)
                            st.success(f"${price_set} dla {asset_set}")
                            st.rerun()
            else:
                st.info("Brak kryptowalut w portfolio.")
            
            st.markdown("---")
            
            # Transactions
            st.markdown("## Historia Transakcji")
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("### Dodaj transakcję")
                
                # Quick sync
                if st.button("Pobierz z API", type="secondary", use_container_width=True):
                    try:
                        from auto_sync_transactions import sync_all_transactions
                        with st.spinner("Synchronizowanie..."):
                            sync_all_transactions()
                        st.success("Zsynchronizowano!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                
                st.markdown("---")
                
                # Transaction form
                with st.form("add_crypto_transaction_form"):
                    exchange_t = st.selectbox("Giełda", ["Binance", "Bybit"])
                    asset_t = st.text_input("Aktywo (kryptowaluta)", placeholder="np. BTC, ETH, USDT")
                    amount_t = st.number_input("Ilość", min_value=0.0, step=0.00000001, format="%.8f")
                    
                    col_form1, col_form2 = st.columns(2)
                    
                    with col_form1:
                        price_t = st.number_input("Cena ($)", min_value=0.0, step=0.01)
                        transaction_type_t = st.selectbox("Typ", ["kupno", "sprzedaż"])
                    
                    with col_form2:
                        date_t = st.date_input("Data transakcji")
                    
                    submitted = st.form_submit_button("Dodaj transakcję", type="primary", use_container_width=True)
                    
                    if submitted and asset_t and amount_t > 0 and price_t > 0:
                        tx_type = "buy" if transaction_type_t == "kupno" else "sell"
                        transaction_history.add_transaction(
                            exchange=exchange_t,
                            asset=asset_t.upper(),
                            amount=amount_t,
                            price_usd=price_t,
                            transaction_type=tx_type,
                            date=date_t.isoformat()
                        )
                        st.success(f"Dodano {transaction_type_t}: {amount_t} {asset_t.upper()}")
                        st.rerun()
            
            with col_t2:
                st.markdown("### Historia Transakcji")
                
                crypto_transactions = [t for t in transaction_history.transactions if t['exchange'] in ['Binance', 'Bybit']]
                
                if crypto_transactions:
                    recent_tx = crypto_transactions[-10:][::-1]
                    
                    for tx in recent_tx:
                        type_name = "Kupno" if tx['type'] == 'buy' else "Sprzedaż"
                        st.markdown(f"**{type_name}** {tx['asset']} - {tx['amount']:.4f} @ ${tx['price_usd']:.2f}")
                    
                    if len(crypto_transactions) > 10:
                        st.info(f"... i {len(crypto_transactions) - 10} więcej")
                    
                    # Export
                    df_tx = pd.DataFrame(crypto_transactions)
                    csv_tx = df_tx.to_csv(index=False)
                    st.download_button(
                        label="Eksportuj historię",
                        data=csv_tx,
                        file_name=f"crypto_transactions_{time.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        width='stretch'
                    )
                else:
                    st.info("Brak transakcji. Dodaj pierwszą powyżej.")
                
                
                st.markdown("---")
                
                # Exchange details
                st.markdown("## Szczegóły Giełd")
                
                for portfolio in crypto_portfolios:
                    exchange = portfolio['exchange']
                    total_value = portfolio['total_value_usdt']
                    balances = portfolio['balances']
                    
                    if total_value > 0:
                        with st.expander(f"{exchange} - ${total_value:,.2f} USDT ({total_value * usd_to_pln:,.2f} zł)", expanded=False):
                            st.markdown("---")
                            if balances:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Aktywa", len(balances))
                                with col2:
                                    total_coins = sum(b['total'] for b in balances)
                                    st.metric("Ilość", f"{total_coins:.4f}")
                                with col3:
                                    locked_coins = sum(b['locked'] for b in balances)
                                    st.metric("Zablokowane", f"{locked_coins:.4f}")
                                
                                st.markdown("---")
                                st.markdown("#### Lista aktywów")
                                
                                df_balances = pd.DataFrame(balances)
                                df_display = df_balances[['asset', 'total', 'free', 'locked']].copy()
                                df_display.columns = ['Aktywo', 'Całkowita ilość', 'Dostępne', 'Zablokowane']
                                df_display = df_display.sort_values('Całkowita ilość', ascending=False)
                                
                                st.dataframe(df_display, hide_index=True, width='stretch')
                    else:
                        st.info(f"{exchange}: Brak danych")

except Exception as e:
    st.error(f"Błąd: {e}")
    st.exception(e)

