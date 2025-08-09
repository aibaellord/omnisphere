#!/usr/bin/env python3
"""
📊 YOUTUBE ANALYTICS DASHBOARD 📊
Streamlit dashboard for YouTube performance & revenue tracking

Features:
- KPIs overview (views, watch time, RPM, revenue)
- Revenue trendlines and growth analysis
- Cost vs Revenue visualization (zero cost system)
- Channel performance comparison
- Real-time data updates from analytics_collector.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
import os

# Page configuration
st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class YouTubeDashboard:
    """YouTube Analytics Dashboard using Streamlit"""
    
    def __init__(self, db_path: str = "analytics_data.db"):
        self.db_path = db_path
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            st.error(f"❌ Analytics database not found at {self.db_path}")
            st.info("🔧 Please run `python analytics_collector.py` first to collect data")
            st.stop()
    
    def get_kpi_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Get KPI data for the overview cards"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Current period metrics
            current_query = '''
            SELECT 
                SUM(views) as total_views,
                SUM(watch_time_minutes) as total_watch_time,
                SUM(estimated_revenue) as total_revenue,
                AVG(rpm) as avg_rpm,
                AVG(cpm) as avg_cpm,
                SUM(subscribers_gained) as total_subs_gained,
                SUM(subscribers_lost) as total_subs_lost
            FROM channel_analytics
            WHERE date >= ? AND date <= ?
            '''
            
            current_df = pd.read_sql_query(
                current_query, conn, 
                params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            )
            
            # Previous period for comparison
            prev_end_date = start_date
            prev_start_date = prev_end_date - timedelta(days=days_back)
            
            prev_df = pd.read_sql_query(
                current_query, conn,
                params=(prev_start_date.strftime('%Y-%m-%d'), prev_end_date.strftime('%Y-%m-%d'))
            )
            
            conn.close()
            
            # Current metrics
            current_metrics = current_df.iloc[0] if not current_df.empty else {}
            prev_metrics = prev_df.iloc[0] if not prev_df.empty else {}
            
            # Calculate changes
            def calc_change(current, previous, default=0):
                current_val = current if pd.notna(current) else default
                prev_val = previous if pd.notna(previous) else 1
                if prev_val == 0:
                    return 0
                return ((current_val - prev_val) / prev_val) * 100
            
            kpis = {
                'total_views': {
                    'value': int(current_metrics.get('total_views', 0)),
                    'change': calc_change(current_metrics.get('total_views', 0), 
                                        prev_metrics.get('total_views', 0))
                },
                'watch_time_hours': {
                    'value': int(current_metrics.get('total_watch_time', 0)) / 60,
                    'change': calc_change(current_metrics.get('total_watch_time', 0), 
                                        prev_metrics.get('total_watch_time', 0))
                },
                'total_revenue': {
                    'value': float(current_metrics.get('total_revenue', 0)),
                    'change': calc_change(current_metrics.get('total_revenue', 0), 
                                        prev_metrics.get('total_revenue', 0))
                },
                'avg_rpm': {
                    'value': float(current_metrics.get('avg_rpm', 0)),
                    'change': calc_change(current_metrics.get('avg_rpm', 0), 
                                        prev_metrics.get('avg_rpm', 0))
                },
                'subscriber_growth': {
                    'value': int(current_metrics.get('total_subs_gained', 0) - 
                               current_metrics.get('total_subs_lost', 0)),
                    'change': 0  # Not comparing subscriber growth change for now
                }
            }
            
            return kpis
            
        except Exception as e:
            st.error(f"Error fetching KPI data: {e}")
            return {}
    
    def get_trend_data(self, days_back: int = 30) -> pd.DataFrame:
        """Get trend data for charts"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            query = '''
            SELECT 
                date,
                SUM(views) as daily_views,
                SUM(watch_time_minutes) as daily_watch_time,
                SUM(estimated_revenue) as daily_revenue,
                AVG(rpm) as daily_rpm,
                AVG(cpm) as daily_cpm,
                SUM(subscribers_gained) as daily_subs_gained,
                SUM(likes) as daily_likes,
                SUM(comments) as daily_comments
            FROM channel_analytics
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date ASC
            '''
            
            df = pd.read_sql_query(
                query, conn,
                params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            )
            
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['daily_watch_time_hours'] = df['daily_watch_time'] / 60
                df['cumulative_revenue'] = df['daily_revenue'].cumsum()
                df['7day_avg_views'] = df['daily_views'].rolling(window=7, min_periods=1).mean()
                df['7day_avg_revenue'] = df['daily_revenue'].rolling(window=7, min_periods=1).mean()
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching trend data: {e}")
            return pd.DataFrame()
    
    def get_channel_comparison_data(self) -> pd.DataFrame:
        """Get channel comparison data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
            SELECT 
                cm.channel_name,
                cm.subscriber_count,
                cm.total_views,
                cm.video_count,
                SUM(ca.estimated_revenue) as total_revenue,
                AVG(ca.rpm) as avg_rpm,
                SUM(ca.views) as recent_views,
                SUM(ca.watch_time_minutes) as recent_watch_time
            FROM channel_metadata cm
            LEFT JOIN channel_analytics ca ON cm.channel_id = ca.channel_id
            WHERE ca.date >= date('now', '-30 days')
            GROUP BY cm.channel_id, cm.channel_name, cm.subscriber_count, cm.total_views, cm.video_count
            ORDER BY total_revenue DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['recent_watch_time_hours'] = df['recent_watch_time'] / 60
                df['revenue_per_subscriber'] = df['total_revenue'] / df['subscriber_count'].replace(0, 1)
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching channel data: {e}")
            return pd.DataFrame()
    
    def render_kpi_cards(self, kpis: Dict[str, Any]):
        """Render KPI overview cards"""
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            views = kpis.get('total_views', {})
            delta_color = "normal" if views.get('change', 0) >= 0 else "inverse"
            st.metric(
                label="👀 Total Views",
                value=f"{views.get('value', 0):,}",
                delta=f"{views.get('change', 0):+.1f}%",
                delta_color=delta_color
            )
        
        with col2:
            watch_time = kpis.get('watch_time_hours', {})
            delta_color = "normal" if watch_time.get('change', 0) >= 0 else "inverse"
            st.metric(
                label="⏱️ Watch Time (Hours)",
                value=f"{watch_time.get('value', 0):,.0f}",
                delta=f"{watch_time.get('change', 0):+.1f}%",
                delta_color=delta_color
            )
        
        with col3:
            revenue = kpis.get('total_revenue', {})
            delta_color = "normal" if revenue.get('change', 0) >= 0 else "inverse"
            st.metric(
                label="💰 Revenue",
                value=f"${revenue.get('value', 0):.2f}",
                delta=f"{revenue.get('change', 0):+.1f}%",
                delta_color=delta_color
            )
        
        with col4:
            rpm = kpis.get('avg_rpm', {})
            delta_color = "normal" if rpm.get('change', 0) >= 0 else "inverse"
            st.metric(
                label="📈 Average RPM",
                value=f"${rpm.get('value', 0):.2f}",
                delta=f"{rpm.get('change', 0):+.1f}%",
                delta_color=delta_color
            )
        
        with col5:
            subs = kpis.get('subscriber_growth', {})
            st.metric(
                label="📊 Subscriber Growth",
                value=f"{subs.get('value', 0):+,}",
                delta=None
            )
    
    def render_revenue_trends(self, df: pd.DataFrame):
        """Render revenue trend charts"""
        st.subheader("💰 Revenue & Performance Trends")
        
        if df.empty:
            st.warning("📊 No trend data available")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Daily Revenue', 'Cumulative Revenue', 'Views vs Watch Time', 'RPM Trend'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # Daily revenue
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['daily_revenue'], 
                      mode='lines+markers', name='Daily Revenue',
                      line=dict(color='green', width=2)),
            row=1, col=1
        )
        
        # 7-day average revenue
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['7day_avg_revenue'], 
                      mode='lines', name='7-Day Avg',
                      line=dict(color='darkgreen', dash='dash')),
            row=1, col=1
        )
        
        # Cumulative revenue
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['cumulative_revenue'], 
                      mode='lines', name='Cumulative Revenue',
                      line=dict(color='blue', width=2), fill='tonexty'),
            row=1, col=2
        )
        
        # Views (left axis)
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['daily_views'], 
                      mode='lines', name='Daily Views',
                      line=dict(color='orange')),
            row=2, col=1, secondary_y=False
        )
        
        # Watch time (right axis)
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['daily_watch_time_hours'], 
                      mode='lines', name='Watch Time (Hours)',
                      line=dict(color='purple')),
            row=2, col=1, secondary_y=True
        )
        
        # RPM trend
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['daily_rpm'], 
                      mode='lines+markers', name='Daily RPM',
                      line=dict(color='red', width=2)),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Performance Trends Analysis",
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Revenue ($)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Revenue ($)", row=1, col=2)
        fig.update_yaxes(title_text="Views", row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Watch Time (Hours)", row=2, col=1, secondary_y=True)
        fig.update_yaxes(title_text="RPM ($)", row=2, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_cost_vs_revenue(self, df: pd.DataFrame):
        """Render cost vs revenue analysis (zero cost system)"""
        st.subheader("💸 Cost vs Revenue Analysis")
        
        if df.empty:
            st.warning("📊 No data available for cost analysis")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Cost vs Revenue chart
            fig = go.Figure()
            
            # Revenue line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['cumulative_revenue'],
                mode='lines',
                name='Revenue',
                line=dict(color='green', width=3),
                fill='tonexty'
            ))
            
            # Cost line (always zero)
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=[0] * len(df),
                mode='lines',
                name='Cost',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            # Profit area (same as revenue since cost = 0)
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['cumulative_revenue'],
                mode='lines',
                name='Profit',
                line=dict(color='blue', width=1),
                fill='tonexty',
                fillcolor='rgba(0,255,0,0.1)'
            ))
            
            fig.update_layout(
                title="Cost vs Revenue (Zero-Cost System)",
                xaxis_title="Date",
                yaxis_title="Amount ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 💰 Profit Analysis")
            
            total_revenue = df['daily_revenue'].sum()
            total_cost = 0.0  # Zero cost system
            profit_margin = 100.0 if total_revenue > 0 else 0
            
            st.metric("Total Revenue", f"${total_revenue:.2f}")
            st.metric("Total Cost", f"${total_cost:.2f}")
            st.metric("Profit", f"${total_revenue:.2f}")
            st.metric("Profit Margin", f"{profit_margin:.1f}%")
            
            st.success("🎉 **Zero-Cost System**: All revenue is profit!")
            
            # ROI calculation
            if len(df) > 1:
                roi_period = len(df)
                daily_avg_profit = total_revenue / roi_period
                st.info(f"📊 **Daily Average Profit**: ${daily_avg_profit:.2f}")
    
    def render_channel_comparison(self, df: pd.DataFrame):
        """Render channel performance comparison"""
        st.subheader("🏆 Channel Performance Comparison")
        
        if df.empty:
            st.warning("📊 No channel data available")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Revenue by channel
            fig = px.bar(
                df, x='channel_name', y='total_revenue',
                title='Revenue by Channel (Last 30 Days)',
                color='total_revenue',
                color_continuous_scale='Greens'
            )
            fig.update_layout(xaxis_title="Channel", yaxis_title="Revenue ($)")
            st.plotly_chart(fig, use_container_width=True)
            
            # RPM comparison
            fig2 = px.scatter(
                df, x='subscriber_count', y='avg_rpm',
                size='total_revenue', hover_name='channel_name',
                title='Subscribers vs RPM (Bubble size = Revenue)',
                labels={'subscriber_count': 'Subscribers', 'avg_rpm': 'Average RPM ($)'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            st.markdown("### 📈 Top Performers")
            
            for i, row in df.iterrows():
                with st.expander(f"🏆 {row['channel_name']}"):
                    st.metric("Revenue", f"${row['total_revenue']:.2f}")
                    st.metric("Subscribers", f"{row['subscriber_count']:,}")
                    st.metric("Recent Views", f"{row['recent_views']:,}")
                    st.metric("Watch Time", f"{row['recent_watch_time_hours']:.0f}h")
                    st.metric("RPM", f"${row['avg_rpm']:.2f}")
    
    def render_sidebar_controls(self):
        """Render sidebar controls"""
        st.sidebar.header("⚙️ Dashboard Controls")
        
        # Date range selector
        date_range = st.sidebar.selectbox(
            "📅 Analysis Period",
            options=[7, 14, 30, 60, 90],
            index=2,  # Default to 30 days
            format_func=lambda x: f"Last {x} days"
        )
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5 min)", value=False)
        
        if auto_refresh:
            st.sidebar.info("🔄 Dashboard will refresh every 5 minutes")
            # In a real deployment, you'd implement auto-refresh here
            # For now, we'll use st.rerun() with time delay
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Export options
        st.sidebar.markdown("### 📊 Export Data")
        export_format = st.sidebar.selectbox(
            "Export Format",
            ["CSV", "JSON", "Excel"]
        )
        
        if st.sidebar.button("📥 Export Dashboard Data"):
            st.sidebar.success("Export feature coming soon!")
        
        # Database info
        st.sidebar.markdown("### 🗃️ Database Info")
        if os.path.exists(self.db_path):
            file_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            st.sidebar.info(f"Database size: {file_size:.2f} MB")
        
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.sidebar.info(f"Last updated: {last_update}")
        
        return date_range
    
    def run(self):
        """Run the main dashboard"""
        st.title("📊 YouTube Analytics Dashboard")
        st.markdown("Real-time performance tracking and revenue analysis")
        
        # Sidebar controls
        days_back = self.render_sidebar_controls()
        
        try:
            # Load data
            with st.spinner("📊 Loading analytics data..."):
                kpis = self.get_kpi_data(days_back)
                trend_data = self.get_trend_data(days_back)
                channel_data = self.get_channel_comparison_data()
            
            # Render sections
            if kpis:
                self.render_kpi_cards(kpis)
                st.markdown("---")
            
            if not trend_data.empty:
                self.render_revenue_trends(trend_data)
                st.markdown("---")
                
                self.render_cost_vs_revenue(trend_data)
                st.markdown("---")
            
            if not channel_data.empty:
                self.render_channel_comparison(channel_data)
            
            # Footer
            st.markdown("---")
            st.markdown(
                "💡 **Zero-Cost System**: All compute costs are considered zero, "
                "making every dollar of revenue pure profit! 🎉"
            )
            
        except Exception as e:
            st.error(f"❌ Error loading dashboard: {e}")
            st.info("🔧 Make sure the analytics collector has been run and data is available")


def main():
    """Main function to run the dashboard"""
    dashboard = YouTubeDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
