#!/usr/bin/env python3
"""
Plotly visualization dashboards for Universal Battery Diagnostics Framework
Interactive web-based battery analysis and reporting
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sqlite3

from ...core.database.models import BatteryDatabase


class UniversalBatteryVisualizationDashboard:
    """Universal visualization dashboard supporting all manufacturers"""
    
    def __init__(self, database_path: str):
        self.database = BatteryDatabase(database_path)
        self.theme = "plotly_white"
        self.color_palette = {
            'milwaukee': '#FF0000',
            'makita': '#00CCFF', 
            'dewalt': '#FFCC00',
            'ryobi': '#00FF00',
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#ff7f0e', 
            'danger': '#d62728'
        }
    
    def generate_fleet_overview(self, output_path: str = "fleet_overview.html") -> str:
        """Generate comprehensive fleet overview dashboard"""
        
        # Get fleet data
        batteries = self.database.get_all_batteries()
        stats = self.database.get_database_stats()
        
        if not batteries:
            return self._generate_empty_dashboard(output_path, "No batteries found")
        
        # Create subplot structure
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Fleet Health Distribution',
                'Battery Count by Manufacturer', 
                'Health Score vs Age',
                'Session Success Rate',
                'Capacity Distribution',
                'Recent Activity'
            ),
            specs=[[{"type": "histogram"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "box"}, {"type": "scatter"}]]
        )
        
        # Prepare data
        df = pd.DataFrame(batteries)
        
        # Get health data for active batteries
        health_data = []
        for battery in batteries:
            health = self.database.get_latest_health_metrics(battery['id'])
            if health:
                health_data.append({
                    'battery_id': battery['one_key_id'],
                    'manufacturer': battery['manufacturer'],
                    'model': battery['model'],
                    'health_score': health.get('health_score', 0),
                    'capacity_percentage': health.get('capacity_percentage', 0),
                    'cycle_count': health.get('cycle_count', 0),
                    'session_count': battery.get('session_count', 0)
                })
        
        health_df = pd.DataFrame(health_data)
        
        if not health_df.empty:
            # 1. Fleet Health Distribution
            fig.add_trace(
                go.Histogram(
                    x=health_df['health_score'],
                    nbinsx=20,
                    name="Health Distribution",
                    marker_color=self.color_palette['primary']
                ),
                row=1, col=1
            )
            
            # 2. Battery Count by Manufacturer
            manufacturer_counts = df['manufacturer'].value_counts()
            colors = [self.color_palette.get(mfg.lower(), self.color_palette['primary']) 
                     for mfg in manufacturer_counts.index]
            
            fig.add_trace(
                go.Pie(
                    labels=manufacturer_counts.index,
                    values=manufacturer_counts.values,
                    marker_colors=colors,
                    name="Manufacturer Distribution"
                ),
                row=1, col=2
            )
            
            # 3. Health Score vs Age (using cycle count as proxy)
            fig.add_trace(
                go.Scatter(
                    x=health_df['cycle_count'],
                    y=health_df['health_score'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=health_df['health_score'],
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(title="Health Score")
                    ),
                    text=health_df['battery_id'],
                    name="Health vs Cycles"
                ),
                row=2, col=1
            )
            
            # 4. Session Success Rate by Manufacturer
            session_data = df.groupby('manufacturer').agg({
                'session_count': 'sum'
            }).reset_index()
            
            fig.add_trace(
                go.Bar(
                    x=session_data['manufacturer'],
                    y=session_data['session_count'],
                    marker_color=[self.color_palette.get(mfg.lower(), self.color_palette['primary']) 
                                for mfg in session_data['manufacturer']],
                    name="Total Sessions"
                ),
                row=2, col=2
            )
            
            # 5. Capacity Distribution
            fig.add_trace(
                go.Box(
                    y=health_df['capacity_percentage'],
                    x=health_df['manufacturer'],
                    name="Capacity Distribution",
                    marker_color=self.color_palette['secondary']
                ),
                row=3, col=1
            )
            
            # 6. Recent Activity (mock data for timeline)
            recent_sessions = health_df.nlargest(10, 'session_count')
            fig.add_trace(
                go.Scatter(
                    x=recent_sessions['battery_id'],
                    y=recent_sessions['session_count'],
                    mode='markers+lines',
                    marker=dict(size=10),
                    name="Session Activity"
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"🔋 Battery Fleet Dashboard - {len(batteries)} Batteries",
                x=0.5,
                font=dict(size=24)
            ),
            template=self.theme,
            height=1200,
            showlegend=False
        )
        
        # Add annotations with key stats
        annotations = [
            dict(
                text=f"Total Batteries: {stats['total_batteries']}<br>"
                     f"Successful Sessions: {stats['successful_sessions']}<br>"
                     f"Failed Sessions: {stats['failed_sessions']}",
                xref="paper", yref="paper",
                x=0.02, y=0.98, xanchor="left", yanchor="top",
                showarrow=False,
                font=dict(size=12),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            )
        ]
        fig.update_layout(annotations=annotations)
        
        # Save dashboard
        fig.write_html(output_path)
        return str(Path(output_path).absolute())
    
    def generate_individual_battery_report(self, battery_id: str, 
                                         output_path: str = None) -> str:
        """Generate detailed individual battery analysis report"""
        
        if not output_path:
            output_path = f"battery_{battery_id}_report.html"
        
        # Get battery data
        battery = self.database.get_battery_by_one_key_id(battery_id)
        if not battery:
            return self._generate_empty_dashboard(output_path, f"Battery {battery_id} not found")
        
        sessions = self.database.get_diagnostic_sessions(battery['id'])
        if not sessions:
            return self._generate_empty_dashboard(output_path, f"No diagnostic data for {battery_id}")
        
        # Create multi-panel dashboard
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Health Score Trend',
                'Capacity Degradation',
                'Cell Balance Analysis', 
                'Temperature Correlation',
                'Usage Pattern (Current Histogram)',
                'Cycle Count Progress'
            ),
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Get time-series health data
        health_history = []
        with sqlite3.connect(self.database.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT hm.*, ds.session_start 
                FROM health_metrics hm
                JOIN diagnostic_sessions ds ON hm.session_id = ds.id
                WHERE ds.battery_id = ? AND ds.success = 1
                ORDER BY ds.session_start ASC
            """, (battery['id'],))
            
            health_history = [dict(row) for row in cursor.fetchall()]
        
        if health_history:
            health_df = pd.DataFrame(health_history)
            health_df['session_date'] = pd.to_datetime(health_df['session_start'])
            
            # 1. Health Score Trend
            fig.add_trace(
                go.Scatter(
                    x=health_df['session_date'],
                    y=health_df['health_score'],
                    mode='markers+lines',
                    marker=dict(size=8, color=self.color_palette['milwaukee']),
                    line=dict(width=2),
                    name="Health Score"
                ),
                row=1, col=1
            )
            
            # 2. Capacity Degradation
            if 'capacity_percentage' in health_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=health_df['session_date'],
                        y=health_df['capacity_percentage'],
                        mode='markers+lines',
                        marker=dict(size=8, color=self.color_palette['danger']),
                        line=dict(width=2),
                        name="Capacity %"
                    ),
                    row=1, col=2
                )
            
            # 3. Cell Balance Analysis (using latest session)
            latest_session = sessions[0]['id']
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cell_number, voltage_mv FROM cell_voltages 
                    WHERE session_id = ? ORDER BY cell_number
                """, (latest_session,))
                
                cell_data = cursor.fetchall()
                if cell_data:
                    cell_nums, voltages = zip(*cell_data)
                    fig.add_trace(
                        go.Bar(
                            x=[f"Cell {i}" for i in cell_nums],
                            y=voltages,
                            marker_color=self.color_palette['secondary'],
                            name="Cell Voltages"
                        ),
                        row=2, col=1
                    )
            
            # 4. Temperature Correlation
            if 'average_temperature_c' in health_df.columns and 'health_score' in health_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=health_df['average_temperature_c'],
                        y=health_df['health_score'],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=health_df['cycle_count'] if 'cycle_count' in health_df.columns else 'blue',
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title="Cycle Count")
                        ),
                        name="Temp vs Health"
                    ),
                    row=2, col=2
                )
            
            # 5. Usage Pattern (Current Histogram) - latest session
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT current_range_min, current_range_max, time_seconds
                    FROM discharge_histogram 
                    WHERE session_id = ? 
                    ORDER BY current_range_min
                """, (latest_session,))
                
                discharge_data = cursor.fetchall()
                if discharge_data:
                    ranges = [f"{min_i}-{max_i}A" for min_i, max_i, _ in discharge_data]
                    times = [time_sec for _, _, time_sec in discharge_data]
                    
                    fig.add_trace(
                        go.Bar(
                            x=ranges,
                            y=times,
                            marker_color=self.color_palette['success'],
                            name="Usage Time"
                        ),
                        row=3, col=1
                    )
            
            # 6. Cycle Count Progress
            if 'cycle_count' in health_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=health_df['session_date'],
                        y=health_df['cycle_count'],
                        mode='markers+lines',
                        marker=dict(size=8, color=self.color_palette['warning']),
                        line=dict(width=2),
                        name="Cycle Count"
                    ),
                    row=3, col=2
                )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"🔋 {battery['manufacturer']} {battery['model']} - Detailed Analysis",
                x=0.5,
                font=dict(size=24)
            ),
            template=self.theme,
            height=1200,
            showlegend=False
        )
        
        # Add battery info annotation
        latest_health = self.database.get_latest_health_metrics(battery['id'])
        info_text = f"Battery ID: {battery['one_key_id']}<br>"
        info_text += f"Capacity: {battery['capacity_ah']} Ah<br>"
        
        if latest_health:
            info_text += f"Health Score: {latest_health.get('health_score', 'N/A')}<br>"
            info_text += f"Cycles: {latest_health.get('cycle_count', 'N/A')}<br>"
            info_text += f"Capacity: {latest_health.get('capacity_percentage', 'N/A')}%"
        
        fig.add_annotation(
            text=info_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98, xanchor="left", yanchor="top",
            showarrow=False,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1
        )
        
        # Save report
        fig.write_html(output_path)
        return str(Path(output_path).absolute())
    
    def generate_manufacturer_comparison(self, output_path: str = "manufacturer_comparison.html") -> str:
        """Generate cross-manufacturer comparison dashboard"""
        
        batteries = self.database.get_all_batteries()
        if not batteries:
            return self._generate_empty_dashboard(output_path, "No batteries for comparison")
        
        # Get health metrics for all manufacturers
        comparison_data = []
        for battery in batteries:
            health = self.database.get_latest_health_metrics(battery['id'])
            if health:
                comparison_data.append({
                    'manufacturer': battery['manufacturer'],
                    'model': battery['model'],
                    'health_score': health.get('health_score', 0),
                    'capacity_percentage': health.get('capacity_percentage', 0),
                    'cycle_count': health.get('cycle_count', 0),
                    'internal_resistance': health.get('internal_resistance_mohm', 0)
                })
        
        if not comparison_data:
            return self._generate_empty_dashboard(output_path, "No health data for comparison")
        
        df = pd.DataFrame(comparison_data)
        
        # Create comparison charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Health Score by Manufacturer',
                'Capacity Retention Comparison',
                'Cycle Count Distribution', 
                'Internal Resistance Analysis'
            ),
            specs=[[{"type": "box"}, {"type": "violin"}],
                   [{"type": "histogram"}, {"type": "bar"}]]
        )
        
        manufacturers = df['manufacturer'].unique()
        
        # 1. Health Score Box Plot
        for i, mfg in enumerate(manufacturers):
            mfg_data = df[df['manufacturer'] == mfg]
            fig.add_trace(
                go.Box(
                    y=mfg_data['health_score'],
                    name=mfg,
                    marker_color=self.color_palette.get(mfg.lower(), self.color_palette['primary'])
                ),
                row=1, col=1
            )
        
        # 2. Capacity Retention Violin Plot
        for i, mfg in enumerate(manufacturers):
            mfg_data = df[df['manufacturer'] == mfg]
            fig.add_trace(
                go.Violin(
                    y=mfg_data['capacity_percentage'],
                    name=mfg,
                    line_color=self.color_palette.get(mfg.lower(), self.color_palette['primary'])
                ),
                row=1, col=2
            )
        
        # 3. Cycle Count Distribution
        fig.add_trace(
            go.Histogram(
                x=df['cycle_count'],
                nbinsx=20,
                name="Cycle Distribution",
                marker_color=self.color_palette['secondary']
            ),
            row=2, col=1
        )
        
        # 4. Average Internal Resistance by Manufacturer
        avg_resistance = df.groupby('manufacturer')['internal_resistance'].mean().reset_index()
        fig.add_trace(
            go.Bar(
                x=avg_resistance['manufacturer'],
                y=avg_resistance['internal_resistance'],
                marker_color=[self.color_palette.get(mfg.lower(), self.color_palette['primary']) 
                            for mfg in avg_resistance['manufacturer']],
                name="Avg Internal Resistance"
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title=dict(
                text="🏭 Multi-Manufacturer Battery Comparison",
                x=0.5,
                font=dict(size=24)
            ),
            template=self.theme,
            height=1000,
            showlegend=False
        )
        
        fig.write_html(output_path)
        return str(Path(output_path).absolute())
    
    def _generate_empty_dashboard(self, output_path: str, message: str) -> str:
        """Generate empty dashboard with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"📊 {message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=24)
        )
        
        fig.update_layout(
            title="UBDF Dashboard",
            template=self.theme,
            height=600
        )
        
        fig.write_html(output_path)
        return str(Path(output_path).absolute())
    
    def generate_all_reports(self, output_dir: str = "./reports") -> Dict[str, str]:
        """Generate all available reports"""
        Path(output_dir).mkdir(exist_ok=True)
        
        reports = {}
        
        # Fleet overview
        fleet_path = Path(output_dir) / "fleet_overview.html"
        reports['fleet'] = self.generate_fleet_overview(str(fleet_path))
        
        # Individual battery reports
        batteries = self.database.get_all_batteries()
        for battery in batteries:
            if battery.get('session_count', 0) > 0:  # Only batteries with data
                battery_path = Path(output_dir) / f"battery_{battery['one_key_id']}_report.html"
                reports[f"battery_{battery['one_key_id']}"] = self.generate_individual_battery_report(
                    battery['one_key_id'], str(battery_path)
                )
        
        # Manufacturer comparison
        comparison_path = Path(output_dir) / "manufacturer_comparison.html"
        reports['comparison'] = self.generate_manufacturer_comparison(str(comparison_path))
        
        return reports