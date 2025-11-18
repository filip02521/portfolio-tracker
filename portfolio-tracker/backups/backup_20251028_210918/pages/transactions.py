import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import transaction history and utilities
from transaction_history import TransactionHistory
from utils import get_usd_to_pln_rate
from ui_common import load_custom_css, render_main_navigation, render_sidebar, render_footer
from config import Config

# Page configuration
st.set_page_config(
    page_title="Transactions - Portfolio Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and render navigation
load_custom_css()
render_main_navigation()

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Transaction Management</h1>
    <p class="hero-subtitle">Track and analyze all your investment transactions</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Initialize
Config.init()
th = TransactionHistory()
usd_to_pln = get_usd_to_pln_rate()

# Transaction Management Section
st.markdown("## 💼 Transaction Management")

# Create tabs
tab1, tab2, tab3 = st.tabs(["All Transactions", "Add Transaction", "Transaction Analysis"])

with tab1:
    st.markdown("### Transaction History")
    
    transactions = th.get_all_transactions()
    
    if transactions:
        # Convert to DataFrame
        df_transactions = pd.DataFrame(transactions)
        
        # Format dates - handle different date formats
        df_transactions['date'] = pd.to_datetime(df_transactions['date'], format='mixed')
        df_transactions = df_transactions.sort_values('date', ascending=False)
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            assets = ["All"] + sorted(df_transactions['asset'].unique().tolist())
            asset_filter = st.selectbox("Filter by Asset", assets)
        
        with col2:
            types = ["All"] + sorted(df_transactions['type'].unique().tolist())
            type_filter = st.selectbox("Filter by Type", types)
        
        with col3:
            exchanges = ["All"] + sorted(df_transactions['exchange'].unique().tolist())
            exchange_filter = st.selectbox("Filter by Exchange", exchanges)
        
        with col4:
            # Date range filter
            days_back = st.selectbox("Time Period", [30, 90, 180, 365, "All"], index=4)
        
        # Apply filters
        filtered_df = df_transactions.copy()
        
        if asset_filter != "All":
            filtered_df = filtered_df[filtered_df['asset'] == asset_filter]
        if type_filter != "All":
            filtered_df = filtered_df[filtered_df['type'] == type_filter]
        if exchange_filter != "All":
            filtered_df = filtered_df[filtered_df['exchange'] == exchange_filter]
        if days_back != "All":
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_df = filtered_df[filtered_df['date'] >= cutoff_date]
        
        # Display transactions
        st.markdown(f"**Found {len(filtered_df)} transactions**")
        
        # Prepare display dataframe
        display_df = filtered_df.copy()
        display_df['Date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Type'] = display_df['type'].str.capitalize()
        display_df['Asset'] = display_df['asset']
        display_df['Exchange'] = display_df['exchange'].str.capitalize()
        display_df['Amount'] = display_df['amount']
        display_df['Price (USD)'] = display_df['price_usd'].round(2)
        display_df['Value (USD)'] = display_df['value_usd'].round(2)
        display_df['Commission'] = display_df['commission'].fillna(0).round(2)
        
        # Select columns to display
        display_columns = ['Date', 'Type', 'Asset', 'Exchange', 'Amount', 'Price (USD)', 'Value (USD)', 'Commission']
        
        st.dataframe(
            display_df[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Transaction summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(filtered_df))
        
        with col2:
            total_volume = filtered_df['value_usd'].sum()
            st.metric("Total Volume (USD)", f"${total_volume:,.2f}")
        
        with col3:
            buy_count = len(filtered_df[filtered_df['type'] == 'buy'])
            st.metric("Buy Orders", buy_count)
        
        with col4:
            sell_count = len(filtered_df[filtered_df['type'] == 'sell'])
            st.metric("Sell Orders", sell_count)
        
        # Transaction actions
        st.markdown("---")
        st.markdown("### Transaction Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Edit transaction
            st.markdown("#### Edit Transaction")
            transaction_ids = filtered_df['id'].tolist()
            selected_id = st.selectbox("Select Transaction ID", transaction_ids)
            
            if st.button("Edit Selected Transaction"):
                st.info("Edit functionality coming soon!")
        
        with col2:
            # Delete transaction
            st.markdown("#### Delete Transaction")
            delete_id = st.selectbox("Select Transaction ID to Delete", transaction_ids, key="delete_id")
            
            if st.button("Delete Selected Transaction", type="secondary"):
                try:
                    th.delete_transaction(delete_id)
                    st.success(f"Transaction {delete_id} deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting transaction: {e}")
    else:
        st.info("No transactions found. Add your first transaction below!")

with tab2:
    st.markdown("### Add New Transaction")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_type = st.selectbox("Transaction Type", ["buy", "sell"])
            asset_name = st.text_input("Asset Symbol", placeholder="e.g., BTC, ETH, AAPL")
            quantity = st.number_input("Quantity", min_value=0.0, step=0.01, format="%.8f")
            price = st.number_input("Price per Unit (USD)", min_value=0.0, step=0.01)
        
        with col2:
            exchange = st.selectbox("Exchange", ["binance", "bybit", "xtb", "other"])
            transaction_date = st.date_input("Transaction Date", value=datetime.now().date())
            transaction_time = st.time_input("Transaction Time", value=datetime.now().time())
            commission = st.number_input("Commission (USD)", min_value=0.0, step=0.01, value=0.0)
        
        # Calculate total
        if quantity > 0 and price > 0:
            total_value = quantity * price
            total_with_commission = total_value + commission
            st.info(f"**Total Value:** ${total_value:,.2f} | **With Commission:** ${total_with_commission:,.2f}")
        
        submitted = st.form_submit_button("Add Transaction", type="primary")
        
        if submitted:
            if asset_name and quantity > 0 and price > 0:
                try:
                    # Combine date and time
                    transaction_datetime = datetime.combine(transaction_date, transaction_time)
                    
                    # Add transaction
                    th.add_transaction(
                        exchange=exchange,
                        asset=asset_name.upper(),
                        amount=quantity,
                        price_usd=price,
                        transaction_type=transaction_type,
                        date=transaction_datetime.isoformat(),
                        commission=commission
                    )
                    th.save_history()
                    
                    st.success(f"✅ Transaction added successfully! {transaction_type.upper()} {quantity} {asset_name.upper()} @ ${price}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding transaction: {e}")
            else:
                st.error("Please fill in all required fields (Asset, Quantity, Price)")

with tab3:
    st.markdown("### Transaction Analysis")
    
    transactions = th.get_all_transactions()
    
    if transactions:
        df_transactions = pd.DataFrame(transactions)
        df_transactions['date'] = pd.to_datetime(df_transactions['date'], format='mixed')
        
        # Transaction volume over time
        st.markdown("#### Transaction Volume Over Time")
        
        # Group by date
        daily_volume = df_transactions.groupby(df_transactions['date'].dt.date)['value_usd'].sum().reset_index()
        daily_volume.columns = ['Date', 'Volume']
        
        fig_volume = px.line(
            daily_volume, 
            x='Date', 
            y='Volume',
            title="Daily Transaction Volume (USD)",
            color_discrete_sequence=['#2563eb']
        )
        fig_volume.update_layout(height=400)
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # Transaction distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Transactions by Type")
            type_counts = df_transactions['type'].value_counts()
            fig_type = px.pie(
                values=type_counts.values, 
                names=[t.capitalize() for t in type_counts.index],
                title="Transaction Types",
                color_discrete_sequence=['#10b981', '#ef4444']
            )
            fig_type.update_layout(height=300)
            st.plotly_chart(fig_type, use_container_width=True)
        
        with col2:
            st.markdown("#### Transactions by Exchange")
            exchange_counts = df_transactions['exchange'].value_counts()
            fig_exchange = px.bar(
                x=[e.capitalize() for e in exchange_counts.index], 
                y=exchange_counts.values,
                title="Transactions by Exchange",
                color=exchange_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_exchange.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_exchange, use_container_width=True)
        
        # Trading activity metrics
        st.markdown("#### Trading Activity Metrics")
        
        # Calculate metrics
        total_days = (df_transactions['date'].max() - df_transactions['date'].min()).days + 1
        avg_daily_volume = df_transactions['value_usd'].sum() / total_days if total_days > 0 else 0
        trading_frequency = len(df_transactions) / total_days if total_days > 0 else 0
        avg_transaction_size = df_transactions['value_usd'].mean()
        total_commissions = df_transactions['commission'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Avg Daily Volume", f"${avg_daily_volume:,.2f}")
        with col2:
            st.metric("Trading Frequency", f"{trading_frequency:.2f}/day")
        with col3:
            st.metric("Avg Transaction Size", f"${avg_transaction_size:,.2f}")
        with col4:
            st.metric("Total Commissions", f"${total_commissions:,.2f}")
        
        # Asset-wise analysis
        st.markdown("#### Asset-wise Analysis")
        
        asset_analysis = df_transactions.groupby('asset').agg({
            'value_usd': 'sum',
            'amount': 'sum',
            'type': 'count',
            'commission': 'sum'
        }).reset_index()
        asset_analysis.columns = ['Asset', 'Total Volume (USD)', 'Total Amount', 'Transactions', 'Total Commission']
        asset_analysis = asset_analysis.sort_values('Total Volume (USD)', ascending=False)
        
        st.dataframe(asset_analysis, use_container_width=True, hide_index=True)
        
        # Realized PNL
        st.markdown("#### Realized Profit & Loss")
        
        try:
            realized_pnl = th.get_total_realized_pnl()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Realized PNL (USD)", f"${realized_pnl:,.2f}")
            with col2:
                pnl_pln = realized_pnl * usd_to_pln
                st.metric("Total Realized PNL (PLN)", f"{pnl_pln:,.2f} zł")
            with col3:
                # Calculate percentage if we have buy transactions
                total_invested = df_transactions[df_transactions['type'] == 'buy']['value_usd'].sum()
                pnl_percentage = (realized_pnl / total_invested * 100) if total_invested > 0 else 0
                st.metric("PNL Percentage", f"{pnl_percentage:.2f}%")
        except Exception as e:
            st.error(f"Error calculating realized PNL: {e}")
    else:
        st.info("No transactions to analyze. Add transactions to see analytics.")

# Footer
render_footer()
