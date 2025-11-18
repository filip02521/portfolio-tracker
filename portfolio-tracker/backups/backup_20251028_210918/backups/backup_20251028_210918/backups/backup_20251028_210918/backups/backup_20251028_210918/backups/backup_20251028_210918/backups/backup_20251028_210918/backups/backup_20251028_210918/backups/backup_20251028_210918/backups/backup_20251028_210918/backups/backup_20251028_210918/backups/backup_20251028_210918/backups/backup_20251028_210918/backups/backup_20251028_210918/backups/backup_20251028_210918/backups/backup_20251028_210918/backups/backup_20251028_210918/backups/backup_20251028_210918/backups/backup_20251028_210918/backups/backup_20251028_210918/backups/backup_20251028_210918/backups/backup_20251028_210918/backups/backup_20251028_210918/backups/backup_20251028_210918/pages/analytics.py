import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import json

# Import necessary modules
from portfolio_tracker import PortfolioTracker
from transaction_history import TransactionHistory
from utils import get_usd_to_pln_rate
from ui_common import load_custom_css, render_main_navigation, render_sidebar, render_footer
from config import Config

# Page configuration
st.set_page_config(
    page_title="Analytics - Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and render navigation
load_custom_css()
render_main_navigation()

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Portfolio Analytics</h1>
    <p class="hero-subtitle">Advanced analytics and insights for your investment portfolio</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Initialize
Config.init()
tracker = PortfolioTracker()
th = TransactionHistory()
usd_to_pln = get_usd_to_pln_rate()

# Get data
portfolios = tracker.get_all_portfolios()
transactions = th.get_all_transactions()

# Analytics Section
st.markdown("## 📈 Portfolio Analytics")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Performance", "Risk Analysis", "Asset Analysis"])

with tab1:
    st.markdown("### Performance Analytics")
    
    # Load historical data
    try:
        with open('portfolio_history.json', 'r') as f:
            history = json.load(f)
        
        if history and len(history) > 1:
            # Prepare data
            dates = [datetime.fromisoformat(h['timestamp']) for h in history]
            values_usd = [h['value_usd'] for h in history]
            values_pln = [h['value_pln'] for h in history]
            
            values_display = values_pln if currency == "PLN" else values_usd
            currency_symbol = "zł" if currency == "PLN" else "$"
            
            performance_data = pd.DataFrame({
                'Date': dates,
                'Portfolio Value': values_display
            })
            
            # Calculate returns
            performance_data['Daily Return'] = performance_data['Portfolio Value'].pct_change() * 100
            performance_data['Cumulative Return'] = ((performance_data['Portfolio Value'] / performance_data['Portfolio Value'].iloc[0]) - 1) * 100
            
            # Performance metrics
            total_return = performance_data['Cumulative Return'].iloc[-1]
            avg_daily_return = performance_data['Daily Return'].mean()
            volatility = performance_data['Daily Return'].std()
            sharpe_ratio = (avg_daily_return / volatility * np.sqrt(252)) if volatility > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Return", f"{total_return:.2f}%")
            with col2:
                annualized_return = avg_daily_return * 252
                st.metric("Annualized Return", f"{annualized_return:.2f}%")
            with col3:
                st.metric("Volatility", f"{volatility:.2f}%")
            with col4:
                st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
            
            # Performance charts
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
                # Rolling returns
                performance_data['Rolling Return (7d)'] = performance_data['Portfolio Value'].pct_change(7) * 100
                fig_rolling = px.line(
                    performance_data, 
                    x='Date', 
                    y='Rolling Return (7d)',
                    title="7-Day Rolling Returns (%)",
                    color_discrete_sequence=['#10b981']
                )
                fig_rolling.update_layout(height=400)
                st.plotly_chart(fig_rolling, use_container_width=True)
            
            # Drawdown analysis
            st.markdown("#### Drawdown Analysis")
            
            peak = performance_data['Portfolio Value'].expanding().max()
            drawdown = ((performance_data['Portfolio Value'] - peak) / peak * 100)
            max_drawdown = drawdown.min()
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig_drawdown = px.area(
                    x=performance_data['Date'], 
                    y=drawdown,
                    title="Portfolio Drawdown (%)",
                    color_discrete_sequence=['#ef4444']
                )
                fig_drawdown.update_layout(height=300)
                st.plotly_chart(fig_drawdown, use_container_width=True)
            
            with col2:
                st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                
                # Current drawdown
                current_drawdown = drawdown.iloc[-1]
                st.metric("Current Drawdown", f"{current_drawdown:.2f}%")
        else:
            st.info("Insufficient historical data. Continue tracking your portfolio to see performance analytics.")
    except FileNotFoundError:
        st.info("No historical data available. Start tracking your portfolio to see performance analytics.")
    except Exception as e:
        st.error(f"Error loading historical data: {e}")

with tab2:
    st.markdown("### Risk Analysis")
    
    if transactions:
        df_trans = pd.DataFrame(transactions)
        
        # Calculate portfolio metrics
        holdings_data = []
        for portfolio in portfolios:
            for balance in portfolio['balances']:
                if balance.get('value_usdt', 0) > 0:  # Only show assets with value
                    holdings_data.append({
                        'Asset': balance['asset'],
                        'Value': balance['value_usdt'],
                        'Type': 'Crypto' if portfolio['exchange'] in ['Binance', 'Bybit'] else 'Stock'
                    })
        
        if holdings_data:
            df_holdings = pd.DataFrame(holdings_data)
            
            # Risk metrics
            total_value = df_holdings['Value'].sum()
            
            # Concentration risk
            top_asset_pct = (df_holdings.groupby('Asset')['Value'].sum().max() / total_value) * 100
            num_assets = len(df_holdings['Asset'].unique())
            herfindahl_index = sum(((df_holdings.groupby('Asset')['Value'].sum() / total_value) ** 2))
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Number of Assets", num_assets)
            with col2:
                st.metric("Top Asset %", f"{top_asset_pct:.1f}%")
            with col3:
                st.metric("Herfindahl Index", f"{herfindahl_index:.3f}")
            with col4:
                diversification = "High" if herfindahl_index < 0.15 else "Medium" if herfindahl_index < 0.25 else "Low"
                st.metric("Diversification", diversification)
            
            # Asset allocation
            st.markdown("#### Asset Allocation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # By asset
                asset_allocation = df_holdings.groupby('Asset')['Value'].sum().sort_values(ascending=False).head(10)
                fig_assets = px.bar(
                    x=asset_allocation.index,
                    y=asset_allocation.values,
                    title="Top 10 Assets by Value",
                    color=asset_allocation.values,
                    color_continuous_scale='Blues'
                )
                fig_assets.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_assets, use_container_width=True)
            
            with col2:
                # By type
                type_allocation = df_holdings.groupby('Type')['Value'].sum()
                fig_types = px.pie(
                    values=type_allocation.values,
                    names=type_allocation.index,
                    title="Allocation by Asset Type",
                    color_discrete_sequence=['#2563eb', '#10b981']
                )
                fig_types.update_layout(height=300)
                st.plotly_chart(fig_types, use_container_width=True)
            
            # Exposure analysis
            st.markdown("#### Exposure Analysis")
            
            # Calculate exposure by exchange
            exchange_exposure = []
            for portfolio in portfolios:
                exchange_value = sum(b['value_usdt'] for b in portfolio['balances'] if b.get('value_usdt', 0) > 0)
                if exchange_value > 0:
                    exchange_exposure.append({
                        'Exchange': portfolio['exchange'].capitalize(),
                        'Value': exchange_value,
                        'Percentage': (exchange_value / total_value) * 100
                    })
            
            if exchange_exposure:
                df_exposure = pd.DataFrame(exchange_exposure)
                
                fig_exposure = px.bar(
                    df_exposure,
                    x='Exchange',
                    y='Percentage',
                    title="Exchange Exposure (%)",
                    color='Exchange',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_exposure.update_layout(height=300)
                st.plotly_chart(fig_exposure, use_container_width=True)
        else:
            st.info("No holdings data available for risk analysis.")
    else:
        st.info("No transaction data available. Add transactions to see risk analysis.")

with tab3:
    st.markdown("### Asset Analysis")
    
    if transactions:
        df_trans = pd.DataFrame(transactions)
        df_trans['date'] = pd.to_datetime(df_trans['date'], format='mixed')
        
        # Asset performance
        st.markdown("#### Asset-wise Performance")
        
        # Calculate per-asset metrics
        asset_metrics = []
        
        for asset in df_trans['asset'].unique():
            asset_trans = df_trans[df_trans['asset'] == asset]
            
            buy_trans = asset_trans[asset_trans['type'] == 'buy']
            sell_trans = asset_trans[asset_trans['type'] == 'sell']
            
            total_bought = buy_trans['amount'].sum()
            total_sold = sell_trans['amount'].sum()
            remaining = total_bought - total_sold
            
            avg_buy_price = (buy_trans['value_usd'] / buy_trans['amount']).mean() if len(buy_trans) > 0 else 0
            avg_sell_price = (sell_trans['value_usd'] / sell_trans['amount']).mean() if len(sell_trans) > 0 else 0
            
            # Get current holding if exists
            current_value = 0
            for portfolio in portfolios:
                for balance in portfolio['balances']:
                    if balance['asset'] == asset:
                        current_value = balance.get('value_usdt', 0)
                        break
            
            asset_metrics.append({
                'Asset': asset,
                'Total Bought': total_bought,
                'Total Sold': total_sold,
                'Remaining': remaining,
                'Avg Buy Price': avg_buy_price,
                'Avg Sell Price': avg_sell_price,
                'Current Value': current_value,
                'Transactions': len(asset_trans)
            })
        
        df_asset_metrics = pd.DataFrame(asset_metrics)
        df_asset_metrics = df_asset_metrics.sort_values('Current Value', ascending=False)
        
        st.dataframe(df_asset_metrics, use_container_width=True, hide_index=True)
        
        # Trading activity by asset
        st.markdown("#### Trading Activity by Asset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most traded assets by volume
            asset_volume = df_trans.groupby('asset')['value_usd'].sum().sort_values(ascending=False).head(10)
            fig_volume = px.bar(
                x=asset_volume.index,
                y=asset_volume.values,
                title="Top 10 Assets by Trading Volume (USD)",
                color=asset_volume.values,
                color_continuous_scale='Greens'
            )
            fig_volume.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Most traded assets by count
            asset_count = df_trans.groupby('asset').size().sort_values(ascending=False).head(10)
            fig_count = px.bar(
                x=asset_count.index,
                y=asset_count.values,
                title="Top 10 Assets by Transaction Count",
                color=asset_count.values,
                color_continuous_scale='Oranges'
            )
            fig_count.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_count, use_container_width=True)
        
        # Transaction timeline
        st.markdown("#### Transaction Timeline")
        
        # Create timeline data
        timeline_data = df_trans.copy()
        timeline_data['Month'] = timeline_data['date'].dt.to_period('M').astype(str)
        monthly_stats = timeline_data.groupby(['Month', 'type'])['value_usd'].sum().reset_index()
        
        fig_timeline = px.bar(
            monthly_stats,
            x='Month',
            y='value_usd',
            color='type',
            title="Monthly Transaction Volume by Type",
            barmode='group',
            color_discrete_map={'buy': '#10b981', 'sell': '#ef4444'}
        )
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No transaction data available. Add transactions to see asset analysis.")

# Footer
render_footer()
