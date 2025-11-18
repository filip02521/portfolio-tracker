import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import portfolio tracker and utilities
from portfolio_tracker import PortfolioTracker
from utils import get_usd_to_pln_rate
from ui_common import load_custom_css, render_main_navigation, render_sidebar, render_footer
from config import Config

# Page configuration
st.set_page_config(
    page_title="Portfolio - Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and render navigation
load_custom_css()
render_main_navigation()

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Portfolio Management</h1>
    <p class="hero-subtitle">Comprehensive portfolio analysis and asset allocation</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Initialize configuration
try:
    Config.init()
except Exception as e:
    st.error(f"Błąd inicjalizacji: {e}")
    st.stop()

# Get portfolio data
@st.cache_data(ttl=300)
def get_portfolio_data():
    tracker = PortfolioTracker()
    return tracker.get_all_portfolios()

@st.cache_data(ttl=3600)
def get_exchange_rate():
    return get_usd_to_pln_rate()

try:
    with st.spinner("⏳ Ładowanie danych portfolio..."):
        portfolios = get_portfolio_data()
        usd_to_pln = get_exchange_rate()
except Exception as e:
    st.error(f"Błąd pobierania danych: {e}")
    st.stop()

# Calculate total portfolio values
total_value_usd = sum(p['total_value_usdt'] for p in portfolios)
total_value_pln = total_value_usd * usd_to_pln

display_value = total_value_pln if currency == "PLN" else total_value_usd
currency_symbol = "zł" if currency == "PLN" else "$"

# Portfolio Overview Section
st.markdown("## 📊 Portfolio Overview")

# Create tabs for different portfolio views
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Allocation", "Performance", "Holdings"])

with tab1:
    st.markdown("### Portfolio Summary")
    
    # Portfolio metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"Total Value ({currency})",
            value=f"{currency_symbol}{display_value:,.2f}",
            delta=None
        )
    
    with col2:
        # Count total assets
        total_assets = sum(len(p['balances']) for p in portfolios)
        st.metric(
            label="Total Assets",
            value=total_assets
        )
    
    with col3:
        # Count exchanges
        exchanges = set(p['exchange'] for p in portfolios if p['balances'])
        st.metric(
            label="Active Exchanges",
            value=len(exchanges)
        )
    
    with col4:
        # Asset types
        crypto_count = sum(1 for p in portfolios if p['exchange'] in ['binance', 'bybit'])
        stocks_count = sum(1 for p in portfolios if p['exchange'] == 'xtb')
        st.metric(
            label="Asset Types",
            value=f"{crypto_count} Crypto / {stocks_count} Stocks"
        )
    
    # Portfolio composition
    st.markdown("### Asset Composition")
    
    # Prepare data for charts
    holdings_data = []
    for portfolio in portfolios:
        for balance in portfolio['balances']:
            if balance.get('value_usdt', 0) > 0:  # Only show assets with value
                value_display = balance['value_usdt'] * usd_to_pln if currency == "PLN" else balance['value_usdt']
                holdings_data.append({
                    'Asset': balance['asset'],
                    'Value': value_display,
                    'Exchange': portfolio['exchange'].capitalize(),
                    'Type': 'Crypto' if portfolio['exchange'] in ['Binance', 'Bybit'] else 'Stock'
                })
    
    if holdings_data:
        df_holdings = pd.DataFrame(holdings_data)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                df_holdings, 
                values='Value', 
                names='Asset',
                title=f"Portfolio Allocation ({currency})",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.markdown("#### Top Holdings")
            # Sort by value and show top 10
            top_holdings = df_holdings.groupby('Asset')['Value'].sum().sort_values(ascending=False).head(10)
            total_value = df_holdings['Value'].sum()
            
            for asset, value in top_holdings.items():
                percentage = (value / total_value) * 100
                st.markdown(f"**{asset}** - {percentage:.1f}%")
                st.progress(percentage / 100)
    else:
        st.info("Brak danych o aktywach w portfolio.")

