"""
Podstrona dla akcji i tradycyjnych aktywów
"""
import streamlit as st
import pandas as pd
import time

# Try to import modules with error handling
try:
    from portfolio_tracker import PortfolioTracker
    from config import Config
    from utils import get_usd_to_pln_rate
    from transaction_history import TransactionHistory
    from stock_prices import get_multiple_stock_prices
    from stock_validator import validate_stock_symbol, search_stocks, get_popular_stocks, search_by_isin, get_stock_info
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"❌ Błąd importu modułów: {e}")
    st.error("Sprawdź czy wszystkie zależności są zainstalowane i API keys są skonfigurowane.")
    IMPORTS_SUCCESSFUL = False

# Setup
st.set_page_config(
    page_title="Akcje - Portfolio Tracker",
    page_icon="📊",
    layout="wide"
)

from ui_common import load_custom_css, render_sidebar, render_navigation_menu

load_custom_css()

# Render navigation menu
render_navigation_menu()

# Title
st.markdown("""
<div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
    <h1 style="margin: 0;">Akcje</h1>
    <span style="color: #6b7280; font-size: 0.9rem; font-weight: 400;">XTB</span>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Main content
if not IMPORTS_SUCCESSFUL:
    st.error("⚠️ Aplikacja nie może się uruchomić z powodu błędów importu.")
    st.stop()

try:
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_portfolio_data():
        tracker = PortfolioTracker()
        return tracker.get_all_portfolios()
    
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
    
    # Get transactions (no XTB, just manual entries)
    transactions = [t for t in transaction_history.transactions if t['exchange'] == 'Manual']
    
    if not transactions:
        st.info("Nie masz jeszcze żadnych transakcji z akcjami. Dodaj pierwszą transakcję poniżej.")
        st.markdown("---")
    else:
        # Calculate holdings
        holdings = {}
        for tx in transactions:
            asset = tx['asset']
            if asset not in holdings:
                holdings[asset] = {'amount': 0, 'total_cost': 0, 'transactions': []}
            
            if tx['transaction_type'] == 'buy':
                holdings[asset]['amount'] += tx['amount']
                holdings[asset]['total_cost'] += tx['amount'] * tx['price_usd']
            else:  # sell
                holdings[asset]['amount'] -= tx['amount']
                avg_cost = holdings[asset]['total_cost'] / (holdings[asset]['amount'] + tx['amount']) if (holdings[asset]['amount'] + tx['amount']) > 0 else 0
                holdings[asset]['total_cost'] -= avg_cost * tx['amount']
            
            holdings[asset]['transactions'].append(tx)
        
        # Filter out sold positions
        holdings = {k: v for k, v in holdings.items() if v['amount'] > 0}
        
        if holdings:
            # ==========================================
            # SEKCJA 1: PODSUMOWANIE (METRICS)
            # ==========================================
            st.markdown("## Podsumowanie")
            
            # Calculate totals
            stock_symbols = list(holdings.keys())
            current_prices = get_multiple_stock_prices(stock_symbols)
            
            total_value = sum(data['amount'] * current_prices.get(asset, 0) for asset, data in holdings.items())
            total_invested = sum(data['total_cost'] for data in holdings.values())
            total_pnl = total_value - total_invested
            total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                value_display = total_value if currency == 'USD' else total_value * usd_to_pln
                alt_value = total_value * usd_to_pln if currency == 'USD' else total_value
                alt_symbol = 'zł' if currency == 'USD' else '$'
                st.metric(
                    "Wartość akcji",
                    f"{value_display:,.2f} {currency}",
                    f"{alt_symbol}{alt_value:,.2f}"
                )
            
            with col2:
                st.metric("Aktywa", len(holdings))
            
            with col3:
                pnl_display = total_pnl if currency == 'USD' else total_pnl * usd_to_pln
                pnl_color = "+" if total_pnl >= 0 else ""
                st.metric("PNL", f"{pnl_color}{pnl_display:,.2f} {currency}")
            
            with col4:
                st.metric("ROI", f"{total_pnl_percent:.2f}%")
            
            # Przyciski odświeżania
            st.markdown("---")
            col_refresh1, col_refresh2 = st.columns(2)
            
            with col_refresh1:
                if st.button("🔄 Odśwież dane", type="secondary", use_container_width=True):
                    st.cache_data.clear()
                    if 'portfolios' in st.session_state:
                        del st.session_state.portfolios
                    st.success("✅ Cache wyczyszczony - dane zostaną ponownie załadowane")
                    st.rerun()
            
            with col_refresh2:
                if st.button("📊 Wyczyść portfolio", type="secondary", use_container_width=True):
                    st.cache_data.clear()
                    st.success("✅ Portfolio wyczyszczone")
                    st.rerun()
            
            st.markdown("---")
            
            # ==========================================
            # SEKCJA 2: MOJE AKCJE (HOLDINGS)
            # ==========================================
            st.markdown("## Akcje")
            
            # Get current prices
            st.info(f"Pobieranie aktualnych cen dla {len(stock_symbols)} aktywów...")
            current_prices = get_multiple_stock_prices(stock_symbols)
            
            # Prepare display data
            xtb_data = []
            for asset, data in holdings.items():
                avg_price = data['total_cost'] / data['amount'] if data['amount'] > 0 else 0
                current_price = current_prices.get(asset, avg_price)
                
                pnl = data['amount'] * current_price - data['total_cost']
                pnl_percent = (pnl / data['total_cost'] * 100) if data['total_cost'] > 0 else 0
                
                xtb_data.append({
                    'Aktywo': asset,
                    'Ilość': f"{data['amount']:.2f}",
                    'Średnia cena zakupu': f"${avg_price:.2f}",
                    'Obecna cena': f"${current_price:.2f}",
                    'Wartość': f"${data['amount'] * current_price:.2f}",
                    'Zainwestowano': f"${data['total_cost']:.2f}",
                    'PNL': f"${pnl:.2f}",
                    'PNL %': f"{pnl_percent:.2f}%",
                    'Status': '🟢' if pnl > 0 else '🔴' if pnl < 0 else '⚪'
                })
            
            df_xtb = pd.DataFrame(xtb_data)
            
            # Filters
            st.markdown("### Filtry i Sortowanie")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filter_pnl = st.selectbox(
                    "PNL",
                    options=["Wszystkie", "Na plusie", "Na minusie"]
                )
            
            with col_f2:
                sort_by = st.selectbox(
                    "Sortuj według",
                    options=["Wartość", "PNL %", "PNL", "Aktywo"]
                )
            
            # Apply filters
            df_filtered = df_xtb.copy()
            
            if filter_pnl == "Na plusie":
                df_filtered = df_filtered[df_filtered['Status'] == '🟢']
            elif filter_pnl == "Na minusie":
                df_filtered = df_filtered[df_filtered['Status'] == '🔴']
            
            # Sort
            if sort_by == "PNL %":
                df_filtered['PNL_num'] = df_filtered['PNL %'].str.replace('%', '').str.replace('+', '').replace('-', '').astype(float, errors='ignore')
                df_filtered = df_filtered.sort_values('PNL_num', ascending=False, na_position='last')
                df_filtered = df_filtered.drop('PNL_num', axis=1)
            elif sort_by == "Wartość":
                df_filtered['Wartość_num'] = df_filtered['Wartość'].str.replace('$', '').str.replace(',', '').astype(float, errors='ignore')
                df_filtered = df_filtered.sort_values('Wartość_num', ascending=False, na_position='last')
                df_filtered = df_filtered.drop('Wartość_num', axis=1)
            elif sort_by == "Aktywo":
                df_filtered = df_filtered.sort_values('Aktywo')
            
            st.dataframe(df_filtered, hide_index=True, use_container_width=True)
            
            # Export
            csv_xtb = df_filtered.to_csv(index=False)
            st.download_button(
                label="Eksportuj akcje do CSV",
                data=csv_xtb,
                file_name=f"stocks_{time.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Performance section
            st.markdown("---")
            st.markdown("## Top Performers")
            from ui_common import render_performance_section
            render_performance_section("Best/Worst Stocks", df_filtered)
            
            st.markdown("---")
        
        # ==========================================
        # SEKCJA 3: HISTORIA TRANSAKCJI
        # ==========================================
        st.markdown("## Historia Transakcji")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("### Dodaj transakcję")
            
            # Selection method
            search_method = st.radio(
                "**Wybierz metodę dodawania:**",
                ["Symbol ticker", "ISIN", "Popularne symbole"],
                horizontal=True
            )
            
            # Show popular stocks
            if search_method == "Popularne symbole":
                st.markdown("### Popularne symbole akcji")
                popular_stocks = get_popular_stocks()
                
                cols = st.columns(3)
                for idx, (symbol, name) in enumerate(list(popular_stocks.items())[:15]):
                    with cols[idx % 3]:
                        st.markdown(f"**{symbol}** - *{name}*")
                
                if st.checkbox("Pokaż więcej symboli", key="show_more_stocks"):
                    with st.expander("Szukaj symbolu lub nazwy", expanded=True):
                        search_query = st.text_input("Wyszukaj:", key="stock_search_extended")
                        
                        if search_query:
                            filtered = {k: v for k, v in popular_stocks.items() 
                                      if search_query.upper() in k.upper() or search_query.upper() in v.upper()}
                            
                            if filtered:
                                st.markdown(f"**Znaleziono {len(filtered)} wyników:**")
                                cols2 = st.columns(3)
                                for idx, (symbol, name) in enumerate(filtered.items()):
                                    with cols2[idx % 3]:
                                        st.markdown(f"**{symbol}** - {name}")
                            else:
                                st.info("Nie znaleziono. Spróbuj: AAPL, TSLA, MSFT")
                        else:
                            cols3 = st.columns(3)
                            for idx, (symbol, name) in enumerate(list(popular_stocks.items())[15:]):
                                with cols3[idx % 3]:
                                    st.markdown(f"**{symbol}** - {name}")
            
            st.markdown("---")
            
            # ISIN search form (if ISIN method)
            if search_method == "ISIN":
                st.info("ISIN - International Securities Identification Number (np. US0378331005 dla Apple)")
                
                with st.form("isin_search_form"):
                    identifier_t = st.text_input(
                        "Kod ISIN", 
                        placeholder="np. US0378331005",
                        key="isin_input"
                    )
                    search_btn = st.form_submit_button("Znajdź symbol", use_container_width=True)
                    
                    if search_btn and identifier_t:
                        with st.spinner("Szukanie symbolu..."):
                            symbol, stock_name = search_by_isin(identifier_t.upper())
                            if symbol:
                                st.success(f"Znaleziono: **{symbol}** - {stock_name}")
                                st.session_state['found_symbol'] = symbol
                                st.session_state['found_name'] = stock_name
                            else:
                                st.error("Nie znaleziono symbolu dla tego ISIN")
                                st.session_state['found_symbol'] = None
            
            # Display found symbol or prompt
            if st.session_state.get('found_symbol'):
                st.success(f"**Symbol:** {st.session_state['found_symbol']} | **Nazwa:** {st.session_state['found_name']}")
            elif search_method == "ISIN":
                st.warning("Najpierw wprowadź ISIN i kliknij 'Znajdź symbol'")
            
            st.markdown("---")
            
            # Transaction form
            with st.form("add_stock_transaction_form"):
                st.markdown("### Szczegóły transakcji")
                
                if search_method == "ISIN":
                    # Use found symbol from ISIN search
                    asset_t = st.session_state.get('found_symbol', '')
                    if asset_t:
                        st.text_input("Symbol akcji", value=asset_t, disabled=True)
                else:  # Symbol method
                    asset_t = st.text_input(
                        "Symbol akcji/aktywa", 
                        placeholder="np. AAPL, TSLA, MSFT, EURUSD",
                        help="Wpisz symbol ticker z Yahoo Finance"
                    )
                
                amount_t = st.number_input("Ilość akcji/lotów", min_value=0.0, step=0.01, format="%.2f")
                
                col_form1, col_form2 = st.columns(2)
                
                with col_form1:
                    price_t = st.number_input("Cena ($)", min_value=0.0, step=0.01)
                    transaction_type_t = st.selectbox("Typ", ["kupno", "sprzedaż"])
                
                with col_form2:
                    date_t = st.date_input("Data transakcji")
                    commission_t = st.number_input("Prowizja ($)", min_value=0.0, step=0.01, value=0.0, help="Opcjonalna prowizja")
                
                # Additional notes
                notes_t = st.text_area("Uwagi (opcjonalne)", placeholder="Dodatkowe informacje o transakcji...")
                
                submitted = st.form_submit_button("Dodaj transakcję", type="primary", use_container_width=True)
                
                if submitted:
                    # Validate all inputs
                    errors = []
                    
                    if not asset_t:
                        errors.append("Wprowadź symbol akcji/aktywa")
                    
                    if amount_t <= 0:
                        errors.append("Ilość musi być większa od 0")
                    
                    if price_t <= 0:
                        errors.append("Cena musi być większa od 0")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                        st.stop()
                    
                    # Validate stock symbol
                    is_valid, stock_name = validate_stock_symbol(asset_t.upper())
                    if not is_valid:
                        st.error(f"Symbol '{asset_t.upper()}' nie został znaleziony. Sprawdź czy jest poprawny.")
                        st.stop()
                    
                    # Add transaction
                    tx_type = "buy" if transaction_type_t == "kupno" else "sell"
                    
                    # Calculate total value (including commission)
                    total_value = amount_t * price_t + commission_t
                    
                    transaction_history.add_transaction(
                        exchange="Manual",
                        asset=asset_t.upper(),
                        amount=amount_t,
                        price_usd=price_t,
                        transaction_type=tx_type,
                        date=date_t.isoformat()
                    )
                    
                    # Clear ISIN session state after successful transaction
                    if search_method == "ISIN":
                        st.session_state['found_symbol'] = None
                        st.session_state['found_name'] = None
                    
                    # Show confirmation
                    st.success(f"Dodano {transaction_type_t}: {amount_t} {asset_t.upper()} @ ${price_t:.2f}")
                    if commission_t > 0:
                        st.info(f"Wartość całkowita: ${total_value:.2f} (w tym prowizja: ${commission_t:.2f})")
                    if notes_t:
                        st.info(f"Uwagi: {notes_t}")
                    
                    st.rerun()
        
        with col_t2:
            st.markdown("### Historia Transakcji")
            
            if transactions:
                recent_tx = transactions[-10:][::-1]
                
                for tx in recent_tx:
                    type_name = "Kupno" if tx['type'] == 'buy' else "Sprzedaż"
                    st.markdown(f"**{type_name}** {tx['asset']} - {tx['amount']:.2f} akcji @ ${tx['price_usd']:.2f}")
                
                if len(transactions) > 10:
                    st.info(f"... i {len(transactions) - 10} więcej")
                
                # Export
                df_tx = pd.DataFrame(transactions)
                csv_tx = df_tx.to_csv(index=False)
                st.download_button(
                    label="Eksportuj historię",
                    data=csv_tx,
                    file_name=f"stocks_transactions_{time.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("Brak transakcji. Dodaj pierwszą po lewej stronie.")

except Exception as e:
    st.error(f"Błąd: {e}")
    st.exception(e)
