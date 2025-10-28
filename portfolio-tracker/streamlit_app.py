"""
Professional Portfolio Tracker Dashboard - Main Summary Page
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Try to import portfolio tracker with error handling
try:
    from portfolio_tracker import PortfolioTracker
    from config import Config
    from utils import get_usd_to_pln_rate, calculate_diversification
    from transaction_history import TransactionHistory
    from portfolio_history import PortfolioHistory
    # stock_prices.get_multiple_stock_prices not used in this module
    # from stock_prices import get_multiple_stock_prices
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
from ui_common import load_custom_css, render_sidebar
load_custom_css()

# Hero Section - Professional Dashboard Header
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #111827; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">Portfolio Tracker</h1>
    <p style="color: #6b7280; font-size: 1.1rem; margin: 0;">Profesjonalne zarządzanie inwestycjami</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
if not IMPORTS_SUCCESSFUL:
    with st.sidebar:
        st.error("Aplikacja nie może się uruchomić z powodu błędów importu.")
        st.stop()

# Initialize configuration
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
        # PERFORMANCE METRICS
        # ==========================================
        st.markdown("### Performance Metrics")
        
        chart_data_history = portfolio_history.get_chart_data(days=30)
        
        if chart_data_history and len(chart_data_history) > 1:
            
            df_history = pd.DataFrame(chart_data_history)
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            df_history = df_history.sort_values('timestamp')
            
            col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
            
            with col_perf1:
                today_value = df_history['value_usd'].iloc[-1]
                yesterday_value = df_history['value_usd'].iloc[-2] if len(df_history) > 1 else today_value
                today_change = today_value - yesterday_value
                today_change_pct = (today_change / yesterday_value * 100) if yesterday_value > 0 else 0
                st.metric("Today", f"{today_change:+,.2f} {currency}", f"{today_change_pct:+.2f}%")
            
            with col_perf2:
                week_ago_value = df_history['value_usd'].iloc[0] if len(df_history) >= 7 else df_history['value_usd'].iloc[0]
                week_change = today_value - week_ago_value
                week_change_pct = (week_change / week_ago_value * 100) if week_ago_value > 0 else 0
                st.metric("Week", f"{week_change:+,.2f} {currency}", f"{week_change_pct:+.2f}%")
            
            with col_perf3:
                df_history['daily_return'] = df_history['value_usd'].pct_change()
                volatility = df_history['daily_return'].std() * 100 * np.sqrt(252)
                st.metric("Volatility", f"{volatility:.2f}%", "annual")
            
            with col_perf4:
                df_history['cummax'] = df_history['value_usd'].cummax()
                df_history['drawdown'] = (df_history['value_usd'] - df_history['cummax']) / df_history['cummax'] * 100
                max_drawdown = df_history['drawdown'].min()
                st.metric("Max Drawdown", f"{max_drawdown:.2f}%", "largest loss")
        else:
            st.info("Wymagane więcej danych historycznych do obliczenia metryk. Dane będą zbierane automatycznie.")
        
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
            limit_currency_symbol = 'zł' if currency == 'USD' else '$'
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
                st.metric(
                    "Realized PNL",
                    f"{realized_symbol}{realized_display:,.2f} {currency}",
                    f"{realized_symbol}{total_realized:,.2f} USD"
                )
        else:
            st.info("Brak transakcji do wyświetlenia. Dodaj transakcje w zakładkach Kryptowaluty lub Akcje.")
        
        st.markdown("---")
        
        # ==========================================
        # EXPORT AND REPORTS
        # ==========================================
        st.markdown("### Export & Reports")
        
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        
        with col_exp1:
            if st.button("Export Transactions CSV", use_container_width=True):
                from tax_report_exporter import TaxReportExporter
                exporter = TaxReportExporter(transaction_history)
                filename = exporter.export_transactions_csv()
                st.success(f"✅ Wyeksportowano do {filename}")
                st.download_button(
                    label="📥 Pobierz CSV",
                    data=open(filename, 'rb').read(),
                    file_name=filename,
                    mime="text/csv"
                )
        
        with col_exp2:
            year = st.selectbox("Rok raportu", [2024, 2023, 2022], index=0)
            if st.button("Tax Report CSV", use_container_width=True):
                from tax_report_exporter import TaxReportExporter
                exporter = TaxReportExporter(transaction_history)
                filename = exporter.export_tax_report_csv(year)
                if filename:
                    st.success(f"✅ Raport podatkowy {year} wyeksportowany")
                    st.download_button(
                        label="📥 Pobierz Raport",
                        data=open(filename, 'rb').read(),
                        file_name=filename,
                        mime="text/csv"
                    )
        
        with col_exp3:
            if st.button("Tax Report PDF", use_container_width=True):
                from pdf_report_generator import PDFReportGenerator
                from transaction_history import TransactionHistory
                
                th = TransactionHistory()
                transactions = th.get_all_transactions()
                transactions_year = [t for t in transactions if t['date'][:4] == str(year)]
                
                generator = PDFReportGenerator()
                filename = generator.generate_tax_report_pdf(year, transactions_year)
                
                st.success(f"✅ Raport PDF {year} wygenerowany")
                st.download_button(
                    label="📥 Pobierz PDF",
                    data=open(filename, 'rb').read(),
                    file_name=filename,
                    mime="application/pdf"
                )
        
        with col_exp4:
            if st.button("📊 Podsumowanie Portfolio PDF", use_container_width=True):
                from pdf_report_generator import PDFReportGenerator
                
                # Prepare portfolio data
                portfolio_summary = {
                    'total_value': total_value_usd,
                    'exchanges': {}
                }
                
                for portfolio in portfolios:
                    if portfolio['total_value_usdt'] > 0:
                        portfolio_summary['exchanges'][portfolio['exchange']] = {
                            'value': portfolio['total_value_usdt'],
                            'percentage': (portfolio['total_value_usdt'] / total_value_usd * 100) if total_value_usd > 0 else 0
                        }
                
                generator = PDFReportGenerator()
                filename = generator.generate_portfolio_summary_pdf(portfolio_summary)
                
                st.success("✅ Podsumowanie portfolio PDF wygenerowane")
                st.download_button(
                    label="📥 Pobierz PDF",
                    data=open(filename, 'rb').read(),
                    file_name=filename,
                    mime="application/pdf"
                )
        
        # Info section
        st.info("💡 **Raporty PDF zawierają:**\n- Podsumowanie podatkowe (FIFO)\n- Szczegółowe transakcje\n- Alokacja portfolio\n- Gotowe do US")
        
        st.markdown("---")
        
        # ==========================================
        # ALERTS AND NOTIFICATIONS
        # ==========================================
        st.markdown("### Alerts & Notifications")
        
        col_alert1, col_alert2, col_alert3 = st.columns(3)
        
        with col_alert1:
            st.markdown("#### Alert Configuration")
            
            # Alert thresholds
            portfolio_threshold = st.slider("Portfolio Change Threshold (%)", 1.0, 20.0, 5.0, 0.5)
            daily_threshold = st.slider("Daily Change Threshold (%)", 1.0, 50.0, 10.0, 1.0)
            low_balance_threshold = st.slider("Low Balance Threshold ($)", 10.0, 1000.0, 100.0, 10.0)
            
            if st.button("Save Thresholds", use_container_width=True):
                from alerts_system import AlertSystem
                alert_system = AlertSystem()
                alert_system.set_thresholds(
                    portfolio_change=portfolio_threshold,
                    daily_change=daily_threshold,
                    low_balance=low_balance_threshold
                )
                st.success("✅ Progi alertów zapisane")
        
        with col_alert2:
            st.markdown("#### Sprawdź Alerty")
            
            if st.button("🔍 Sprawdź Teraz", use_container_width=True):
                from alerts_system import AlertSystem
                
                alert_system = AlertSystem()
                
                # Prepare portfolio data for checks
                portfolio_data = {
                    'current_value': total_value_usd,
                    'previous_value': total_value_usd * 0.95,  # Simulate 5% change
                    'daily_change_percent': 5.0,  # Simulate daily change
                    'balances': []
                }
                
                # Add balances from portfolios
                for portfolio in portfolios:
                    for balance in portfolio['balances']:
                        if balance.get('value_usdt', 0) > 0:
                            portfolio_data['balances'].append({
                                'exchange': portfolio['exchange'],
                                'asset': balance['asset'],
                                'value_usdt': balance['value_usdt']
                            })
                
                # Run checks
                alerts = alert_system.run_portfolio_checks(portfolio_data)
                
                if alerts:
                    st.warning(f"🔔 Znaleziono {len(alerts)} alertów:")
                    for alert in alerts:
                        st.write(f"• {alert['message']}")
                else:
                    st.success("✅ Brak alertów")
        
        with col_alert3:
            st.markdown("#### Ostatnie Alerty")
            
            try:
                from alerts_system import AlertSystem
                alert_system = AlertSystem()
                recent_alerts = alert_system.get_recent_alerts(24)
                
                if recent_alerts:
                    st.write(f"**Ostatnie 24h:** {len(recent_alerts)} alertów")
                    for alert in recent_alerts[-3:]:  # Show last 3
                        alert_time = alert['timestamp'][:16].replace('T', ' ')
                        st.write(f"• {alert_time}: {alert['message']}")
                else:
                    st.info("Brak alertów w ostatnich 24h")
            except Exception as e:
                st.error(f"Błąd ładowania alertów: {e}")
        
        st.markdown("---")
        
        # ==========================================
        # GOALS AND PROGRESS TRACKING
        # ==========================================
        st.markdown("### Goals & Progress")
        
        col_goal1, col_goal2, col_goal3 = st.columns(3)
        
        with col_goal1:
            st.markdown("#### Set Goals")
            
            goal_type = st.selectbox("Goal Type", ["Portfolio Value", "Monthly Return", "Realized Profit"])
            
            if goal_type == "Portfolio Value":
                target_value = st.number_input("Target Value ($)", min_value=1000.0, value=10000.0, step=1000.0)
                target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=365))
            elif goal_type == "Monthly Return":
                target_value = st.number_input("Target Return (%)", min_value=1.0, value=5.0, step=0.5)
                target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=30))
            else:  # Realized Profit
                target_value = st.number_input("Target Profit ($)", min_value=100.0, value=1000.0, step=100.0)
                target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=180))
            
            if st.button("Set Goal", use_container_width=True):
                from goals_tracker import GoalsTracker
                
                tracker = GoalsTracker()
                
                goal_mapping = {
                    "Wartość Portfolio": "portfolio_value",
                    "Miesięczny Zwrot": "monthly_return", 
                    "Zrealizowany Zysk": "realized_profit"
                }
                
                goal_name = goal_mapping[goal_type]
                tracker.set_goal_target(goal_name, target_value, target_date.isoformat())
                
                st.success(f"✅ Cel '{goal_type}' ustawiony na ${target_value:,.0f}")
        
        with col_goal2:
            st.markdown("#### Postępy")
            
            try:
                from goals_tracker import GoalsTracker
                tracker = GoalsTracker()
                
                # Update current values
                tracker.update_portfolio_value_goal(total_value_usd)
                
                # Get realized PNL for goals tracking
                realized_pnl = transaction_history.get_total_realized_pnl()
                tracker.update_realized_profit_goal(realized_pnl)
                
                # Get progress
                progress_list = tracker.get_all_goals_progress()
                
                if progress_list:
                    for progress in progress_list:
                        st.markdown(f"**{progress['name'].replace('_', ' ').title()}**")
                        
                        # Progress bar
                        progress_percent = progress['progress_percent']
                        st.progress(progress_percent / 100)
                        
                        # Status and message
                        status_colors = {
                            "achieved": "🟢",
                            "on_track": "🟡", 
                            "progressing": "🟠",
                            "behind": "🔴",
                            "overdue": "⚫"
                        }
                        
                        status_icon = status_colors.get(progress['status'], "⚪")
                        st.write(f"{status_icon} {progress['progress_percent']:.1f}% ({progress['days_remaining']} dni)")
                        
                        # Motivational message
                        message = tracker.get_motivational_message(progress)
                        st.info(message)
                        
                        st.markdown("---")
                else:
                    st.info("Brak aktywnych celów")
                    
            except Exception as e:
                st.error(f"Błąd ładowania celów: {e}")
        
        with col_goal3:
            st.markdown("#### Rekomendacje")
            
            try:
                from goals_tracker import GoalsTracker
                tracker = GoalsTracker()
                progress_list = tracker.get_all_goals_progress()
                
                if progress_list:
                    all_recommendations = []
                    for progress in progress_list:
                        recommendations = tracker.get_goal_recommendations(progress)
                        all_recommendations.extend(recommendations)
                    
                    if all_recommendations:
                        st.markdown("**Sugestie:**")
                        for rec in set(all_recommendations):  # Remove duplicates
                            st.write(f"• {rec}")
                    else:
                        st.info("Wszystkie cele są na dobrej drodze!")
                else:
                    st.info("Ustaw cele, aby otrzymać rekomendacje")
                    
            except Exception as e:
                st.error(f"Błąd ładowania rekomendacji: {e}")
        
        st.markdown("---")
        
        # ==========================================
        # BENCHMARK COMPARISON
        # ==========================================
        st.markdown("### Benchmark Comparison")
        
        col_bench1, col_bench2, col_bench3 = st.columns(3)
        
        with col_bench1:
            st.markdown("#### Select Benchmarks")
            
            selected_benchmarks = st.multiselect(
                "Benchmarks to Compare",
                ["S&P 500", "NASDAQ", "DOW", "Bitcoin", "Ethereum", "Gold", "WIG20"],
                default=["S&P 500", "Bitcoin", "Ethereum"]
            )
            
            if st.button("Compare with Benchmarks", use_container_width=True):
                from benchmark_comparison import BenchmarkComparison
                
                benchmark = BenchmarkComparison()
                
                # Prepare portfolio history (simplified)
                portfolio_history = []
                for i in range(12):  # Last 12 months
                    date = datetime.now() - timedelta(days=30*i)
                    # Simulate portfolio growth
                    value = total_value_usd * (1 - i * 0.02)  # 2% monthly growth
                    portfolio_history.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'value': value
                    })
                
                # Run comparison
                results = benchmark.compare_portfolio_to_benchmarks(portfolio_history, total_value_usd)
                
                if results:
                    st.session_state['benchmark_results'] = results
                    st.success("✅ Porównanie wykonane")
                else:
                    st.error("❌ Błąd pobierania danych benchmarków")
        
        with col_bench2:
            st.markdown("#### Wyniki Porównania")
            
            if 'benchmark_results' in st.session_state:
                results = st.session_state['benchmark_results']
                portfolio_metrics = results.get('portfolio_metrics', {})
                outperformance = results.get('outperformance', {})
                
                st.markdown("**Portfolio:**")
                st.write(f"• Zwrot: {portfolio_metrics.get('total_return', 0):.2f}%")
                st.write(f"• Zmienność: {portfolio_metrics.get('volatility', 0):.2f}%")
                st.write(f"• Sharpe: {portfolio_metrics.get('sharpe_ratio', 0):.2f}")
                
                st.markdown("**Przewaga:**")
                for benchmark_name, value in outperformance.items():
                    if benchmark_name in selected_benchmarks:
                        if value > 0:
                            st.write(f"• {benchmark_name}: +{value:.2f}% 🟢")
                        else:
                            st.write(f"• {benchmark_name}: {value:.2f}% 🔴")
            else:
                st.info("Kliknij 'Porównaj z Benchmarkami' aby zobaczyć wyniki")
        
        with col_bench3:
            st.markdown("#### Rekomendacje")
            
            if 'benchmark_results' in st.session_state:
                from benchmark_comparison import BenchmarkComparison
                benchmark = BenchmarkComparison()
                results = st.session_state['benchmark_results']
                
                recommendations = benchmark.get_benchmark_recommendations(results)
                
                if recommendations:
                    st.markdown("**Sugestie:**")
                    for rec in recommendations:
                        st.write(f"• {rec}")
                else:
                    st.info("Portfolio jest dobrze zbalansowane")
            else:
                st.info("Uruchom porównanie aby otrzymać rekomendacje")
        
        st.markdown("---")
        
        # ==========================================
        # SECTOR ANALYSIS
        # ==========================================
        st.markdown("### Sector Analysis")
        
        col_sector1, col_sector2, col_sector3 = st.columns(3)
        
        with col_sector1:
            st.markdown("#### Sector Structure")
            
            try:
                from sector_analysis import SectorAnalysis
                
                analyzer = SectorAnalysis()
                sector_data = analyzer.analyze_portfolio_sectors(portfolios)
                
                if sector_data:
                    # Create sector pie chart
                    sector_names = list(sector_data.keys())
                    sector_values = [sector_data[name]['total_value'] for name in sector_names]
                    sector_percentages = [sector_data[name]['percentage'] for name in sector_names]
                    
                    fig_sector = go.Figure(data=[go.Pie(
                        labels=sector_names,
                        values=sector_values,
                        hole=0.4,
                        textinfo='label+percent',
                        textfont_size=12,
                        marker_colors=['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']
                    )])
                    
                    fig_sector.update_layout(
                        showlegend=True,
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0),
                        title=dict(
                            text="Sector Distribution",
                            font=dict(size=16),
                            x=0.5
                        ),
                        font=dict(size=12)
                    )
                    
                    st.plotly_chart(fig_sector, config={'displayModeBar': False})
                else:
                    st.info("Brak danych do analizy sektorowej")
                    
            except Exception as e:
                st.error(f"Błąd analizy sektorowej: {e}")
        
        with col_sector2:
            st.markdown("#### Risk Metrics")
            
            try:
                from sector_analysis import SectorAnalysis
                
                analyzer = SectorAnalysis()
                sector_data = analyzer.analyze_portfolio_sectors(portfolios)
                risk_metrics = analyzer.calculate_sector_risk_metrics(sector_data)
                
                if risk_metrics:
                    st.metric("Poziom Ryzyka", risk_metrics['risk_level'])
                    st.metric("Skuteczne Sektory", f"{risk_metrics['effective_sectors']:.1f}")
                    st.metric("Score Dywersyfikacji", f"{risk_metrics['diversification_score']:.2f}")
                    
                    # Risk indicator
                    risk_score = risk_metrics['diversification_score']
                    if risk_score >= 0.7:
                        st.success("✅ Dobra dywersyfikacja")
                    elif risk_score >= 0.4:
                        st.warning("⚠️ Średnia dywersyfikacja")
                    else:
                        st.error("❌ Słaba dywersyfikacja")
                else:
                    st.info("Brak danych do kalkulacji ryzyka")
                    
            except Exception as e:
                st.error(f"Błąd kalkulacji ryzyka: {e}")
        
        with col_sector3:
            st.markdown("#### Rekomendacje")
            
            try:
                from sector_analysis import SectorAnalysis
                
                analyzer = SectorAnalysis()
                sector_data = analyzer.analyze_portfolio_sectors(portfolios)
                recommendations = analyzer.get_sector_recommendations(sector_data)
                
                if recommendations:
                    st.markdown("**Sugestie:**")
                    for rec in recommendations:
                        st.write(f"• {rec}")
                else:
                    st.info("Portfolio jest dobrze zbalansowane sektorowo")
                    
            except Exception as e:
                st.error(f"Błąd generowania rekomendacji: {e}")
        
        # Detailed sector breakdown
        st.markdown("#### Szczegółowy Podział Sektorowy")
        
        try:
            from sector_analysis import SectorAnalysis
            
            analyzer = SectorAnalysis()
            sector_data = analyzer.analyze_portfolio_sectors(portfolios)
            
            if sector_data:
                # Create sector breakdown table
                sector_table_data = []
                for sector, data in sector_data.items():
                    sector_table_data.append({
                        'Sektor': sector,
                        'Wartość (USD)': f"${data['total_value']:,.2f}",
                        'Procent': f"{data['percentage']:.2f}%",
                        'Aktywa': len(data['assets']),
                        'Giełdy': len(data['exchanges'])
                    })
                
                df_sectors = pd.DataFrame(sector_table_data)
                df_sectors = df_sectors.sort_values('Procent', ascending=False)
                
                st.dataframe(df_sectors, use_container_width=True)
                
                # Top assets by sector
                st.markdown("#### Top Aktywa w Sektorach")
                top_assets = analyzer.get_top_assets_by_sector(sector_data, top_n=3)
                
                for sector, assets in top_assets.items():
                    if assets:
                        st.markdown(f"**{sector}:**")
                        for asset, value in assets:
                            st.write(f"• {asset}: ${value:,.2f}")
                        st.markdown("---")
            else:
                st.info("Brak danych do wyświetlenia")
                
        except Exception as e:
            st.error(f"Błąd wyświetlania szczegółów: {e}")
        
        st.markdown("---")
        
        # ==========================================
        # TAX CALENDAR
        # ==========================================
        st.markdown("### Tax Calendar")
        
        col_tax1, col_tax2, col_tax3 = st.columns(3)
        
        with col_tax1:
            st.markdown("#### Upcoming Deadlines")
            
            try:
                from tax_calendar import TaxCalendar
                
                tax_calendar = TaxCalendar()
                upcoming = tax_calendar.get_upcoming_deadlines(30)
                
                if upcoming:
                    for deadline in upcoming[:5]:  # Show next 5
                        days_until = deadline['days_until']
                        if days_until <= 7:
                            st.error(f"🔴 {deadline['description']} - {days_until} dni")
                        elif days_until <= 14:
                            st.warning(f"🟡 {deadline['description']} - {days_until} dni")
                        else:
                            st.info(f"🟢 {deadline['description']} - {days_until} dni")
                else:
                    st.success("✅ Brak nadchodzących terminów w ciągu 30 dni")
                    
            except Exception as e:
                st.error(f"Błąd ładowania terminów: {e}")
        
        with col_tax2:
            st.markdown("#### Checklist Podatkowy")
            
            try:
                from tax_calendar import TaxCalendar
                
                tax_calendar = TaxCalendar()
                checklist = tax_calendar.get_tax_checklist()
                
                completed_tasks = 0
                for i, task in enumerate(checklist[:5], 1):  # Show first 5
                    if st.checkbox(f"{i}. {task['task']}", value=False):
                        completed_tasks += 1
                
                progress = completed_tasks / min(len(checklist), 5)
                st.progress(progress)
                st.write(f"Postęp: {completed_tasks}/{min(len(checklist), 5)} zadań")
                
            except Exception as e:
                st.error(f"Błąd ładowania checklist: {e}")
        
        with col_tax3:
            st.markdown("#### Szacunek Podatku")
            
            try:
                from tax_calendar import TaxCalendar
                
                tax_calendar = TaxCalendar()
                
                # Get realized PNL for tax calculation
                realized_pnl = transaction_history.get_total_realized_pnl()
                tax_estimate = tax_calendar.calculate_tax_estimate(realized_pnl)
                
                st.metric("Podstawa Opodatkowania", f"{tax_estimate['taxable_amount']:,.2f} PLN")
                st.metric("Stawka Podatkowa", f"{tax_estimate['tax_rate']*100:.0f}%")
                st.metric("Szacowany Podatek", f"{tax_estimate['estimated_tax']:,.2f} PLN")
                
                if tax_estimate['estimated_tax'] > 0:
                    st.warning("💰 Przygotuj środki na zapłatę podatku")
                else:
                    st.success("✅ Brak podatku do zapłacenia")
                    
            except Exception as e:
                st.error(f"Błąd kalkulacji podatku: {e}")
        
        # Tax tips and recommendations
        st.markdown("#### Wskazówki Podatkowe")
        
        try:
            from tax_calendar import TaxCalendar
            
            tax_calendar = TaxCalendar()
            tips = tax_calendar.get_tax_tips()
            
            col_tip1, col_tip2 = st.columns(2)
            
            with col_tip1:
                st.markdown("**Najważniejsze:**")
                for tip in tips[:5]:
                    st.write(f"• {tip}")
            
            with col_tip2:
                st.markdown("**Dodatkowe:**")
                for tip in tips[5:10]:
                    st.write(f"• {tip}")
                    
        except Exception as e:
            st.error(f"Błąd ładowania wskazówek: {e}")
        
        # Overdue deadlines alert
        try:
            from tax_calendar import TaxCalendar
            
            tax_calendar = TaxCalendar()
            overdue = tax_calendar.get_overdue_deadlines()
            
            if overdue:
                st.markdown("#### ⚠️ Przeterminowane Terminy")
                st.error(f"**UWAGA:** Masz {len(overdue)} przeterminowanych terminów!")
                
                for deadline in overdue[:3]:  # Show first 3
                    st.write(f"• {deadline['description']} - {deadline['days_overdue']} dni temu")
                
                if len(overdue) > 3:
                    st.write(f"... i {len(overdue) - 3} więcej")
                    
        except Exception as e:
            st.error(f"Błąd sprawdzania przeterminowanych terminów: {e}")
        
        st.markdown("---")
        
        # ==========================================
        # BACKUP AND SYNCHRONIZATION
        # ==========================================
        st.markdown("### Backup & Synchronization")
        
        col_backup1, col_backup2, col_backup3 = st.columns(3)
        
        with col_backup1:
            st.markdown("#### Backup Management")
            
            try:
                from backup_system import BackupSystem
                
                backup_system = BackupSystem()
                
                if st.button("💾 Utwórz Backup", use_container_width=True):
                    backup_path = backup_system.create_backup()
                    st.success(f"✅ Backup utworzony: {os.path.basename(backup_path)}")
                
                # List available backups
                backups = backup_system.list_backups()
                
                if backups:
                    st.markdown("**Dostępne backupy:**")
                    for backup in backups[:5]:  # Show last 5
                        size_mb = backup['size'] / (1024 * 1024)
                        date_str = backup['created'][:10]
                        
                        col_name, col_size, col_date = st.columns([2, 1, 1])
                        with col_name:
                            st.write(backup['name'])
                        with col_size:
                            st.write(f"{size_mb:.1f}MB")
                        with col_date:
                            st.write(date_str)
                else:
                    st.info("Brak dostępnych backupów")
                    
            except Exception as e:
                st.error(f"Błąd systemu backupów: {e}")
        
        with col_backup2:
            st.markdown("#### Statystyki Backupów")
            
            try:
                from backup_system import BackupSystem
                
                backup_system = BackupSystem()
                stats = backup_system.get_backup_stats()
                
                st.metric("Całkowite Backupy", stats['total_backups'])
                st.metric("Całkowity Rozmiar", f"{stats['total_size'] / (1024 * 1024):.1f} MB")
                
                if stats['last_backup']:
                    last_backup_date = stats['last_backup'][:10]
                    st.metric("Ostatni Backup", last_backup_date)
                else:
                    st.metric("Ostatni Backup", "Brak")
                
                # Backup health indicator
                if stats['total_backups'] >= 3:
                    st.success("✅ Dobra polityka backupów")
                elif stats['total_backups'] >= 1:
                    st.warning("⚠️ Minimalna liczba backupów")
                else:
                    st.error("❌ Brak backupów")
                    
            except Exception as e:
                st.error(f"Błąd statystyk backupów: {e}")
        
        with col_backup3:
            st.markdown("#### Konfiguracja")
            
            try:
                from backup_system import BackupSystem
                
                backup_system = BackupSystem()
                config = backup_system.config
                
                # Auto backup setting
                auto_backup = st.checkbox("Automatyczne backupy", value=config['auto_backup'])
                
                # Backup frequency
                frequency = st.selectbox(
                    "Częstotliwość backupów",
                    ["daily", "weekly", "monthly"],
                    index=["daily", "weekly", "monthly"].index(config['backup_frequency'])
                )
                
                # Max backups
                max_backups = st.slider("Maksymalna liczba backupów", 1, 20, config['max_backups'])
                
                # Compression
                compression = st.checkbox("Kompresja ZIP", value=config['compression'])
                
                if st.button("💾 Zapisz Konfigurację", use_container_width=True):
                    backup_system.config['auto_backup'] = auto_backup
                    backup_system.config['backup_frequency'] = frequency
                    backup_system.config['max_backups'] = max_backups
                    backup_system.config['compression'] = compression
                    backup_system.save_config()
                    st.success("✅ Konfiguracja zapisana")
                    
            except Exception as e:
                st.error(f"Błąd konfiguracji: {e}")
        
        # Backup recommendations
        st.markdown("#### Rekomendacje Backupów")
        
        try:
            from backup_system import BackupSystem
            
            backup_system = BackupSystem()
            stats = backup_system.get_backup_stats()
            
            recommendations = []
            
            if stats['total_backups'] == 0:
                recommendations.append("🚨 URGENTNE: Utwórz pierwszy backup!")
                recommendations.append("💡 Ustaw automatyczne backupy")
            elif stats['total_backups'] < 3:
                recommendations.append("⚠️ Utwórz więcej backupów dla bezpieczeństwa")
                recommendations.append("📅 Rozważ codzienne backupy")
            else:
                recommendations.append("✅ Dobra polityka backupów")
            
            if stats['last_backup']:
                last_backup_date = datetime.fromisoformat(stats['last_backup']).date()
                days_since_backup = (datetime.now().date() - last_backup_date).days
                
                if days_since_backup > 7:
                    recommendations.append(f"⚠️ Ostatni backup {days_since_backup} dni temu")
                elif days_since_backup > 3:
                    recommendations.append(f"🟡 Ostatni backup {days_since_backup} dni temu")
                else:
                    recommendations.append("✅ Backupy są aktualne")
            
            if stats['total_size'] > 100 * 1024 * 1024:  # > 100MB
                recommendations.append("💾 Rozważ czyszczenie starych backupów")
            
            col_rec1, col_rec2 = st.columns(2)
            
            with col_rec1:
                st.markdown("**Najważniejsze:**")
                for rec in recommendations[:3]:
                    st.write(f"• {rec}")
            
            with col_rec2:
                st.markdown("**Dodatkowe:**")
                for rec in recommendations[3:]:
                    st.write(f"• {rec}")
                    
        except Exception as e:
            st.error(f"Błąd rekomendacji: {e}")
        
        st.markdown("---")
        
        # ==========================================
        # DATA VALIDATION
        # ==========================================
        st.markdown("### Data Validation")
        
        col_valid1, col_valid2, col_valid3 = st.columns(3)
        
        with col_valid1:
            st.markdown("#### Check Data")
            
            try:
                from data_validator import DataValidator
                
                validator = DataValidator()
                
                if st.button("Check Transactions", use_container_width=True):
                    all_transactions = transaction_history.get_all_transactions()
                    transaction_results = validator.validate_transactions(all_transactions)
                    
                    st.session_state['validation_results'] = transaction_results
                    st.success(f"✅ Sprawdzono {len(all_transactions)} transakcji")
                
                if st.button("Check Portfolio", use_container_width=True):
                    portfolio_results = validator.validate_portfolio_data(portfolios)
                    
                    if 'validation_results' in st.session_state:
                        # Merge results
                        st.session_state['validation_results']['portfolio_results'] = portfolio_results
                    else:
                        st.session_state['validation_results'] = {'portfolio_results': portfolio_results}
                    
                    st.success(f"✅ Sprawdzono {len(portfolios)} portfolio")
                    
            except Exception as e:
                st.error(f"Błąd walidacji: {e}")
        
        with col_valid2:
            st.markdown("#### Wyniki Walidacji")
            
            if 'validation_results' in st.session_state:
                results = st.session_state['validation_results']
                
                # Transaction results
                if 'total_transactions' in results:
                    st.metric("Transakcje", f"{results['valid_transactions']}/{results['total_transactions']}")
                    st.metric("Błędy", results['invalid_transactions'])
                    st.metric("Ostrzeżenia", len(results.get('warnings', [])))
                
                # Portfolio results
                if 'portfolio_results' in results:
                    portfolio_results = results['portfolio_results']
                    st.metric("Portfolio", f"{portfolio_results['valid_portfolios']}/{portfolio_results['total_portfolios']}")
                
                # Health score
                health_score = validator.get_data_health_score(results)
                
                if health_score >= 90:
                    st.success(f"✅ Score: {health_score}/100")
                elif health_score >= 70:
                    st.warning(f"⚠️ Score: {health_score}/100")
                else:
                    st.error(f"❌ Score: {health_score}/100")
            else:
                st.info("Kliknij 'Sprawdź Dane' aby zobaczyć wyniki")
                
        with col_valid3:
            st.markdown("#### Rekomendacje")
            
            if 'validation_results' in st.session_state:
                try:
                    from data_validator import DataValidator
                    
                    validator = DataValidator()
                    results = st.session_state['validation_results']
                    recommendations = validator.get_validation_recommendations(results)
                    
                    if recommendations:
                        for rec in recommendations[:5]:  # Show first 5
                            st.write(f"• {rec}")
                    else:
                        st.success("✅ Wszystkie dane są poprawne")
                        
                except Exception as e:
                    st.error(f"Błąd rekomendacji: {e}")
            else:
                st.info("Uruchom walidację aby otrzymać rekomendacje")
        
        # Detailed validation results
        if 'validation_results' in st.session_state:
            st.markdown("#### Szczegółowe Wyniki")
            
            results = st.session_state['validation_results']
            
            # Show errors
            if results.get('errors'):
                st.markdown("**Błędy:**")
                for error in results['errors'][:10]:  # Show first 10
                    st.error(f"• {error}")
            
            # Show warnings
            if results.get('warnings'):
                st.markdown("**Ostrzeżenia:**")
                for warning in results['warnings'][:10]:  # Show first 10
                    st.warning(f"• {warning}")
            
            # Show duplicates
            if results.get('duplicates'):
                st.markdown("**Duplikaty:**")
                for duplicate in results['duplicates'][:5]:  # Show first 5
                    st.info(f"• Transakcja {duplicate['index']}: {duplicate['transaction'].get('asset', 'N/A')}")
            
            # Show missing data
            if results.get('missing_data'):
                st.markdown("**Brakujące Dane:**")
                for missing in results['missing_data']:
                    st.info(f"• {missing['description']}")
        
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
    st.error(f"Błąd: {e}")
    st.exception(e)