with tab2:
    st.markdown("### Asset Allocation Analysis")
    
    if holdings_data:
        df_holdings = pd.DataFrame(holdings_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### By Asset Type")
            type_data = df_holdings.groupby('Type')['Value'].sum().reset_index()
            type_data['Percentage'] = (type_data['Value'] / type_data['Value'].sum()) * 100
            
            fig_type = px.bar(
                type_data, 
                x='Type', 
                y='Percentage',
                title="Allocation by Asset Type",
                color='Type',
                color_discrete_sequence=['#2563eb', '#10b981']
            )
            fig_type.update_layout(height=300)
            st.plotly_chart(fig_type, use_container_width=True)
        
        with col2:
            st.markdown("#### By Exchange")
            exchange_data = df_holdings.groupby('Exchange')['Value'].sum().reset_index()
            exchange_data['Percentage'] = (exchange_data['Value'] / exchange_data['Value'].sum()) * 100
            
            fig_exchange = px.pie(
                exchange_data, 
                values='Percentage', 
                names='Exchange',
                title="Allocation by Exchange",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_exchange.update_layout(height=300)
            st.plotly_chart(fig_exchange, use_container_width=True)
        
        # Risk metrics placeholder
        st.markdown("#### Portfolio Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Diversification", f"{len(df_holdings['Asset'].unique())} Assets")
        with col2:
            # Calculate concentration (top asset percentage)
            top_asset_pct = (df_holdings.groupby('Asset')['Value'].sum().max() / df_holdings['Value'].sum()) * 100
            st.metric("Top Asset %", f"{top_asset_pct:.1f}%")
        with col3:
            st.metric("Exchanges", f"{len(df_holdings['Exchange'].unique())}")
        with col4:
            # Crypto vs Stock ratio
            crypto_value = df_holdings[df_holdings['Type'] == 'Crypto']['Value'].sum()
            total = df_holdings['Value'].sum()
            crypto_pct = (crypto_value / total) * 100 if total > 0 else 0
            st.metric("Crypto Allocation", f"{crypto_pct:.1f}%")
    else:
        st.info("Brak danych o aktywach do analizy.")

with tab3:
    st.markdown("### Performance Analysis")
    
    # Load historical data if available
    try:
        with open('portfolio_history.json', 'r') as f:
            history = json.load(f)
        
        if history:
            # Prepare historical data
            dates = [datetime.fromisoformat(h['timestamp']) for h in history]
            values_usd = [h['value_usd'] for h in history]
            values_pln = [h['value_pln'] for h in history]
            
            values_display = values_pln if currency == "PLN" else values_usd
            
            performance_data = pd.DataFrame({
                'Date': dates,
                'Portfolio Value': values_display
            })
            
            # Calculate daily returns
            performance_data['Daily Return'] = performance_data['Portfolio Value'].pct_change() * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_performance = px.line(
                    performance_data, 
                    x='Date', 
                    y='Portfolio Value',
                    title=f"Portfolio Value Over Time ({currency})",
                    color_discrete_sequence=['#2563eb']
                )
                fig_performance.update_layout(height=400)
                st.plotly_chart(fig_performance, use_container_width=True)
            
            with col2:
                fig_returns = px.histogram(
                    performance_data.dropna(), 
                    x='Daily Return',
                    title="Daily Returns Distribution (%)",
                    color_discrete_sequence=['#10b981']
                )
                fig_returns.update_layout(height=400)
                st.plotly_chart(fig_returns, use_container_width=True)
            
            # Performance metrics
            st.markdown("#### Performance Metrics")
            
            if len(values_display) > 1:
                # Calculate metrics
                total_return = ((values_display[-1] - values_display[0]) / values_display[0]) * 100
                avg_daily_return = performance_data['Daily Return'].mean()
                volatility = performance_data['Daily Return'].std()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"{total_return:.2f}%")
                with col2:
                    st.metric("Avg Daily Return", f"{avg_daily_return:.2f}%")
                with col3:
                    st.metric("Volatility", f"{volatility:.2f}%")
                with col4:
                    # Simple Sharpe-like ratio
                    sharpe = (avg_daily_return / volatility) if volatility > 0 else 0
                    st.metric("Risk-Adjusted Return", f"{sharpe:.2f}")
        else:
            st.info("Brak danych historycznych. Dodaj więcej transakcji, aby zobaczyć wykresy wydajności.")
    except FileNotFoundError:
        st.info("Brak danych historycznych. Rozpocznij śledzenie portfolio, aby zobaczyć wykresy wydajności.")
    except Exception as e:
        st.error(f"Błąd ładowania danych historycznych: {e}")

with tab4:
    st.markdown("### Current Holdings")
    
    if holdings_data:
        # Create detailed holdings table
        detailed_holdings = []
        for portfolio in portfolios:
            for balance in portfolio['balances']:
                if balance.get('value_usdt', 0) > 0:  # Only show assets with value
                    detailed_holdings.append({
                        'Asset': balance['asset'],
                        'Exchange': portfolio['exchange'].capitalize(),
                        'Quantity': balance.get('free', 0) + balance.get('locked', 0),
                        'Current Price (USD)': balance['value_usdt'] / (balance.get('free', 0) + balance.get('locked', 0)) if (balance.get('free', 0) + balance.get('locked', 0)) > 0 else 0,
                        'Market Value (USD)': balance['value_usdt'],
                        'Market Value (PLN)': balance['value_usdt'] * usd_to_pln,
                        'Type': 'Crypto' if portfolio['exchange'] in ['Binance', 'Bybit'] else 'Stock'
                    })
        
        df_detailed = pd.DataFrame(detailed_holdings)
        
        # Display based on selected currency
        if currency == "PLN":
            display_columns = ['Asset', 'Exchange', 'Type', 'Quantity', 'Current Price (USD)', 'Market Value (PLN)']
        else:
            display_columns = ['Asset', 'Exchange', 'Type', 'Quantity', 'Current Price (USD)', 'Market Value (USD)']
        
        st.dataframe(df_detailed[display_columns], use_container_width=True)
        
        # Holdings summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Holdings Summary")
            total_market_value = df_detailed['Market Value (USD)'].sum()
            
            st.metric("Total Market Value (USD)", f"${total_market_value:,.2f}")
            st.metric("Total Market Value (PLN)", f"{total_market_value * usd_to_pln:,.2f} zł")
            st.metric("Number of Holdings", len(df_detailed))
        
        with col2:
            st.markdown("#### Asset Distribution")
            fig_dist = px.treemap(
                df_detailed, 
                path=['Type', 'Exchange', 'Asset'], 
                values='Market Value (USD)',
                title="Holdings by Market Value",
                color='Market Value (USD)',
                color_continuous_scale='Blues'
            )
            fig_dist.update_layout(height=300)
            st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.info("Brak aktywów w portfolio. Dodaj transakcje, aby zobaczyć swoje pozycje.")

# Footer
render_footer()
