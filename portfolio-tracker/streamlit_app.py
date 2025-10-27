"""
Professional Portfolio Tracker Dashboard - Main Summary Page
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time

# Try to import portfolio tracker with error handling
try:
    from portfolio_tracker import PortfolioTracker
    from config import Config
    from utils import get_usd_to_pln_rate, calculate_diversification
    from transaction_history import TransactionHistory
    from portfolio_history import PortfolioHistory
    from stock_prices import get_multiple_stock_prices
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"❌ Błąd importu modułów: {e}")
    st.error("Sprawdź czy wszystkie zależności są zainstalowane i API keys są skonfigurowane.")
    IMPORTS_SUCCESSFUL = False

# Page configuration
st.set_page_config(
    page_title="Portfolio Tracker Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimalist CSS
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
    
    .stSidebar {
        background: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("""
<div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
    <h1 style="margin: 0;">Portfolio Tracker</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Panel Sterowania")
    
    if not IMPORTS_SUCCESSFUL:
        st.error("⚠️ Aplikacja nie może się uruchomić z powodu błędów importu.")
        st.stop()
    
    # Initialize configuration
    try:
        Config.init()  # Make sure config is loaded
        missing = Config.validate()
        if missing:
            st.warning(f"⚠️ Brakuje kluczy API: {', '.join(missing)}")
            st.info("💡 API keys są konfigurowane w Railway")
            st.markdown("---")
            st.markdown("**Aby kontynuować bez API:**")
            st.markdown("- Przejdź do zakładki 'Kryptowaluty'")
            st.markdown("- Użyj przycisku 'Pobierz z API'")
            # Don't stop here - let user navigate to other pages
        else:
            st.success("✅ Konfiguracja API załadowana")
    except Exception as e:
        st.error(f"❌ Błąd konfiguracji: {e}")
    
    st.markdown("### Waluta")
    currency = st.selectbox("Wybierz walutę", ["USD", "PLN"], index=0, label_visibility="collapsed")
    
    st.markdown("---")
    
    st.markdown("### Odświeżanie")
    auto_refresh = st.checkbox("Auto-odświeżanie", value=False)
    if auto_refresh:
        refresh_interval = st.slider("Interwał (sek)", 10, 300, 60)
    
    if st.button("Odśwież teraz", type="primary", use_container_width=True):
        st.cache_data.clear()
        if 'portfolios' in st.session_state:
            del st.session_state.portfolios
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### Status giełd")
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
    if 'last_update' in st.session_state:
        last_update_time = time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))
        st.markdown(f"**Ostatnia aktualizacja:**")
        st.markdown(f"*{last_update_time}*")
        st.caption(f"Cache: 5 minut")

