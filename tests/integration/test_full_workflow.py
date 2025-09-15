#!/usr/bin/env python3
"""
End-to-end workflow tests for UBDF
"""

import pytest
import tempfile
from pathlib import Path

from ubdf.core.database.models import BatteryDatabase
from ubdf.software.visualization.plotly_dashboards import UniversalBatteryVisualizationDashboard


class TestFullWorkflow:
    """Test complete battery diagnostic workflows"""
    
    def test_complete_diagnostic_workflow(self, complete_test_setup):
        """Test full workflow: connect -> diagnose -> analyze -> report"""
        database = complete_test_setup['database']
        protocol = complete_test_setup['protocol']
        
        # Step 1: Register battery
        battery_id = database.register_battery(
            one_key_id="WORKFLOW_TEST",
            manufacturer="Milwaukee",
            model="M18B9",
            capacity_ah=9.0
        )
        assert battery_id is not None
        
        # Step 2: Start diagnostic session
        session_id = database.start_diagnostic_session(
            battery_id, test_type="integration_test"
        )
        assert session_id is not None
        
        # Step 3: Run diagnostics (mocked)
        diagnostics = protocol.read_diagnostics()
        assert diagnostics is not None
        assert diagnostics.manufacturer == "Milwaukee"
        
        # Step 4: Store diagnostic data
        for reg_addr, value in diagnostics.parsed_registers.items():
            database.store_parsed_value(
                session_id, reg_addr, f"register_{reg_addr}",
                f"0x{reg_addr:04X}", "uint16", str(value), str(value)
            )
        
        # Step 5: Store health metrics
        database.store_health_metrics(session_id, diagnostics.health_metrics)
        
        # Step 6: Complete session
        database.complete_diagnostic_session(session_id, success=True)
        
        # Step 7: Verify data was stored
        stats = database.get_database_stats()
        assert stats['total_batteries'] >= 1
        assert stats['successful_sessions'] >= 1
        
        # Step 8: Generate visualization report
        with tempfile.TemporaryDirectory() as tmpdir:
            dashboard = UniversalBatteryVisualizationDashboard(database.db_path)
            report_path = dashboard.generate_individual_battery_report(
                "WORKFLOW_TEST", 
                str(Path(tmpdir) / "test_report.html")
            )
            assert Path(report_path).exists()
    
    def test_multi_battery_fleet_analysis(self, sample_battery_fleet, clean_database):
        """Test fleet-wide analysis with multiple batteries"""
        # Fleet should have 5 batteries with diagnostic data
        stats = clean_database.get_database_stats()
        assert stats['total_batteries'] == 5
        assert stats['successful_sessions'] >= 15  # 5 batteries × 3 sessions
        
        # Test fleet visualization
        with tempfile.TemporaryDirectory() as tmpdir:
            dashboard = UniversalBatteryVisualizationDashboard(clean_database.db_path)
            fleet_report = dashboard.generate_fleet_overview(
                str(Path(tmpdir) / "fleet_overview.html")
            )
            assert Path(fleet_report).exists()
            
        # Test manufacturer comparison
        with tempfile.TemporaryDirectory() as tmpdir:
            comparison_report = dashboard.generate_manufacturer_comparison(
                str(Path(tmpdir) / "manufacturer_comparison.html")
            )
            assert Path(comparison_report).exists()
    
    def test_data_export_and_backup(self, sample_battery_fleet, clean_database):
        """Test data export functionality"""
        batteries = clean_database.get_all_batteries()
        assert len(batteries) > 0
        
        # Test exporting battery data
        first_battery = batteries[0]
        export_data = clean_database.export_battery_data(first_battery['id'])
        
        assert 'battery_info' in export_data
        assert 'sessions' in export_data
        assert len(export_data['sessions']) > 0
        
        # Verify session data completeness
        first_session = export_data['sessions'][0]
        assert 'register_values' in first_session
        assert 'health_metrics' in first_session
    
    def test_error_recovery_workflow(self, clean_database, mock_milwaukee_protocol):
        """Test workflow behavior during errors"""
        # Simulate connection failure
        mock_milwaukee_protocol.connect.return_value = False
        mock_milwaukee_protocol.get_last_error.return_value = "Connection timeout"
        
        # Workflow should handle gracefully
        assert not mock_milwaukee_protocol.connect()
        error = mock_milwaukee_protocol.get_last_error()
        assert "timeout" in error.lower()
        
        # Test diagnostic failure recovery
        mock_milwaukee_protocol.connect.return_value = True
        mock_milwaukee_protocol.read_diagnostics.return_value = None
        mock_milwaukee_protocol.get_last_error.return_value = "Communication error"
        
        diagnostics = mock_milwaukee_protocol.read_diagnostics()
        assert diagnostics is None
        assert mock_milwaukee_protocol.get_last_error() is not None


