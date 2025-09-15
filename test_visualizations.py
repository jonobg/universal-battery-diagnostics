#!/usr/bin/env python3
"""
Test script for Universal Battery Diagnostics Framework visualizations
Generates mock data and creates interactive dashboards
"""

import sys
import os
sys.path.append('.')

from ubdf.testing.mock_data_generator import MockDataGenerator
from ubdf.core.visualizations.dashboard_generator import DashboardGenerator
from ubdf.core.analytics.battery_analyzer import BatteryAnalyzer
import logging
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_visualizations():
    """Test all visualization capabilities"""
    
    # Database path for testing
    db_path = "test_battery_diagnostics.db"
    
    print("🔋 Universal Battery Diagnostics Framework - Visualization Test")
    print("=" * 60)
    
    # Step 1: Generate mock data
    print("\n📊 Step 1: Generating mock fleet data...")
    generator = MockDataGenerator(db_path)
    
    success = generator.populate_database(fleet_size=15, clear_existing=True)
    if not success:
        print("❌ Failed to generate mock data")
        return False
    
    print("✅ Generated 15 mock batteries with diagnostic history")
    
    # Step 2: Verify data in database
    print("\n🔍 Step 2: Verifying database contents...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check batteries
        cursor.execute("SELECT COUNT(*) FROM batteries")
        battery_count = cursor.fetchone()[0]
        print(f"   📦 Batteries: {battery_count}")
        
        # Check diagnostic sessions
        cursor.execute("SELECT COUNT(*) FROM diagnostic_sessions")
        session_count = cursor.fetchone()[0]
        print(f"   🔬 Diagnostic sessions: {session_count}")
        
        # Check health metrics
        cursor.execute("SELECT COUNT(*) FROM health_metrics")
        health_count = cursor.fetchone()[0]
        print(f"   💚 Health records: {health_count}")
        
        # Show sample battery data
        cursor.execute("""
            SELECT b.manufacturer, b.model, h.capacity_percentage, h.health_score, h.cycle_count
            FROM batteries b
            JOIN diagnostic_sessions ds ON b.id = ds.battery_id
            JOIN health_metrics h ON ds.id = h.session_id
            WHERE ds.session_date = (
                SELECT MAX(session_date) 
                FROM diagnostic_sessions ds2 
                WHERE ds2.battery_id = b.id AND ds2.success = 1
            )
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        print(f"\n   📋 Sample battery health data:")
        for manufacturer, model, capacity, health, cycles in sample_data:
            print(f"      {manufacturer} {model}: {capacity}% capacity, {health} health score, {cycles} cycles")
    
    # Step 3: Generate fleet overview dashboard
    print("\n📈 Step 3: Generating fleet overview dashboard...")
    dashboard_gen = DashboardGenerator(db_path)
    
    try:
        fleet_dashboard = dashboard_gen.generate_fleet_overview_dashboard()
        
        # Save as HTML
        fleet_dashboard.write_html("fleet_overview_dashboard.html")
        print("✅ Fleet overview dashboard saved as 'fleet_overview_dashboard.html'")
        
        # Show dashboard info
        print(f"   📊 Dashboard contains {len(fleet_dashboard.data)} visualization traces")
        
    except Exception as e:
        print(f"❌ Failed to generate fleet dashboard: {e}")
        return False
    
    # Step 4: Generate individual battery health report
    print("\n🔋 Step 4: Generating individual battery health report...")
    
    try:
        # Get a battery with multiple sessions
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT battery_id, COUNT(*) as session_count
                FROM diagnostic_sessions 
                WHERE success = 1
                GROUP BY battery_id
                ORDER BY session_count DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                battery_id, session_count = result
                print(f"   🎯 Selected battery {battery_id} with {session_count} diagnostic sessions")
                
                battery_dashboard = dashboard_gen.generate_battery_health_report(battery_id)
                battery_dashboard.write_html(f"battery_{battery_id}_health_report.html")
                print(f"✅ Battery health report saved as 'battery_{battery_id}_health_report.html'")
                
            else:
                print("⚠️  No suitable battery found for individual report")
        
    except Exception as e:
        print(f"❌ Failed to generate battery health report: {e}")
        return False
    
    # Step 5: Generate comparative analysis
    print("\n⚖️  Step 5: Generating comparative analysis...")
    
    try:
        # Get multiple batteries for comparison
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT battery_id 
                FROM diagnostic_sessions 
                WHERE success = 1
                LIMIT 4
            """)
            battery_ids = [row[0] for row in cursor.fetchall()]
            
        if len(battery_ids) >= 2:
            print(f"   🔍 Comparing batteries: {battery_ids}")
            
            comparison_dashboard = dashboard_gen.generate_comparative_analysis(battery_ids)
            comparison_dashboard.write_html("battery_comparison_analysis.html")
            print("✅ Comparative analysis saved as 'battery_comparison_analysis.html'")
            
        else:
            print("⚠️  Insufficient batteries for comparison")
        
    except Exception as e:
        print(f"❌ Failed to generate comparative analysis: {e}")
        return False
    
    # Step 6: Generate predictive analysis
    print("\n🔮 Step 6: Generating predictive analysis...")
    
    try:
        if battery_ids:
            predictive_dashboard = dashboard_gen.generate_predictive_analysis_dashboard(battery_ids[0])
            predictive_dashboard.write_html(f"battery_{battery_ids[0]}_predictive_analysis.html")
            print(f"✅ Predictive analysis saved as 'battery_{battery_ids[0]}_predictive_analysis.html'")
        
    except Exception as e:
        print(f"❌ Failed to generate predictive analysis: {e}")
        return False
    
    # Step 7: Test battery analyzer
    print("\n🤖 Step 7: Testing battery analyzer...")
    
    try:
        analyzer = BatteryAnalyzer(db_path)
        
        # Analyze individual battery
        if battery_ids:
            assessment = analyzer.analyze_battery_health(battery_ids[0])
            print(f"   🎯 Battery {battery_ids[0]} analysis:")
            print(f"      Health Score: {assessment.overall_health_score}/100")
            print(f"      Capacity: {assessment.capacity_percentage}%")
            print(f"      Predicted Remaining Cycles: {assessment.predicted_remaining_cycles}")
            print(f"      Performance Category: {assessment.performance_category}")
            
            if assessment.risk_factors:
                print(f"      Risk Factors: {', '.join(assessment.risk_factors)}")
            
            if assessment.maintenance_recommendations:
                print(f"      Recommendations: {assessment.maintenance_recommendations[0]}")
        
        # Analyze fleet
        fleet_analytics = analyzer.analyze_fleet_performance()
        print(f"\n   🚗 Fleet analysis:")
        print(f"      Total Batteries: {fleet_analytics.total_batteries}")
        print(f"      Average Health Score: {fleet_analytics.average_health_score:.1f}")
        print(f"      Batteries Needing Attention: {len(fleet_analytics.batteries_needing_attention)}")
        
        if fleet_analytics.optimization_opportunities:
            print(f"      Optimization Opportunities: {len(fleet_analytics.optimization_opportunities)}")
        
    except Exception as e:
        print(f"❌ Failed to test battery analyzer: {e}")
        return False
    
    # Summary
    print("\n🎉 Visualization Test Complete!")
    print("=" * 60)
    print("Generated files:")
    print("  📊 fleet_overview_dashboard.html - Complete fleet visualization")
    print(f"  🔋 battery_{battery_ids[0] if battery_ids else 'X'}_health_report.html - Individual battery report")
    print("  ⚖️  battery_comparison_analysis.html - Multi-battery comparison")
    print(f"  🔮 battery_{battery_ids[0] if battery_ids else 'X'}_predictive_analysis.html - Predictive modeling")
    print("\n💡 Open these HTML files in your browser to view interactive dashboards!")
    print("🗄️  Database saved as: test_battery_diagnostics.db")
    
    return True

def cleanup():
    """Clean up test files"""
    import glob
    
    test_files = [
        "test_battery_diagnostics.db",
        "fleet_overview_dashboard.html",
        "battery_*_health_report.html",
        "battery_comparison_analysis.html",
        "battery_*_predictive_analysis.html"
    ]
    
    removed_count = 0
    for pattern in test_files:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                removed_count += 1
            except Exception:
                pass
    
    print(f"🧹 Cleaned up {removed_count} test files")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test UBD Framework visualizations")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test files and exit")
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup()
    else:
        success = test_visualizations()
        if success:
            print("\n🔧 Run with --cleanup to remove test files")
            sys.exit(0)
        else:
            print("\n❌ Test failed!")
            sys.exit(1)