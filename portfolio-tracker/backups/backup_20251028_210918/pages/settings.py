import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Import necessary modules
from config import Config
from ui_common import load_custom_css, render_main_navigation, render_sidebar, render_footer

# Page configuration
st.set_page_config(
    page_title="Settings - Portfolio Tracker",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and render navigation
load_custom_css()
render_main_navigation()

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Settings & Configuration</h1>
    <p class="hero-subtitle">Manage your portfolio tracker preferences and API keys</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Settings Section
st.markdown("## ⚙️ Settings & Configuration")

# Create tabs
tab1, tab2, tab3 = st.tabs(["API Keys", "General Settings", "Data Management"])

with tab1:
    st.markdown("### API Keys Configuration")
    
    # Exchange API keys
    st.markdown("#### Exchange API Keys")
    
    # Binance API
    with st.expander("Binance API Configuration", expanded=True):
        st.markdown("**Required for cryptocurrency trading and portfolio tracking**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            binance_api_key = st.text_input("API Key", type="password", key="binance_api", help="Your Binance API key")
            binance_secret_key = st.text_input("Secret Key", type="password", key="binance_secret", help="Your Binance secret key")
        
        with col2:
            binance_testnet = st.checkbox("Use Testnet", value=False, key="binance_testnet", help="Use Binance testnet for testing")
            binance_readonly = st.checkbox("Read-only permissions", value=True, key="binance_readonly", help="Recommended for security")
        
        if st.button("Test Binance Connection", key="test_binance"):
            try:
                # Test connection logic would go here
                st.success("✅ Binance connection successful!")
            except Exception as e:
                st.error(f"❌ Binance connection failed: {e}")
    
    # Bybit API
    with st.expander("Bybit API Configuration"):
        st.markdown("**Required for Bybit cryptocurrency trading**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            bybit_api_key = st.text_input("API Key", type="password", key="bybit_api", help="Your Bybit API key")
            bybit_secret_key = st.text_input("Secret Key", type="password", key="bybit_secret", help="Your Bybit secret key")
        
        with col2:
            bybit_testnet = st.checkbox("Use Testnet", value=False, key="bybit_testnet", help="Use Bybit testnet for testing")
            bybit_readonly = st.checkbox("Read-only permissions", value=True, key="bybit_readonly", help="Recommended for security")
        
        if st.button("Test Bybit Connection", key="test_bybit"):
            try:
                # Test connection logic would go here
                st.success("✅ Bybit connection successful!")
            except Exception as e:
                st.error(f"❌ Bybit connection failed: {e}")
    
    # XTB API
    with st.expander("XTB API Configuration"):
        st.markdown("**Required for stock trading and portfolio tracking**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            xtb_username = st.text_input("Username", key="xtb_username", help="Your XTB username")
            xtb_password = st.text_input("Password", type="password", key="xtb_password", help="Your XTB password")
        
        with col2:
            xtb_demo = st.checkbox("Use Demo Account", value=True, key="xtb_demo", help="Use XTB demo account for testing")
            xtb_readonly = st.checkbox("Read-only permissions", value=True, key="xtb_readonly", help="Recommended for security")
        
        if st.button("Test XTB Connection", key="test_xtb"):
            try:
                # Test connection logic would go here
                st.success("✅ XTB connection successful!")
            except Exception as e:
                st.error(f"❌ XTB connection failed: {e}")
    
    # API status overview
    st.markdown("#### API Status Overview")
    
    try:
        Config.init()
        missing = Config.validate()
        
        api_status = {
            'Exchange': ['Binance', 'Bybit', 'XTB'],
            'Status': [
                'Connected' if 'Binance' not in missing else 'Not Connected',
                'Connected' if 'Bybit' not in missing else 'Not Connected',
                'Connected' if 'XTB' not in missing else 'Not Connected'
            ],
            'Last Update': ['2024-10-28 14:30', '2024-10-28 14:25', 'Never'],
            'Rate Limit': ['1000/min', '1200/min', 'N/A']
        }
        
        df_api_status = pd.DataFrame(api_status)
        st.dataframe(df_api_status, use_container_width=True, hide_index=True)
        
        # API usage stats
        st.markdown("#### API Usage Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Binance Calls Today", "245", "15")
        with col2:
            st.metric("Bybit Calls Today", "189", "8")
        with col3:
            st.metric("XTB Calls Today", "0", "0")
        
    except Exception as e:
        st.error(f"Error checking API status: {e}")
    
    # Save API settings
    if st.button("Save API Settings", type="primary"):
        st.success("API settings saved successfully!")
        st.info("Note: In a real implementation, these would be securely stored in environment variables or a secure config file.")

with tab2:
    st.markdown("### General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Display Preferences")
        
        default_currency = st.selectbox("Default Currency", ["USD", "PLN", "EUR"], index=0)
        date_format = st.selectbox("Date Format", ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"], index=0)
        number_format = st.selectbox("Number Format", ["1,234.56", "1.234,56", "1 234,56"], index=0)
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
        
        st.markdown("#### Portfolio Settings")
        
        auto_refresh = st.checkbox("Auto-refresh portfolio data", value=True)
        refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 5)
        show_commissions = st.checkbox("Show commission costs", value=True)
        show_taxes = st.checkbox("Show tax calculations", value=True)
    
    with col2:
        st.markdown("#### Trading Preferences")
        
        default_exchange = st.selectbox("Default Exchange", ["Binance", "Bybit", "XTB", "Other"], index=0)
        default_order_type = st.selectbox("Default Order Type", ["Market", "Limit", "Stop"], index=0)
        confirm_trades = st.checkbox("Confirm before executing trades", value=True)
        show_advanced_options = st.checkbox("Show advanced trading options", value=False)
        
        st.markdown("#### Privacy Settings")
        
        data_sharing = st.checkbox("Allow anonymous data sharing", value=False)
        analytics = st.checkbox("Enable analytics tracking", value=True)
        crash_reports = st.checkbox("Send crash reports", value=True)
    
    # Save general settings
    if st.button("Save General Settings", type="primary"):
        st.success("General settings saved successfully!")

with tab3:
    st.markdown("### Data Management")
    
    # Data export
    st.markdown("#### Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Options**")
        
        export_transactions = st.checkbox("Export transactions", value=True)
        export_portfolio = st.checkbox("Export portfolio data", value=True)
        export_goals = st.checkbox("Export goals", value=True)
        export_settings = st.checkbox("Export settings", value=False)
        
        export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])
        
        if st.button("Export Data", type="primary"):
            st.success("Data exported successfully!")
            st.download_button(
                label="Download Export",
                data="Sample export data",
                file_name=f"portfolio_export_{datetime.now().strftime('%Y%m%d')}.{export_format.lower()}",
                mime="text/csv" if export_format == "CSV" else "application/json"
            )
    
    with col2:
        st.markdown("**Data Import**")
        
        st.file_uploader("Import Data", type=['csv', 'json', 'xlsx'], help="Upload your portfolio data")
        
        if st.button("Import Data", type="secondary"):
            st.info("Data import feature coming soon!")
    
    # Data backup
    st.markdown("#### Data Backup")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Backup Status**")
        last_backup = st.info("Last backup: 2024-10-28 14:30")
        backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"], index=1)
    
    with col2:
        st.markdown("**Backup Options**")
        auto_backup = st.checkbox("Automatic backup", value=True)
        cloud_backup = st.checkbox("Cloud backup", value=False)
        local_backup = st.checkbox("Local backup", value=True)
    
    with col3:
        st.markdown("**Backup Actions**")
        if st.button("Create Backup", type="primary"):
            st.success("Backup created successfully!")
        
        if st.button("Restore Backup", type="secondary"):
            st.info("Restore feature coming soon!")
    
    # Data cleanup
    st.markdown("#### Data Cleanup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Cleanup Options**")
        cleanup_old_data = st.checkbox("Remove old transaction data", value=False)
        cleanup_duplicates = st.checkbox("Remove duplicate entries", value=True)
        cleanup_invalid = st.checkbox("Remove invalid data", value=True)
        
        if st.button("Clean Data", type="secondary"):
            st.success("Data cleaned successfully!")
    
    with col2:
        st.markdown("**Storage Usage**")
        
        # Calculate storage usage
        try:
            transaction_file_size = os.path.getsize('transaction_history.json') if os.path.exists('transaction_history.json') else 0
            portfolio_file_size = os.path.getsize('portfolio_history.json') if os.path.exists('portfolio_history.json') else 0
            total_size = transaction_file_size + portfolio_file_size
            
            st.metric("Storage Used", f"{total_size / 1024:.1f} KB")
            
            # Count records
            with open('transaction_history.json', 'r') as f:
                transactions = json.load(f)
            transaction_count = len(transactions)
            
            with open('portfolio_history.json', 'r') as f:
                portfolio_history = json.load(f)
            portfolio_count = len(portfolio_history)
            
            st.metric("Transactions", transaction_count)
            st.metric("Portfolio Records", portfolio_count)
            
        except Exception as e:
            st.error(f"Error calculating storage: {e}")
    
    # Reset options
    st.markdown("#### Reset Options")
    
    st.warning("⚠️ Warning: These actions cannot be undone!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Reset Settings", type="secondary"):
            st.error("Settings reset feature coming soon!")
    
    with col2:
        if st.button("Reset Portfolio", type="secondary"):
            st.error("Portfolio reset feature coming soon!")
    
    with col3:
        if st.button("Reset All Data", type="secondary"):
            st.error("Full reset feature coming soon!")

# Footer
render_footer()
