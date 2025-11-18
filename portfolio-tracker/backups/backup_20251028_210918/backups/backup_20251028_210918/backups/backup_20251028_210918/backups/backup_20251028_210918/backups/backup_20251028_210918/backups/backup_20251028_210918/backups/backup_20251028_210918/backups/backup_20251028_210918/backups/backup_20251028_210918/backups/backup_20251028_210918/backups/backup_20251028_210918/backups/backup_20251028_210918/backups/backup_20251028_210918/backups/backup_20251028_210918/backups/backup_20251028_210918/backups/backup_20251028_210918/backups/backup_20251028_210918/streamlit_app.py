"""
Professional Portfolio Tracker Dashboard - Main Summary Page
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta

# Try to import portfolio tracker with error handling
try:
    from portfolio_tracker import PortfolioTracker
    from config import Config
    from utils import get_usd_to_pln_rate, calculate_diversification
    from transaction_history import TransactionHistory
    from portfolio_history import PortfolioHistory
    from ui_common import add_reset_button
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

# Minimalist CSS - loaded from ui_common
from ui_common import load_custom_css, render_sidebar, render_main_navigation, render_footer
load_custom_css()

# Main Navigation - Professional Navigation Bar
render_main_navigation()

# Hero Section - Professional Dashboard Header
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Portfolio Dashboard</h1>
    <p class="hero-subtitle">Professional Investment Management & Analytics</p>
</div>
""", unsafe_allow_html=True)

# Initialize configuration (powinno być wykonane niezależnie od IMPORTS_SUCCESSFUL)
try:
    Config.init()
    missing = Config.validate()
    if missing:
        with st.sidebar:
            st.warning(f"Brakuje kluczy API: {', '.join(missing)}")
except Exception as e:
    with st.sidebar:
        st.error(f"Błąd konfiguracji: {e}")

currency = render_sidebar()

# Sidebar error handling
if not IMPORTS_SUCCESSFUL:
    with st.sidebar:
        st.error("⚠️ Aplikacja nie może wyświetlić danych ze względu na błędy importu modułów/bibliotek. Sprawdź terminal.")

