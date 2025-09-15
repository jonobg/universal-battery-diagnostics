"""
Interactive Plotly Dashboard Generator
Advanced battery diagnostic visualizations with interactive dashboards
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Generate interactive Plotly dashboards for battery diagnostics"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        
        # Color schemes for different manufacturers
        self.manufacturer_colors = {
            'Milwaukee': '#FF0000',
            'Makita': '#00FFFF', 
            'DeWalt': '#FFFF00',
            'Ryobi': '#00FF00'
        }
        
        # Health status colors
        self.health_colors = {
            'excellent': '#00FF00',
            'good': '#90EE90',
            'fair': '#FFFF00',
            'poor': '#FFA500',
            'critical': '#FF0000'
        }

    def generate_fleet_overview_dashboard(self, fleet_ids: List[int] = None) -> go.Figure:
        """Generate comprehensive fleet overview dashboard"""
        logger.info("Generating fleet overview dashboard")
        
        # Get fleet data
        fleet_data = self._get_fleet_summary_data(fleet_ids)
        
        if fleet_data.empty:
            return self._create_empty_dashboard("No fleet data available")
        
        # Create subplot layout
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Fleet Health Distribution', 'Capacity vs Age', 'Health Score by Manufacturer',
                'Cycle Count Distribution', 'Cell Imbalance Analysis', 'Temperature Performance',
                'Battery Timeline', 'Usage Patterns', 'Warranty Status'
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}, {"type": "box"}],
                [{"type": "histogram"}, {"type": "scatter"}, {"type": "heatmap"}],
                [{"type": "scatter", "colspan": 2}, None, {"type": "pie"}]
            ]
        )
        
        # 1. Fleet Health Distribution
        health_dist = fleet_data['health_rating'].value_counts()
        fig.add_trace(
            go.Bar(
                x=health_dist.index,
                y=health_dist.values,
                marker_color=[self.health_colors.get(rating, '#888888') for rating in health_dist.index],
                name="Health Distribution"
            ),
            row=1, col=1
        )
        
        # 2. Capacity vs Age scatter plot
        fig.add_trace(
            go.Scatter(
                x=fleet_data['age_days'],
                y=fleet_data['capacity_percentage'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=fleet_data['cycle_count'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Cycle Count")
                ),
                text=fleet_data['model'],
                hovertemplate='<b>%{text}</b><br>Age: %{x} days<br>Capacity: %{y}%<br>Cycles: %{marker.color}<extra></extra>',
                name="Capacity vs Age"
            ),
            row=1, col=2
        )
        
        # 3. Health Score by Manufacturer box plot
        for manufacturer in fleet_data['manufacturer'].unique():
            mfg_data = fleet_data[fleet_data['manufacturer'] == manufacturer]
            fig.add_trace(
                go.Box(
                    y=mfg_data['health_score'],
                    name=manufacturer,
                    marker_color=self.manufacturer_colors.get(manufacturer, '#888888')
                ),
                row=1, col=3
            )
        
        # 4. Cycle Count Distribution
        fig.add_trace(
            go.Histogram(
                x=fleet_data['cycle_count'],
                nbinsx=20,
                marker_color='lightblue',
                name="Cycle Distribution"
            ),
            row=2, col=1
        )
        
        # 5. Cell Imbalance Analysis
        fig.add_trace(
            go.Scatter(
                x=fleet_data['cycle_count'],
                y=fleet_data['cell_imbalance_mv'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=fleet_data['health_score'],
                    colorscale='RdYlGn',
                    showscale=True
                ),
                text=fleet_data['model'],
                name="Cell Imbalance"
            ),
            row=2, col=2
        )
        
        # 6. Temperature Performance Heatmap
        temp_pivot = fleet_data.pivot_table(
            values='health_score', 
            index='manufacturer', 
            columns=pd.cut(fleet_data['age_days'], bins=5, labels=['New', 'Young', 'Medium', 'Mature', 'Old']),
            aggfunc='mean'
        )
        
        fig.add_trace(
            go.Heatmap(
                z=temp_pivot.values,
                x=temp_pivot.columns,
                y=temp_pivot.index,
                colorscale='RdYlGn',
                showscale=True
            ),
            row=2, col=3
        )
        
        # 7. Battery Timeline (age vs purchase date)
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(fleet_data['purchase_date']),
                y=fleet_data['capacity_percentage'],
                mode='markers+lines',
                marker=dict(size=8),
                text=fleet_data['model'],
                name="Timeline"
            ),
            row=3, col=1
        )
        
        # 8. Warranty Status Pie Chart
        warranty_dist = fleet_data['warranty_status'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=warranty_dist.index,
                values=warranty_dist.values,
                name="Warranty Status"
            ),
            row=3, col=3
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text="Battery Fleet Overview Dashboard",
            title_x=0.5,
            showlegend=False
        )
        
        return fig

    def generate_battery_health_report(self, battery_id: int) -> go.Figure:
        """Generate detailed health report for a specific battery"""
        logger.info(f"Generating health report for battery {battery_id}")
        
        # Get battery history
        battery_data = self._get_battery_history(battery_id)
        
        if battery_data.empty:
            return self._create_empty_dashboard(f"No data available for battery {battery_id}")
        
        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Capacity Degradation Over Time',
                'Cell Voltage Balance',
                'Health Metrics Timeline',
                'Usage Pattern Analysis'
            ),
            specs=[
                [{"secondary_y": True}, {"type": "bar"}],
                [{"secondary_y": True}, {"type": "pie"}]
            ]
        )
        
        # 1. Capacity degradation with cycle count
        fig.add_trace(
            go.Scatter(
                x=battery_data['session_date'],
                y=battery_data['capacity_percentage'],
                mode='lines+markers',
                name='Capacity %',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=battery_data['session_date'],
                y=battery_data['cycle_count'],
                mode='lines+markers',
                name='Cycle Count',
                line=dict(color='red', width=2),
                yaxis='y2'
            ),
            row=1, col=1, secondary_y=True
        )
        
        # 2. Latest cell voltage balance
        latest_cell_data = self._get_latest_cell_voltages(battery_id)
        if not latest_cell_data.empty:
            fig.add_trace(
                go.Bar(
                    x=[f"Cell {i}" for i in latest_cell_data['cell_number']],
                    y=latest_cell_data['voltage_mv'],
                    marker_color=['red' if v < latest_cell_data['voltage_mv'].mean() - 20 
                                else 'orange' if v < latest_cell_data['voltage_mv'].mean() - 10
                                else 'green' for v in latest_cell_data['voltage_mv']],
                    name='Cell Voltages'
                ),
                row=1, col=2
            )
        
        # 3. Health metrics timeline
        fig.add_trace(
            go.Scatter(
                x=battery_data['session_date'],
                y=battery_data['health_score'],
                mode='lines+markers',
                name='Health Score',
                line=dict(color='green', width=3)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=battery_data['session_date'],
                y=battery_data['internal_resistance_mohm'],
                mode='lines+markers',
                name='Resistance (mΩ)',
                line=dict(color='orange', width=2),
                yaxis='y4'
            ),
            row=2, col=1, secondary_y=True
        )
        
        # 4. Usage pattern analysis
        usage_data = self._get_usage_patterns(battery_id)
        if not usage_data.empty:
            fig.add_trace(
                go.Pie(
                    labels=usage_data['real_world_equivalent'],
                    values=usage_data['percentage_of_total_use'],
                    name='Usage Patterns'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Battery {battery_id} Health Report",
            title_x=0.5
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Capacity %", row=1, col=1)
        fig.update_yaxes(title_text="Cycle Count", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="Voltage (mV)", row=1, col=2)
        fig.update_yaxes(title_text="Health Score", row=2, col=1)
        fig.update_yaxes(title_text="Resistance (mΩ)", row=2, col=1, secondary_y=True)
        
        return fig

    def generate_comparative_analysis(self, battery_ids: List[int]) -> go.Figure:
        """Generate comparative analysis between multiple batteries"""
        logger.info(f"Generating comparative analysis for {len(battery_ids)} batteries")
        
        # Get comparison data
        comparison_data = self._get_comparative_data(battery_ids)
        
        if comparison_data.empty:
            return self._create_empty_dashboard("No comparison data available")
        
        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Health Score Comparison',
                'Capacity vs Cycle Count',
                'Degradation Rate Comparison',
                'Performance Radar Chart'
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "scatterpolar"}]
            ]
        )
        
        # 1. Health Score Comparison
        fig.add_trace(
            go.Bar(
                x=[f"Battery {bid}" for bid in comparison_data['battery_id']],
                y=comparison_data['health_score'],
                marker_color=[self.health_colors.get(self._categorize_health(score), '#888888') 
                            for score in comparison_data['health_score']],
                text=comparison_data['health_score'],
                textposition='auto',
                name='Health Scores'
            ),
            row=1, col=1
        )
        
        # 2. Capacity vs Cycle Count
        for i, battery_id in enumerate(battery_ids):
            battery_subset = comparison_data[comparison_data['battery_id'] == battery_id]
            fig.add_trace(
                go.Scatter(
                    x=battery_subset['cycle_count'],
                    y=battery_subset['capacity_percentage'],
                    mode='markers',
                    marker=dict(size=12),
                    name=f'Battery {battery_id}',
                    text=f'Battery {battery_id}'
                ),
                row=1, col=2
            )
        
        # 3. Degradation Rate Comparison
        degradation_rates = self._calculate_degradation_rates(battery_ids)
        fig.add_trace(
            go.Bar(
                x=[f"Battery {bid}" for bid in degradation_rates.keys()],
                y=list(degradation_rates.values()),
                marker_color='lightcoral',
                name='Degradation Rate'
            ),
            row=2, col=1
        )
        
        # 4. Performance Radar Chart
        for battery_id in battery_ids[:3]:  # Limit to 3 batteries for readability
            battery_perf = self._get_performance_metrics(battery_id)
            if battery_perf:
                fig.add_trace(
                    go.Scatterpolar(
                        r=list(battery_perf.values()),
                        theta=list(battery_perf.keys()),
                        fill='toself',
                        name=f'Battery {battery_id}'
                    ),
                    row=2, col=2
                )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Battery Comparative Analysis",
            title_x=0.5
        )
        
        return fig

    def generate_predictive_analysis_dashboard(self, battery_id: int) -> go.Figure:
        """Generate predictive analysis dashboard with forecasting"""
        logger.info(f"Generating predictive analysis for battery {battery_id}")
        
        # Get historical data
        historical_data = self._get_battery_history(battery_id)
        
        if historical_data.empty:
            return self._create_empty_dashboard(f"No historical data for battery {battery_id}")
        
        # Create predictions
        future_predictions = self._generate_predictions(historical_data)
        
        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Capacity Prediction',
                'Health Score Forecast',
                'Cycle Life Estimation',
                'Risk Assessment Timeline'
            )
        )
        
        # 1. Capacity Prediction
        fig.add_trace(
            go.Scatter(
                x=historical_data['session_date'],
                y=historical_data['capacity_percentage'],
                mode='lines+markers',
                name='Historical Capacity',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        if future_predictions:
            fig.add_trace(
                go.Scatter(
                    x=future_predictions['dates'],
                    y=future_predictions['capacity_pred'],
                    mode='lines',
                    name='Predicted Capacity',
                    line=dict(color='red', dash='dash')
                ),
                row=1, col=1
            )
        
        # 2. Health Score Forecast
        fig.add_trace(
            go.Scatter(
                x=historical_data['session_date'],
                y=historical_data['health_score'],
                mode='lines+markers',
                name='Historical Health',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        if future_predictions:
            fig.add_trace(
                go.Scatter(
                    x=future_predictions['dates'],
                    y=future_predictions['health_pred'],
                    mode='lines',
                    name='Predicted Health',
                    line=dict(color='orange', dash='dash')
                ),
                row=1, col=2
            )
        
        # 3. Cycle Life Estimation
        cycle_life_data = self._estimate_cycle_life(battery_id)
        if cycle_life_data:
            fig.add_trace(
                go.Bar(
                    x=['Current', 'Estimated Total', 'Remaining'],
                    y=[
                        cycle_life_data['current_cycles'],
                        cycle_life_data['estimated_total'],
                        cycle_life_data['remaining_cycles']
                    ],
                    marker_color=['blue', 'gray', 'green'],
                    name='Cycle Life'
                ),
                row=2, col=1
            )
        
        # 4. Risk Assessment Timeline
        risk_timeline = self._generate_risk_timeline(battery_id)
        if risk_timeline:
            fig.add_trace(
                go.Scatter(
                    x=risk_timeline['dates'],
                    y=risk_timeline['risk_scores'],
                    mode='lines+markers',
                    name='Risk Score',
                    line=dict(color='red'),
                    fill='tonexty'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Predictive Analysis - Battery {battery_id}",
            title_x=0.5
        )
        
        return fig

    def _get_fleet_summary_data(self, fleet_ids: List[int] = None) -> pd.DataFrame:
        """Get summary data for fleet overview"""
        with sqlite3.connect(self.database_path) as conn:
            if fleet_ids:
                placeholders = ','.join(['?' for _ in fleet_ids])
                where_clause = f"WHERE b.id IN ({placeholders})"
                params = fleet_ids
            else:
                where_clause = "WHERE b.is_active = 1"
                params = []
            
            query = f"""
            SELECT 
                b.id as battery_id,
                b.model,
                b.manufacturer,
                b.platform,
                b.nominal_capacity_ah,
                b.purchase_date,
                julianday('now') - julianday(b.purchase_date) as age_days,
                hm.capacity_percentage,
                hm.health_score,
                hm.cycle_count,
                hm.cell_imbalance_mv,
                hm.internal_resistance_mohm,
                hm.warranty_status,
                CASE 
                    WHEN hm.health_score >= 90 THEN 'excellent'
                    WHEN hm.health_score >= 75 THEN 'good'
                    WHEN hm.health_score >= 60 THEN 'fair'
                    WHEN hm.health_score >= 40 THEN 'poor'
                    ELSE 'critical'
                END as health_rating
            FROM batteries b
            LEFT JOIN diagnostic_sessions ds ON b.id = ds.battery_id 
                AND ds.session_date = (
                    SELECT MAX(session_date) 
                    FROM diagnostic_sessions ds2 
                    WHERE ds2.battery_id = b.id AND ds2.success = 1
                )
            LEFT JOIN health_metrics hm ON ds.id = hm.session_id
            {where_clause}
            """
            
            return pd.read_sql_query(query, conn, params=params)

    def _get_battery_history(self, battery_id: int) -> pd.DataFrame:
        """Get historical data for a specific battery"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT 
                ds.session_date,
                hm.capacity_percentage,
                hm.health_score,
                hm.cycle_count,
                hm.internal_resistance_mohm,
                hm.cell_imbalance_mv,
                hm.temperature_during_test_c
            FROM diagnostic_sessions ds
            JOIN health_metrics hm ON ds.id = hm.session_id
            WHERE ds.battery_id = ? AND ds.success = 1
            ORDER BY ds.session_date
            """
            
            return pd.read_sql_query(query, conn, params=(battery_id,))

    def _get_latest_cell_voltages(self, battery_id: int) -> pd.DataFrame:
        """Get latest cell voltage data for a battery"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT cv.cell_number, cv.voltage_mv
            FROM cell_voltages cv
            JOIN diagnostic_sessions ds ON cv.session_id = ds.id
            WHERE ds.battery_id = ?
            AND ds.session_date = (
                SELECT MAX(session_date) 
                FROM diagnostic_sessions ds2 
                WHERE ds2.battery_id = ? AND ds2.success = 1
            )
            ORDER BY cv.cell_number
            """
            
            return pd.read_sql_query(query, conn, params=(battery_id, battery_id))

    def _get_usage_patterns(self, battery_id: int) -> pd.DataFrame:
        """Get usage pattern data for a battery"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT 
                dh.real_world_equivalent,
                AVG(dh.percentage_of_total_use) as percentage_of_total_use
            FROM discharge_histograms dh
            JOIN diagnostic_sessions ds ON dh.session_id = ds.id
            WHERE ds.battery_id = ? AND ds.success = 1
            GROUP BY dh.real_world_equivalent
            """
            
            return pd.read_sql_query(query, conn, params=(battery_id,))

    def _get_comparative_data(self, battery_ids: List[int]) -> pd.DataFrame:
        """Get comparative data for multiple batteries"""
        with sqlite3.connect(self.database_path) as conn:
            placeholders = ','.join(['?' for _ in battery_ids])
            query = f"""
            SELECT 
                ds.battery_id,
                hm.capacity_percentage,
                hm.health_score,
                hm.cycle_count,
                hm.internal_resistance_mohm
            FROM diagnostic_sessions ds
            JOIN health_metrics hm ON ds.id = hm.session_id
            WHERE ds.battery_id IN ({placeholders})
            AND ds.session_date = (
                SELECT MAX(session_date) 
                FROM diagnostic_sessions ds2 
                WHERE ds2.battery_id = ds.battery_id AND ds2.success = 1
            )
            """
            
            return pd.read_sql_query(query, conn, params=battery_ids)

    def _calculate_degradation_rates(self, battery_ids: List[int]) -> Dict[int, float]:
        """Calculate degradation rates for multiple batteries"""
        degradation_rates = {}
        
        for battery_id in battery_ids:
            history = self._get_battery_history(battery_id)
            if len(history) >= 2:
                # Simple linear regression for degradation rate
                x = history['cycle_count'].values
                y = history['capacity_percentage'].values
                if len(x) > 1 and np.std(x) > 0:
                    slope = np.polyfit(x, y, 1)[0]
                    degradation_rates[battery_id] = abs(slope * 100)  # % per 100 cycles
                else:
                    degradation_rates[battery_id] = 0.0
            else:
                degradation_rates[battery_id] = 0.0
        
        return degradation_rates

    def _get_performance_metrics(self, battery_id: int) -> Optional[Dict[str, float]]:
        """Get normalized performance metrics for radar chart"""
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            return None
        
        return {
            'Capacity': latest_data.get('capacity_percentage', 0),
            'Health Score': latest_data.get('health_score', 0),
            'Cell Balance': max(0, 100 - latest_data.get('cell_imbalance_mv', 0)),
            'Temperature Performance': max(0, 100 - (latest_data.get('temperature_during_test_c', 25) - 25) * 2),
            'Resistance Performance': max(0, 100 - latest_data.get('internal_resistance_mohm', 0) / 2)
        }

    def _get_latest_diagnostic_data(self, battery_id: int) -> Optional[Dict[str, Any]]:
        """Get latest diagnostic data for a battery"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT 
                hm.capacity_percentage,
                hm.health_score,
                hm.cycle_count,
                hm.internal_resistance_mohm,
                hm.cell_imbalance_mv,
                hm.temperature_during_test_c
            FROM diagnostic_sessions ds
            JOIN health_metrics hm ON ds.id = hm.session_id
            WHERE ds.battery_id = ? AND ds.success = 1
            ORDER BY ds.session_date DESC
            LIMIT 1
            """
            result = conn.execute(query, (battery_id,)).fetchone()
        
        if not result:
            return None
        
        columns = ['capacity_percentage', 'health_score', 'cycle_count',
                  'internal_resistance_mohm', 'cell_imbalance_mv', 'temperature_during_test_c']
        
        return dict(zip(columns, result))

    def _generate_predictions(self, historical_data: pd.DataFrame) -> Optional[Dict[str, List]]:
        """Generate future predictions based on historical data"""
        if len(historical_data) < 3:
            return None
        
        # Simple linear extrapolation for demonstration
        dates = pd.to_datetime(historical_data['session_date'])
        
        # Generate future dates (next 6 months)
        last_date = dates.max()
        future_dates = pd.date_range(start=last_date, periods=6, freq='M')[1:]
        
        # Predict capacity
        capacity_trend = np.polyfit(range(len(historical_data)), historical_data['capacity_percentage'], 1)
        future_capacity = [np.polyval(capacity_trend, len(historical_data) + i) for i in range(1, 6)]
        
        # Predict health score
        health_trend = np.polyfit(range(len(historical_data)), historical_data['health_score'], 1)
        future_health = [np.polyval(health_trend, len(historical_data) + i) for i in range(1, 6)]
        
        return {
            'dates': future_dates,
            'capacity_pred': future_capacity,
            'health_pred': future_health
        }

    def _estimate_cycle_life(self, battery_id: int) -> Optional[Dict[str, int]]:
        """Estimate cycle life for a battery"""
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            return None
        
        current_cycles = latest_data.get('cycle_count', 0)
        current_capacity = latest_data.get('capacity_percentage', 100)
        
        # Simple estimation assuming 50% capacity at end of life
        if current_capacity > 50:
            degradation_rate = (100 - current_capacity) / max(1, current_cycles)
            remaining_degradation = current_capacity - 50
            estimated_remaining = int(remaining_degradation / max(0.1, degradation_rate))
        else:
            estimated_remaining = 0
        
        return {
            'current_cycles': current_cycles,
            'estimated_total': current_cycles + estimated_remaining,
            'remaining_cycles': estimated_remaining
        }

    def _generate_risk_timeline(self, battery_id: int) -> Optional[Dict[str, List]]:
        """Generate risk assessment timeline"""
        # Placeholder for risk timeline generation
        # In a real implementation, this would use ML models
        dates = pd.date_range(start=datetime.now(), periods=12, freq='M')
        risk_scores = np.random.uniform(0, 100, 12)  # Placeholder data
        
        return {
            'dates': dates,
            'risk_scores': risk_scores
        }

    def _categorize_health(self, health_score: int) -> str:
        """Categorize health score into rating"""
        if health_score >= 90:
            return 'excellent'
        elif health_score >= 75:
            return 'good'
        elif health_score >= 60:
            return 'fair'
        elif health_score >= 40:
            return 'poor'
        else:
            return 'critical'

    def _create_empty_dashboard(self, message: str) -> go.Figure:
        """Create empty dashboard with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            title="Dashboard",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig