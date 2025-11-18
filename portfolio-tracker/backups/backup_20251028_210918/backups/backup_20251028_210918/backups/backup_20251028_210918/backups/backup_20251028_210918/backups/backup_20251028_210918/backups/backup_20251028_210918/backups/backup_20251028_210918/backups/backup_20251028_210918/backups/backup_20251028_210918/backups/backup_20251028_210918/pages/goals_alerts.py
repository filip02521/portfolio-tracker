import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# Import necessary modules
from portfolio_tracker import PortfolioTracker
from transaction_history import TransactionHistory
from utils import get_usd_to_pln_rate
from ui_common import load_custom_css, render_main_navigation, render_sidebar, render_footer
from config import Config

# Page configuration
st.set_page_config(
    page_title="Goals & Alerts - Portfolio Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and render navigation
load_custom_css()
render_main_navigation()

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Goals & Alerts</h1>
    <p class="hero-subtitle">Set financial goals and manage investment alerts</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
currency = render_sidebar()

# Initialize
Config.init()
tracker = PortfolioTracker()
th = TransactionHistory()
usd_to_pln = get_usd_to_pln_rate()

# Get current portfolio value
portfolios = tracker.get_all_portfolios()
total_value_usd = sum(p['total_value_usdt'] for p in portfolios)
total_value_pln = total_value_usd * usd_to_pln

# Goals & Alerts Section
st.markdown("## 🎯 Goals & Alerts")

# Create tabs
tab1, tab2 = st.tabs(["Financial Goals", "Price Alerts"])

with tab1:
    st.markdown("### Financial Goals")
    
    # Load goals
    goals_file = 'financial_goals.json'
    
    def load_goals():
        if os.path.exists(goals_file):
            try:
                with open(goals_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_goals(goals):
        with open(goals_file, 'w') as f:
            json.dump(goals, f, indent=2)
    
    goals = load_goals()
    
    # Goals overview
    if goals:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            active_goals = [g for g in goals if not g.get('completed', False)]
            st.metric("Active Goals", len(active_goals))
        
        with col2:
            completed_goals = [g for g in goals if g.get('completed', False)]
            st.metric("Completed Goals", len(completed_goals))
        
        with col3:
            total_target = sum(g['target_amount'] for g in active_goals)
            st.metric(f"Total Target ({currency})", f"${total_target:,.0f}" if currency == "USD" else f"{total_target * usd_to_pln:,.0f} zł")
        
        # Display active goals
        st.markdown("#### Active Goals")
        
        current_value_display = total_value_pln if currency == "PLN" else total_value_usd
        
        for i, goal in enumerate(active_goals):
            with st.expander(f"**{goal['name']}** - {goal['progress']:.0f}% Complete"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Target:** ${goal['target_amount']:,.0f}")
                    st.markdown(f"**Current Progress:** ${current_value_display:,.0f}")
                    progress = min((current_value_display / goal['target_amount']) * 100, 100)
                    st.progress(progress / 100)
                    st.caption(f"{progress:.1f}% complete")
                
                with col2:
                    st.markdown(f"**Target Date:**")
                    st.markdown(goal['target_date'])
                    
                    days_remaining = (datetime.fromisoformat(goal['target_date']) - datetime.now()).days
                    st.markdown(f"**Days Remaining:**")
                    st.markdown(f"{days_remaining} days")
                
                with col3:
                    st.markdown(f"**Priority:**")
                    st.markdown(goal['priority'])
                    
                    if st.button(f"Mark Complete", key=f"complete_{i}"):
                        goals[i]['completed'] = True
                        save_goals(goals)
                        st.success("Goal marked as complete!")
                        st.rerun()
    else:
        st.info("No goals set yet. Add your first financial goal below!")
    
    # Add new goal
    st.markdown("#### Add New Goal")
    
    with st.form("new_goal_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund")
            target_amount = st.number_input("Target Amount (USD)", min_value=0, step=100)
            target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=365))
        
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            goal_type = st.selectbox("Goal Type", ["Savings", "Investment", "Debt Payoff", "Other"])
            notes = st.text_area("Notes (optional)", placeholder="Add any notes about this goal")
        
        submitted = st.form_submit_button("Add Goal", type="primary")
        
        if submitted:
            if goal_name and target_amount > 0:
                new_goal = {
                    'id': len(goals) + 1,
                    'name': goal_name,
                    'target_amount': target_amount,
                    'current_amount': current_value_display,
                    'progress': min((current_value_display / target_amount) * 100, 100),
                    'target_date': target_date.isoformat(),
                    'priority': priority,
                    'type': goal_type,
                    'notes': notes,
                    'completed': False,
                    'created_date': datetime.now().isoformat()
                }
                goals.append(new_goal)
                save_goals(goals)
                st.success(f"✅ Goal '{goal_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please provide a goal name and target amount")

with tab2:
    st.markdown("### Price Alerts")
    
    # Load alerts
    alerts_file = 'price_alerts.json'
    
    def load_alerts():
        if os.path.exists(alerts_file):
            try:
                with open(alerts_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_alerts(alerts):
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    alerts = load_alerts()
    
    # Alerts overview
    if alerts:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            active_alerts = [a for a in alerts if a.get('active', True)]
            st.metric("Active Alerts", len(active_alerts))
        
        with col2:
            triggered_alerts = [a for a in alerts if a.get('triggered', False)]
            st.metric("Triggered Alerts", len(triggered_alerts))
        
        with col3:
            st.metric("Total Alerts", len(alerts))
        
        # Display active alerts
        st.markdown("#### Active Alerts")
        
        if active_alerts:
            for i, alert in enumerate(active_alerts):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{alert['asset']}**")
                    st.caption(f"Type: {alert['alert_type']}")
                
                with col2:
                    st.markdown(f"**Condition:** {alert['condition']} ${alert['threshold']}")
                    st.caption(f"Created: {alert['created_date'][:10]}")
                
                with col3:
                    status = "🔔 Active" if alert.get('active', True) else "⏸️ Paused"
                    st.markdown(status)
                
                with col4:
                    if st.button("Delete", key=f"delete_alert_{i}"):
                        alerts.pop(i)
                        save_alerts(alerts)
                        st.rerun()
        else:
            st.info("No active alerts")
    else:
        st.info("No alerts configured yet. Add your first alert below!")
    
    # Add new alert
    st.markdown("#### Add New Alert")
    
    with st.form("new_alert_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get list of assets from portfolio
            assets = set()
            for portfolio in portfolios:
                for balance in portfolio['balances']:
                    if balance.get('value_usdt', 0) > 0:
                        assets.add(balance['asset'])
            
            asset_options = ["Custom"] + sorted(list(assets))
            selected_asset = st.selectbox("Select Asset", asset_options)
            
            if selected_asset == "Custom":
                alert_asset = st.text_input("Enter Asset Symbol", placeholder="e.g., BTC")
            else:
                alert_asset = selected_asset
            
            alert_type = st.selectbox("Alert Type", ["Price Alert", "Portfolio Value", "Daily Change"])
        
        with col2:
            condition = st.selectbox("Condition", ["Above", "Below"])
            threshold = st.number_input("Threshold Value (USD)", min_value=0.0, step=0.01)
            notification_method = st.multiselect("Notification Method", ["Email", "Push", "In-App"], default=["In-App"])
        
        submitted_alert = st.form_submit_button("Add Alert", type="primary")
        
        if submitted_alert:
            if alert_asset and threshold > 0:
                new_alert = {
                    'id': len(alerts) + 1,
                    'asset': alert_asset,
                    'alert_type': alert_type,
                    'condition': condition,
                    'threshold': threshold,
                    'notification_method': notification_method,
                    'active': True,
                    'triggered': False,
                    'created_date': datetime.now().isoformat()
                }
                alerts.append(new_alert)
                save_alerts(alerts)
                st.success(f"✅ Alert for {alert_asset} added successfully!")
                st.rerun()
            else:
                st.error("Please provide an asset and threshold value")
    
    # Alert history
    if triggered_alerts:
        st.markdown("#### Alert History")
        
        for alert in triggered_alerts[-5:]:  # Show last 5 triggered alerts
            st.info(f"🔔 {alert['asset']} {alert['condition']} ${alert['threshold']} - Triggered on {alert.get('triggered_date', 'Unknown')[:10]}")

# Footer
render_footer()