class TestDatabaseIntegrity:
    """Test database integrity and performance"""
    
    def test_concurrent_sessions(self, clean_database):
        """Test handling multiple concurrent diagnostic sessions"""
        # Register battery
        battery_id = clean_database.register_battery(
            one_key_id="CONCURRENT_TEST",
            manufacturer="Milwaukee",
            model="M18B9",
            capacity_ah=9.0
        )
        
        # Start multiple sessions
        session_ids = []
        for i in range(5):
            session_id = clean_database.start_diagnostic_session(
                battery_id, test_type=f"concurrent_test_{i}"
            )
            session_ids.append(session_id)
        
        # Complete all sessions
        for session_id in session_ids:
            clean_database.complete_diagnostic_session(session_id, success=True)
        
        # Verify all sessions recorded
        sessions = clean_database.get_diagnostic_sessions(battery_id)
        assert len(sessions) == 5
    
    def test_large_dataset_performance(self, clean_database):
        """Test performance with larger datasets"""
        import time
        
        start_time = time.time()
        
        # Create multiple batteries with sessions
        for i in range(20):
            battery_id = clean_database.register_battery(
                one_key_id=f"PERF_TEST_{i:03d}",
                manufacturer="Milwaukee",
                model="M18B9",
                capacity_ah=9.0
            )
            
            # Add sessions with health metrics
            for j in range(5):
                session_id = clean_database.start_diagnostic_session(
                    battery_id, test_type="performance_test"
                )
                
                health_metrics = {
                    'capacity_percentage': 90 - (i % 10),
                    'health_score': 85 - (j * 2),
                    'cycle_count': 100 + i * 10,
                    'internal_resistance_mohm': 20 + i + j
                }
                clean_database.store_health_metrics(session_id, health_metrics)
                clean_database.complete_diagnostic_session(session_id, success=True)
        
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed_time < 10.0  # 10 seconds max
        
        # Verify data integrity
        stats = clean_database.get_database_stats()
        assert stats['total_batteries'] >= 20
        assert stats['successful_sessions'] >= 100
    
    def test_database_consistency_checks(self, sample_battery_fleet, clean_database):
        """Test database consistency and relationships"""
        import sqlite3
        
        with sqlite3.connect(clean_database.db_path) as conn:
            # Check foreign key integrity
            cursor = conn.cursor()
            
            # Verify all sessions reference valid batteries
            cursor.execute("""
                SELECT COUNT(*) FROM diagnostic_sessions ds
                LEFT JOIN batteries b ON ds.battery_id = b.id
                WHERE b.id IS NULL
            """)
            orphaned_sessions = cursor.fetchone()[0]
            assert orphaned_sessions == 0
            
            # Verify all health metrics reference valid sessions
            cursor.execute("""
                SELECT COUNT(*) FROM health_metrics hm
                LEFT JOIN diagnostic_sessions ds ON hm.session_id = ds.id
                WHERE ds.id IS NULL
            """)
            orphaned_metrics = cursor.fetchone()[0]
            assert orphaned_metrics == 0