# Main content
try:
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_portfolio_data():
        tracker = PortfolioTracker()
        data = tracker.get_all_portfolios()
        
        return data
    
    @st.cache_data(ttl=3600)
    def get_exchange_rate():
        return get_usd_to_pln_rate()
    
    # Use session state to avoid reloading portfolio on navigation
    if 'portfolios' not in st.session_state:
        with st.spinner("⏳ Ładowanie danych portfolio..."):
            st.session_state.portfolios = get_portfolio_data()
            st.session_state.last_update = time.time()
    
    portfolios = st.session_state.portfolios
    usd_to_pln = get_exchange_rate()
    
    portfolio_history = PortfolioHistory()
    transaction_history = TransactionHistory()
    
    # Calculate totals
    if portfolios:
        total_value_usd = sum(p['total_value_usdt'] for p in portfolios)
        total_value_pln = total_value_usd * usd_to_pln
        
        # Save current portfolio value to history
        portfolio_history.add_snapshot(total_value_usd, total_value_pln)
        
        # Calculate total PNL
        all_pnl = transaction_history.get_all_pnl(portfolios)
        total_pnl = sum(p['pnl'] for p in all_pnl)
        total_invested = sum(p['invested'] for p in all_pnl)
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        # ==========================================
        # SEKCJA 1: PODSUMOWANIE PORTFOLIO
        # ==========================================
        st.markdown("## Podsumowanie Portfolio")
        st.markdown("Przegląd wartości Twojego portfolio na wszystkich giełdach")
        
        # First row: Value and PNL
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            value_display = total_value_usd if currency == 'USD' else total_value_pln
            alt_value = total_value_pln if currency == 'USD' else total_value_usd
            alt_symbol = 'zł' if currency == 'USD' else '$'
            st.metric(
                "Wartość portfolio",
                f"{value_display:,.2f} {currency}",
                f"{alt_symbol}{alt_value:,.2f}"
            )
        
        with col2:
            pnl_display = total_pnl if currency == 'USD' else total_pnl * usd_to_pln
            pnl_symbol = '$' if currency == 'USD' else 'zł'
            pnl_color = "+" if total_pnl >= 0 else ""
            st.metric(
                "Całkowity PNL",
                f"{pnl_color}{pnl_display:,.2f} {currency}",
                f"{pnl_color}{total_pnl_percent:.2f}%"
            )
        
        with col3:
            active_exchanges = len([p for p in portfolios if p['total_value_usdt'] > 0])
            st.metric("Aktywne giełdy", active_exchanges)
        
        with col4:
            total_assets = sum(len(p['balances']) for p in portfolios)
            st.metric("Aktywa", total_assets)
        
        # Second row: Invested amount
        col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
        
        with col_inv1:
            invested_display = total_invested if currency == 'USD' else total_invested * usd_to_pln
            st.metric("Zainwestowano", f"{invested_display:,.2f} {currency}")
        
        with col_inv2:
            roi = (total_value_usd / total_invested * 100) if total_invested > 0 else 0
            st.metric("ROI", f"{roi:.2f}%")
        
        with col_inv3:
            diversification = calculate_diversification(portfolios)
            st.metric("Giełdy", diversification['total_exchanges'])
        
        with col_inv4:
            avg_return = total_pnl_percent / len(all_pnl) if all_pnl else 0
            st.metric("Śr. zwrot", f"{avg_return:.2f}%")
        
        # Przyciski odświeżania
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
        
        # Chart section
        st.markdown("---")
        st.markdown("### Wykres Wartości Portfolio w Czasie")
        
        chart_data = portfolio_history.get_chart_data(days=30)
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'])
            df_chart = df_chart.sort_values('timestamp')
            
            chart_value = 'value_usd' if currency == 'USD' else 'value_pln'
            
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Scatter(
                x=df_chart['timestamp'],
                y=df_chart[chart_value],
                mode='lines+markers',
                name='Wartość portfolio',
                line=dict(color='#3182ce', width=3),
                marker=dict(size=4),
                fill='tonexty',
                fillcolor='rgba(49, 130, 206, 0.1)'
            ))
            
            fig_timeline.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Data",
                yaxis_title=f"Wartość ({currency})",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12)
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Brak danych historycznych. Dane będą zbierane automatycznie.")
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 2: WIZUALIZACJA ALOKACJI
        # ==========================================
        st.markdown("## Wizualizacja Alokacji")
        st.markdown("Podział wartości między poszczególne giełdy")
        
        chart_data = []
        for portfolio in portfolios:
            if portfolio['total_value_usdt'] > 0:
                chart_data.append({
                    'Exchange': portfolio['exchange'],
                    'Value': portfolio['total_value_usdt']
                })
        
        if chart_data:
            col1, col2 = st.columns(2)
            
            with col1:
                df_chart = pd.DataFrame(chart_data)
                fig_pie = go.Figure(data=[go.Pie(
                    labels=df_chart['Exchange'],
                    values=df_chart['Value'],
                    hole=0.4,
                    marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c'],
                    textinfo='label+percent',
                    textfont_size=14
                )])
                fig_pie.update_layout(
                    showlegend=True,
                    height=400,
                    title="Podział na giełdy",
                    font=dict(size=14)
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                fig_bar = go.Figure(data=[go.Bar(
                    x=df_chart['Exchange'],
                    y=df_chart['Value'],
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                    text=[f"${val:,.0f}" for val in df_chart['Value']],
                    textposition='outside'
                )])
                fig_bar.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis_title="Wartość (USDT)",
                    font=dict(size=14)
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 3: WYDAJNOŚĆ I METRYKI RYZYKA
        # ==========================================
        st.markdown("## Wydajność i Metryki Ryzyka")
        
        chart_data_history = portfolio_history.get_chart_data(days=30)
        
        if chart_data_history and len(chart_data_history) > 1:
            import numpy as np
            
            df_history = pd.DataFrame(chart_data_history)
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            df_history = df_history.sort_values('timestamp')
            
            col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
            
            with col_perf1:
                today_value = df_history['value_usd'].iloc[-1]
                yesterday_value = df_history['value_usd'].iloc[-2] if len(df_history) > 1 else today_value
                today_change = today_value - yesterday_value
                today_change_pct = (today_change / yesterday_value * 100) if yesterday_value > 0 else 0
                st.metric("Dzisiaj", f"{today_change:+,.2f} {currency}", f"{today_change_pct:+.2f}%")
            
            with col_perf2:
                week_ago_value = df_history['value_usd'].iloc[0] if len(df_history) >= 7 else df_history['value_usd'].iloc[0]
                week_change = today_value - week_ago_value
                week_change_pct = (week_change / week_ago_value * 100) if week_ago_value > 0 else 0
                st.metric("Tydzień", f"{week_change:+,.2f} {currency}", f"{week_change_pct:+.2f}%")
            
            with col_perf3:
                df_history['daily_return'] = df_history['value_usd'].pct_change()
                volatility = df_history['daily_return'].std() * 100 * np.sqrt(252)
                st.metric("Volatility", f"{volatility:.2f}%", "roczna")
            
            with col_perf4:
                df_history['cummax'] = df_history['value_usd'].cummax()
                df_history['drawdown'] = (df_history['value_usd'] - df_history['cummax']) / df_history['cummax'] * 100
                max_drawdown = df_history['drawdown'].min()
                st.metric("Max Drawdown", f"{max_drawdown:.2f}%", "największa strata")
        else:
            st.info("Potrzebujemy więcej danych historycznych aby obliczyć metryki. Dane będą zbierane automatycznie.")
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 4: PODZIAŁ KRYPTO vs STOCKS
        # ==========================================
        st.markdown("## Podział Portfolio")
        st.markdown("Podsumowanie kryptowalut vs akcji")
        
        # Separate crypto and stocks
        crypto_portfolios = [p for p in portfolios if p['exchange'] in ['Binance', 'Bybit']]
        stocks_portfolios = [p for p in portfolios if p['exchange'] == 'XTB']
        
        crypto_value = sum(p['total_value_usdt'] for p in crypto_portfolios)
        stocks_value = sum(p['total_value_usdt'] for p in stocks_portfolios)
        
        col_div1, col_div2 = st.columns(2)
        
        with col_div1:
            st.markdown("### Kryptowaluty")
            value_display = crypto_value if currency == 'USD' else crypto_value * usd_to_pln
            st.metric("Wartość", f"{value_display:,.2f} {currency}")
            
            # Get crypto PNL
            crypto_pnl = transaction_history.get_all_pnl(crypto_portfolios)
            crypto_total_pnl = sum(p['pnl'] for p in crypto_pnl)
            limit_currency_symbol = 'zł' if currency == 'USD' else '$'
            limit_pnl_display = crypto_total_pnl if currency == 'USD' else crypto_total_pnl * usd_to_pln
            pnl_color = "+" if crypto_total_pnl >= 0 else ""
            st.metric("PNL", f"{pnl_color}{limit_pnl_display:,.2f} {currency}")
            
            st.markdown("**Przejdź do sekcji:**")
            st.markdown("👉 Użyj nawigacji w sidebarze")
        
        with col_div2:
            st.markdown("### Akcje")
            value_display = stocks_value if currency == 'USD' else stocks_value * usd_to_pln
            st.metric("Wartość", f"{value_display:,.2f} {currency}")
            
            # Get stocks PNL
            stocks_pnl = transaction_history.get_all_pnl(stocks_portfolios)
            stocks_total_pnl = sum(p['pnl'] for p in stocks_pnl)
            limit_pnl_display = stocks_total_pnl if currency == 'USD' else stocks_total_pnl * usd_to_pln
            pnl_color = "+" if stocks_total_pnl >= 0 else ""
            st.metric("PNL", f"{pnl_color}{limit_pnl_display:,.2f} {currency}")
            
            st.markdown("**Przejdź do sekcji:**")
            st.markdown("👉 Użyj nawigacji w sidebarze")
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 5: ANALIZA DYWERSYFIKACJI
        # ==========================================
        from ui_common import render_diversification_analysis
        render_diversification_analysis(portfolios)
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 6: INFORMACJE
        # ==========================================
        st.markdown("## Informacje")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.markdown("### Portfolio na żywo")
            st.markdown("Dane aktualizowane automatycznie z giełd")
        with col_info2:
            st.markdown("### Kurs USD/PLN")
            st.markdown(f"Aktualny: **{usd_to_pln:.2f} zł**")
        with col_info3:
            st.markdown("### Bezpieczeństwo")
            st.markdown("Dane lokalne, żadne zewnętrzne serwery")
    else:
        st.info("📊 Brak danych portfolio. Sprawdź czy API keys są skonfigurowane i czy masz aktywa na giełdach.")
        st.markdown("### Jak rozpocząć:")
        st.markdown("1. **API keys** są już skonfigurowane w Railway")
        st.markdown("2. **Sprawdź status giełd** w panelu bocznym")
        st.markdown("3. **Przejdź do zakładki 'Kryptowaluty'** - tam znajdziesz przycisk 'Pobierz z API'")
        st.markdown("4. **Dodaj transakcje** w zakładkach Kryptowaluty/Akcje")
        
        st.markdown("---")
        st.markdown("### 🔍 Gdzie znaleźć synchronizację z API:")
        st.markdown("**Przycisk 'Pobierz z API' znajduje się w zakładce 'Kryptowaluty'**")
        st.markdown("- Kliknij na 'Kryptowaluty' w menu bocznym")
        st.markdown("- Znajdziesz tam sekcję 'Dodaj transakcję'")
        st.markdown("- Przycisk 'Pobierz z API' synchronizuje dane z Binance i Bybit")
        
        st.markdown("---")
        
        # ==========================================
        # SEKCJA 6: INFORMACJE
        # ==========================================
        st.markdown("## Informacje")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.markdown("### Portfolio na żywo")
            st.markdown("Dane aktualizowane automatycznie z giełd")
        with col_info2:
            st.markdown("### Kurs USD/PLN")
            st.markdown(f"Aktualny: **{usd_to_pln:.2f} zł**")
        with col_info3:
            st.markdown("### Bezpieczeństwo")
            st.markdown("Dane lokalne, żadne zewnętrzne serwery")

except Exception as e:
    st.error(f"Błąd: {e}")
    st.exception(e)

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