# Main content - tylko jeśli importy się powiodły
if IMPORTS_SUCCESSFUL:
    
    # Definicje funkcji cache'ujących muszą być na najwyższym poziomie w bloku IMPORTS_SUCCESSFUL
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_portfolio_data():
        tracker = PortfolioTracker()
        data = tracker.get_all_portfolios()
        return data

    @st.cache_data(ttl=3600)
    def get_exchange_rate():
        return get_usd_to_pln_rate()
    
    # Poniższa logika musi znajdować się w bloku try/except, aby obsłużyć błędy API/danych
    try:
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
            # PORTFOLIO OVERVIEW - Professional Metrics
            # ==========================================
            st.markdown("### Portfolio Overview")
            
            # Primary metrics row - most important information
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                value_display = total_value_usd if currency == 'USD' else total_value_pln
                alt_value = total_value_pln if currency == 'USD' else total_value_usd
                alt_symbol = 'zł' if currency == 'USD' else '$'
                st.metric(
                    "Total Value",
                    f"{value_display:,.2f} {currency}",
                    f"{alt_symbol}{alt_value:,.2f}"
                )
            
            with col2:
                pnl_display = total_pnl if currency == 'USD' else total_pnl * usd_to_pln
                pnl_symbol = '$' if currency == 'USD' else 'zł'
                pnl_color = "+" if total_pnl >= 0 else ""
                st.metric(
                    "Total PNL",
                    f"{pnl_color}{pnl_display:,.2f} {currency}",
                    f"{pnl_color}{total_pnl_percent:.2f}%"
                )
            
            with col3:
                active_exchanges = len([p for p in portfolios if p['total_value_usdt'] > 0])
                st.metric("Active Exchanges", f"{active_exchanges}")
            
            with col4:
                total_assets = sum(len(p['balances']) for p in portfolios)
                st.metric("Total Assets", f"{total_assets}")
            
            # Secondary metrics row - additional information
            col_sec1, col_sec2, col_sec3, col_sec4 = st.columns(4)
            
            with col_sec1:
                invested_display = total_invested if currency == 'USD' else total_invested * usd_to_pln
                st.metric("Invested Amount", f"{invested_display:,.2f} {currency}")
            
            with col_sec2:
                roi = (total_value_usd / total_invested * 100) if total_invested > 0 else 0
                st.metric("ROI", f"{roi:.2f}%")
            
            with col_sec3:
                diversification = calculate_diversification(portfolios)
                st.metric("Diversification", f"{diversification['total_exchanges']}")
            
            with col_sec4:
                avg_return = total_pnl_percent / len(all_pnl) if all_pnl else 0
                st.metric("Avg Return", f"{avg_return:.2f}%")
            
            st.markdown("---")
            
            st.markdown("### Portfolio Performance")
            
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
                    name='Portfolio Value',
                    line=dict(color='#2563eb', width=3),
                    marker=dict(size=4),
                    fill='tonexty',
                    fillcolor='rgba(37, 99, 235, 0.1)'
                ))
                
                # Calculate dynamic Y-axis range for better visualization
                y_min = df_chart[chart_value].min()
                y_max = df_chart[chart_value].max()
                y_range = y_max - y_min
                padding = max(y_range * 0.1, y_max * 0.01)  # 10% padding or 1% of max
                
                fig_timeline.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis_title="Date",
                    yaxis_title=f"Value ({currency})",
                    yaxis=dict(
                        range=[y_min - padding, y_max + padding],
                        fixedrange=False
                    ),
                    hovermode='x unified',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    margin=dict(l=60, r=40, t=40, b=60)
                )
                
                st.plotly_chart(fig_timeline, config={'displayModeBar': False})
            else:
                st.info("No historical data available. Data will be collected automatically.")
            
            st.markdown("---")
            
            # ==========================================
            # ALLOCATION VISUALIZATION
            # ==========================================
            st.markdown("### Asset Allocation")
            
            chart_data = []
            for portfolio in portfolios:
                if portfolio['total_value_usdt'] > 0:
                    chart_data.append({
                        'Exchange': portfolio['exchange'],
                        'Value': portfolio['total_value_usdt']
                    })
            
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=df_chart['Exchange'],
                        values=df_chart['Value'],
                        hole=0.4,
                        marker_colors=['#2563eb', '#f59e0b', '#10b981'],
                        textinfo='label+percent',
                        textfont_size=14,
                        textposition='inside'
                    )])
                    fig_pie.update_layout(
                        showlegend=True,
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0),
                        title=dict(
                            text="Exchange Distribution",
                            font=dict(size=16),
                            x=0.5
                        ),
                        font=dict(size=14)
                    )
                    st.plotly_chart(fig_pie, config={'displayModeBar': False})
                
                with col2:
                    # Get max value for proper Y-axis scale
                    max_val = df_chart['Value'].max()
                    y_max = max_val * 1.15  # Add 15% padding
                    
                    fig_bar = go.Figure(data=[go.Bar(
                        x=df_chart['Exchange'],
                        y=df_chart['Value'],
                        marker_color=['#2563eb', '#f59e0b', '#10b981'],
                        text=[f"${val:,.0f}" for val in df_chart['Value']],
                        textposition='outside',
                        textfont=dict(size=14, color='#111827')
                    )])
                    fig_bar.update_layout(
                        height=400,
                        showlegend=False,
                        yaxis_title="Value (USD)",
                        xaxis_title="Exchange",
                        margin=dict(l=60, r=40, t=20, b=60),
                        yaxis=dict(
                            range=[0, y_max],
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.1)'
                        ),
                        font=dict(size=14),
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_bar, config={'displayModeBar': False})
            
            st.markdown("---")
            
            # ==========================================
            # CRYPTO vs STOCKS BREAKDOWN
            # ==========================================
            st.markdown("### Asset Type Breakdown")
            
            # Separate crypto and stocks
            crypto_portfolios = [p for p in portfolios if p['exchange'] in ['Binance', 'Bybit']]
            stocks_portfolios = [p for p in portfolios if p['exchange'] == 'XTB']
            
            crypto_value = sum(p['total_value_usdt'] for p in crypto_portfolios)
            stocks_value = sum(p['total_value_usdt'] for p in stocks_portfolios)
            
            col_div1, col_div2 = st.columns(2)
            
            with col_div1:
                st.markdown("#### Kryptowaluty")
                value_display = crypto_value if currency == 'USD' else crypto_value * usd_to_pln
                st.metric("Wartość", f"{value_display:,.2f} {currency}")
                
                # Get crypto PNL
                crypto_pnl = transaction_history.get_all_pnl(crypto_portfolios)
                crypto_total_pnl = sum(p['pnl'] for p in crypto_pnl)
                limit_pnl_display = crypto_total_pnl if currency == 'USD' else crypto_total_pnl * usd_to_pln
                pnl_color = "+" if crypto_total_pnl >= 0 else ""
                st.metric("PNL", f"{pnl_color}{limit_pnl_display:,.2f} {currency}")
                
                btn_crypto = st.button("Zobacz Kryptowaluty", type="secondary", use_container_width=True)
                if btn_crypto:
                    from ui_common import _safe_switch_page
                    _safe_switch_page("pages/1_kryptowaluty.py")
            
            with col_div2:
                st.markdown("#### Akcje")
                value_display = stocks_value if currency == 'USD' else stocks_value * usd_to_pln
                st.metric("Wartość", f"{value_display:,.2f} {currency}")
                
                # Get stocks PNL
                stocks_pnl = transaction_history.get_all_pnl(stocks_portfolios)
                stocks_total_pnl = sum(p['pnl'] for p in stocks_pnl)
                limit_pnl_display = stocks_total_pnl if currency == 'USD' else stocks_total_pnl * usd_to_pln
                pnl_color = "+" if stocks_total_pnl >= 0 else ""
                st.metric("PNL", f"{pnl_color}{limit_pnl_display:,.2f} {currency}")
                
                btn_stocks = st.button("Zobacz Akcje", type="secondary", use_container_width=True)
                if btn_stocks:
                    from ui_common import _safe_switch_page
                    _safe_switch_page("pages/2_akcje.py")
            
            st.markdown("---")
            
            # ==========================================
            # TOTAL REALIZED PNL
            # ==========================================
            st.markdown("### Realized PNL")
            
            all_transactions = transaction_history.get_all_transactions()
            total_realized = transaction_history.get_total_realized_pnl()
            
            if all_transactions:
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    total_buys = len([t for t in all_transactions if t['type'] == 'buy'])
                    total_sells = len([t for t in all_transactions if t['type'] == 'sell'])
                    st.metric("Buy Orders", f"{total_buys}")
                
                with col_r2:
                    st.metric("Sell Orders", f"{total_sells}")
                
                with col_r3:
                    realized_display = total_realized if currency == 'USD' else total_realized * usd_to_pln
                    realized_symbol = '+' if total_realized >= 0 else ''
                    alt_realized = total_realized * usd_to_pln if currency == 'USD' else total_realized
                    alt_symbol = 'zł' if currency == 'USD' else '$'
                    st.metric(
                        "Realized PNL",
                        f"{realized_symbol}{realized_display:,.2f} {currency}",
                        f"{alt_symbol}{alt_realized:,.2f}"
                    )
            else:
                st.info("Brak transakcji do wyświetlenia. Dodaj transakcje w zakładkach Kryptowaluty lub Akcje.")
            
            st.markdown("---")
            
            # ==========================================
            # DIVERSIFICATION ANALYSIS
            # ==========================================
            st.markdown("### Diversification Analysis")
            
            diversification = calculate_diversification(portfolios)
            
            col_diva1, col_diva2, col_diva3 = st.columns(3)
            
            with col_diva1:
                st.metric("Exchanges", f"{diversification['total_exchanges']}")
            
            with col_diva2:
                st.metric("Assets", f"{diversification['total_assets']}")
            
            with col_diva3:
                if diversification['total_exchanges'] > 0:
                    avg_assets = diversification['total_assets'] / diversification['total_exchanges']
                    st.metric("Avg Assets/Exchange", f"{avg_assets:.1f}")
                else:
                    st.metric("Avg Assets/Exchange", "0")
            
            st.markdown("---")
            
        else:
            st.info("No portfolio data available. Check API key configuration and ensure you have assets on exchanges.")
            st.markdown("### Getting Started")
            st.markdown("1. Configure API keys in Railway")
            st.markdown("2. Check exchange status in sidebar")
            st.markdown("3. Go to 'Cryptocurrencies' tab and use 'Sync with API' button")
            st.markdown("4. Add transactions in Cryptocurrencies/Stocks tabs")

    except Exception as e:
        st.error(f"❌ Błąd podczas ładowania lub przetwarzania danych: {e}")
        st.exception(e)

else:
    # Jeśli importy się nie powiodły, pokaż informację
    st.error("⚠️ Aplikacja nie może wyświetlić danych ze względu na błędy importu modułów/bibliotek.")
    st.info("Sprawdź terminal aby zobaczyć szczegóły błędów importu.")

# Footer - Professional Footer with Links
render_footer()