"""
Mock Data Generator for Universal Battery Diagnostics Framework
Generates realistic test data for development, testing, and demonstrations
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
import uuid
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BatteryProfile:
    """Template for generating realistic battery data"""
    manufacturer: str
    model: str
    platform: str
    nominal_voltage_v: float
    nominal_capacity_ah: float
    cell_count: int
    typical_cycle_life: int
    degradation_rate_base: float  # % per 100 cycles
    usage_patterns: Dict[str, float]  # current ranges and percentages

class MockDataGenerator:
    """Generate realistic mock data for battery diagnostics testing"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        
        # Battery profiles for different manufacturers
        self.battery_profiles = {
            'Milwaukee_M18B5': BatteryProfile(
                manufacturer='Milwaukee',
                model='M18B5',
                platform='M18',
                nominal_voltage_v=18.0,
                nominal_capacity_ah=5.0,
                cell_count=5,
                typical_cycle_life=1000,
                degradation_rate_base=1.5,
                usage_patterns={
                    'drill': 0.3, 'grinder': 0.2, 'saw': 0.25, 'impact': 0.15, 'idle': 0.1
                }
            ),
            'Makita_BL1850B': BatteryProfile(
                manufacturer='Makita',
                model='BL1850B',
                platform='LXT',
                nominal_voltage_v=18.0,
                nominal_capacity_ah=5.0,
                cell_count=5,
                typical_cycle_life=1000,
                degradation_rate_base=1.2,
                usage_patterns={
                    'drill': 0.35, 'grinder': 0.15, 'saw': 0.3, 'impact': 0.12, 'idle': 0.08
                }
            ),
            'DeWalt_DCB606': BatteryProfile(
                manufacturer='DeWalt',
                model='DCB606',
                platform='FLEXVOLT',
                nominal_voltage_v=20.0,
                nominal_capacity_ah=6.0,
                cell_count=10,
                typical_cycle_life=1500,
                degradation_rate_base=1.0,
                usage_patterns={
                    'drill': 0.25, 'grinder': 0.3, 'saw': 0.25, 'impact': 0.1, 'idle': 0.1
                }
            ),
            'Ryobi_P193': BatteryProfile(
                manufacturer='Ryobi',
                model='P193',
                platform='ONE+',
                nominal_voltage_v=18.0,
                nominal_capacity_ah=6.0,
                cell_count=5,
                typical_cycle_life=800,
                degradation_rate_base=2.0,
                usage_patterns={
                    'drill': 0.4, 'grinder': 0.1, 'saw': 0.2, 'impact': 0.2, 'idle': 0.1
                }
            )
        }

    def generate_fleet_data(self, fleet_size: int, start_date: datetime = None) -> Dict[str, List[Dict]]:
        """Generate a complete fleet of batteries with realistic data"""
        logger.info(f"Generating fleet data for {fleet_size} batteries")
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365*2)  # 2 years ago
        
        fleet_data = {
            'batteries': [],
            'diagnostic_sessions': [],
            'health_metrics': [],
            'cell_voltages': [],
            'discharge_histograms': [],
            'raw_register_data': [],
            'parsed_register_values': []
        }
        
        for i in range(fleet_size):
            battery_id = i + 1
            
            # Select random battery profile
            profile_name = random.choice(list(self.battery_profiles.keys()))
            profile = self.battery_profiles[profile_name]
            
            # Generate battery record
            battery = self._generate_battery_record(battery_id, profile, start_date)
            fleet_data['batteries'].append(battery)
            
            # Generate diagnostic history
            diagnostics = self._generate_diagnostic_history(battery_id, battery, profile)
            fleet_data['diagnostic_sessions'].extend(diagnostics['sessions'])
            fleet_data['health_metrics'].extend(diagnostics['health_metrics'])
            fleet_data['cell_voltages'].extend(diagnostics['cell_voltages'])
            fleet_data['discharge_histograms'].extend(diagnostics['discharge_histograms'])
            fleet_data['raw_register_data'].extend(diagnostics['raw_register_data'])
            fleet_data['parsed_register_values'].extend(diagnostics['parsed_register_values'])
        
        return fleet_data

    def populate_database(self, fleet_size: int = 50, clear_existing: bool = False) -> bool:
        """Populate database with mock fleet data"""
        logger.info(f"Populating database with {fleet_size} mock batteries")
        
        try:
            if clear_existing:
                self._clear_database()
            
            # Generate fleet data
            fleet_data = self.generate_fleet_data(fleet_size)
            
            # Insert into database
            with sqlite3.connect(self.database_path) as conn:
                # Create tables from schema if they don't exist
                try:
                    with open('ubdf/core/database/enhanced_schema.sql', 'r') as f:
                        schema_sql = f.read()
                        conn.executescript(schema_sql)
                except FileNotFoundError:
                    logger.warning("Schema file not found, assuming tables exist")
                
                # Insert all data
                self._insert_fleet_data(conn, fleet_data)
                conn.commit()
            
            logger.info(f"Successfully populated database with {fleet_size} batteries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate database: {e}")
            return False

    def _generate_battery_record(self, battery_id: int, profile: BatteryProfile, 
                                start_date: datetime) -> Dict[str, Any]:
        """Generate a realistic battery record"""
        
        age_days = random.randint(1, 730)  # 0-2 years
        purchase_date = start_date + timedelta(days=age_days)
        
        # Generate serial numbers
        serial_number = f"{profile.manufacturer[:2].upper()}{random.randint(100000, 999999)}"
        one_key_id = f"{uuid.uuid4().hex[:8].upper()}" if profile.manufacturer == 'Milwaukee' else None
        
        return {
            'id': battery_id,
            'one_key_id': one_key_id,
            'serial_number': serial_number,
            'model': profile.model,
            'manufacturer': profile.manufacturer,
            'platform': profile.platform,
            'nominal_voltage_v': profile.nominal_voltage_v,
            'nominal_capacity_ah': profile.nominal_capacity_ah,
            'chemistry': 'Li-ion',
            'cell_count': profile.cell_count,
            'cell_configuration': f"{profile.cell_count}S1P",
            'manufacture_date': purchase_date - timedelta(days=random.randint(30, 180)),
            'purchase_date': purchase_date,
            'purchase_price': profile.nominal_capacity_ah * random.uniform(25, 45),
            'warranty_months': 36,
            'initial_capacity_ah': profile.nominal_capacity_ah,
            'first_use_date': purchase_date + timedelta(days=random.randint(1, 30)),
            'location': random.choice(['Workshop', 'Garage', 'Job Site', 'Storage']),
            'owner_notes': '',
            'fleet_identifier': f"Fleet_{random.randint(1, 10)}",
            'is_active': True,
            'created_date': datetime.now(),
            'last_updated': datetime.now()
        }

    def _generate_diagnostic_history(self, battery_id: int, battery: Dict[str, Any], 
                                   profile: BatteryProfile) -> Dict[str, List[Dict]]:
        """Generate realistic diagnostic history for a battery"""
        
        # Calculate battery age and usage
        age_days = (datetime.now() - battery['purchase_date']).days
        diagnostic_frequency = max(1, age_days // 30)  # Monthly diagnostics
        
        diagnostics = {
            'sessions': [],
            'health_metrics': [],
            'cell_voltages': [],
            'discharge_histograms': [],
            'raw_register_data': [],
            'parsed_register_values': []
        }
        
        session_id = battery_id * 1000  # Ensure unique session IDs
        
        for i in range(min(diagnostic_frequency, 24)):  # Limit to 24 sessions max
            # Calculate session date
            session_date = battery['first_use_date'] + timedelta(days=i * 30 + random.randint(-5, 5))
            
            if session_date > datetime.now():
                break
            
            # Calculate degradation
            cycles = self._calculate_cycles_at_date(session_date, battery['first_use_date'])
            degradation = self._calculate_degradation(cycles, profile)
            
            # Generate all related data
            session = self._generate_diagnostic_session(session_id, battery_id, session_date)
            health = self._generate_health_metrics(session_id, degradation, cycles)
            cell_voltages = self._generate_cell_voltages(session_id, profile.cell_count, degradation)
            histograms = self._generate_discharge_histograms(session_id, profile.usage_patterns)
            raw_data = self._generate_raw_register_data(session_id, profile, degradation)
            parsed_data = self._generate_parsed_register_values(session_id, raw_data)
            
            diagnostics['sessions'].append(session)
            diagnostics['health_metrics'].append(health)
            diagnostics['cell_voltages'].extend(cell_voltages)
            diagnostics['discharge_histograms'].extend(histograms)
            diagnostics['raw_register_data'].extend(raw_data)
            diagnostics['parsed_register_values'].extend(parsed_data)
            
            session_id += 1
        
        return diagnostics

    def _calculate_cycles_at_date(self, session_date: datetime, first_use_date: datetime) -> int:
        """Calculate accumulated cycles at a given date"""
        days_in_use = (session_date - first_use_date).days
        cycles = int(days_in_use * random.uniform(0.5, 2.0))  # 0.5-2 cycles per day
        return max(0, cycles)

    def _calculate_degradation(self, cycles: int, profile: BatteryProfile) -> Dict[str, float]:
        """Calculate realistic battery degradation"""
        
        # Base degradation from cycles
        cycle_degradation = (cycles / 100) * profile.degradation_rate_base
        total_degradation = min(cycle_degradation + random.uniform(0, 5), 50)
        
        capacity_percentage = max(50, 100 - total_degradation)
        resistance_mohm = 50 * (1 + total_degradation / 50)
        cell_imbalance_mv = min(100, cycles / 50 + random.uniform(0, 20))
        health_score = max(0, min(100, capacity_percentage - resistance_mohm/5 - cell_imbalance_mv/2))
        
        return {
            'capacity_percentage': capacity_percentage,
            'internal_resistance_mohm': resistance_mohm,
            'cell_imbalance_mv': cell_imbalance_mv,
            'health_score': health_score
        }

    def _generate_diagnostic_session(self, session_id: int, battery_id: int, 
                                   session_date: datetime) -> Dict[str, Any]:
        """Generate a diagnostic session record"""
        return {
            'id': session_id,
            'battery_id': battery_id,
            'session_date': session_date,
            'session_type': 'standard',
            'protocol_version': '1.0',
            'firmware_version': f"v{random.randint(1, 3)}.{random.randint(0, 9)}",
            'hardware_interface': 'FTDI_USB',
            'operator': 'automated',
            'session_duration_seconds': random.randint(30, 300),
            'data_completeness_percent': random.uniform(85, 100),
            'communication_errors': 0,
            'success': True,
            'failure_reason': None,
            'environmental_notes': f"Temp: {random.randint(18, 30)}°C",
            'battery_state_before': 'charged',
            'battery_state_after': 'charged',
            'quality_rating': random.randint(3, 5),
            'notes': ''
        }

    def _generate_health_metrics(self, session_id: int, degradation: Dict[str, float], 
                               cycles: int) -> Dict[str, Any]:
        """Generate health metrics for a session"""
        return {
            'id': session_id,
            'session_id': session_id,
            'capacity_percentage': int(degradation['capacity_percentage']),
            'health_score': int(degradation['health_score']),
            'cycle_count': cycles,
            'internal_resistance_mohm': degradation['internal_resistance_mohm'],
            'cell_imbalance_mv': int(degradation['cell_imbalance_mv']),
            'self_discharge_rate_percent': random.uniform(1, 5),
            'charge_efficiency_percent': random.uniform(90, 98),
            'discharge_efficiency_percent': random.uniform(88, 95),
            'temperature_during_test_c': random.uniform(20, 40),
            'voltage_sag_under_load_v': random.uniform(0.5, 2.0),
            'recovery_time_seconds': random.randint(5, 30),
            'power_capability_w': random.uniform(50, 100),
            'energy_density_wh_kg': random.uniform(150, 200),
            'predicted_remaining_cycles': max(0, 1000 - cycles),
            'degradation_rate_percent_per_100cycles': random.uniform(1, 3),
            'thermal_stability_rating': 'good',
            'safety_status': 'safe',
            'warranty_status': 'valid',
            'calculated_date': datetime.now()
        }

    def _generate_cell_voltages(self, session_id: int, cell_count: int, 
                              degradation: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate individual cell voltage data"""
        base_voltage_mv = 3700
        cell_voltages = []
        
        for cell_num in range(1, cell_count + 1):
            voltage_mv = int(base_voltage_mv + random.uniform(-50, 50))
            cell_voltages.append({
                'id': f"{session_id}_{cell_num}",
                'session_id': session_id,
                'cell_number': cell_num,
                'voltage_mv': voltage_mv,
                'voltage_rank': cell_num,
                'deviation_from_average_mv': random.randint(-20, 20),
                'is_lowest_cell': cell_num == cell_count,
                'is_highest_cell': cell_num == 1,
                'historical_consistency': 'stable',
                'degradation_indicator': False
            })
        
        return cell_voltages

    def _generate_discharge_histograms(self, session_id: int, 
                                     usage_patterns: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate discharge histogram data"""
        histograms = []
        
        for usage_type, percentage in usage_patterns.items():
            histograms.append({
                'id': f"{session_id}_{usage_type}",
                'session_id': session_id,
                'current_range_start_a': 0,
                'current_range_end_a': 25,
                'time_spent_seconds': int(3600 * percentage),
                'percentage_of_total_use': percentage * 100,
                'cumulative_energy_wh': random.uniform(10, 100),
                'average_efficiency_percent': random.uniform(85, 95),
                'thermal_impact_rating': 'medium',
                'stress_level': 'moderate',
                'real_world_equivalent': usage_type
            })
        
        return histograms

    def _generate_raw_register_data(self, session_id: int, profile: BatteryProfile, 
                                  degradation: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate raw register data"""
        registers = [
            ('0x04', int(profile.nominal_voltage_v * 1000)),
            ('0x47', int(degradation['capacity_percentage'])),
            ('0x46', int(degradation['internal_resistance_mohm']))
        ]
        
        raw_data = []
        for reg_addr, value in registers:
            raw_data.append({
                'id': f"{session_id}_{reg_addr}",
                'session_id': session_id,
                'register_address': reg_addr,
                'raw_value_hex': f"{value:04X}",
                'raw_value_bytes': value.to_bytes(2, 'big'),
                'timestamp_ms': random.randint(100, 1000),
                'checksum_valid': True,
                'read_attempt': 1,
                'protocol_notes': f'{profile.manufacturer} protocol'
            })
        
        return raw_data

    def _generate_parsed_register_values(self, session_id: int, 
                                       raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """Generate parsed register values from raw data"""
        parsed_data = []
        
        for raw in raw_data:
            parsed_data.append({
                'id': f"{raw['id']}_parsed",
                'session_id': session_id,
                'register_address': raw['register_address'],
                'register_name': f"Register_{raw['register_address']}",
                'parsed_value': int(raw['raw_value_hex'], 16),
                'parsed_value_text': str(int(raw['raw_value_hex'], 16)),
                'units': 'V' if '04' in raw['register_address'] else '%',
                'data_type': 'voltage' if '04' in raw['register_address'] else 'percentage',
                'confidence_level': 'high',
                'parsing_method': 'hex_to_decimal',
                'validation_status': 'validated',
                'notes': 'Auto-parsed'
            })
        
        return parsed_data

    def _insert_fleet_data(self, conn: sqlite3.Connection, fleet_data: Dict[str, List[Dict]]):
        """Insert all fleet data into database"""
        for table_name, records in fleet_data.items():
            if records:
                # Get column names from first record
                columns = list(records[0].keys())
                placeholders = ', '.join(['?' for _ in columns])
                query = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                for record in records:
                    try:
                        conn.execute(query, [record[col] for col in columns])
                    except Exception as e:
                        logger.warning(f"Failed to insert {table_name} record: {e}")

    def _clear_database(self):
        """Clear all existing data from database"""
        with sqlite3.connect(self.database_path) as conn:
            tables = [
                'parsed_register_values', 'raw_register_data', 'discharge_histograms',
                'cell_voltages', 'health_metrics', 'diagnostic_sessions', 'batteries'
            ]
            
            for table in tables:
                try:
                    conn.execute(f"DELETE FROM {table}")
                except Exception:
                    pass  # Table might not exist yet
            
            conn.commit()

# Utility functions for testing
def generate_test_data(database_path: str = "test_battery_diagnostics.db", 
                      fleet_size: int = 25) -> bool:
    """Generate test data for development and testing"""
    generator = MockDataGenerator(database_path)
    return generator.populate_database(fleet_size, clear_existing=True)

if __name__ == "__main__":
    # Generate sample data for testing
    success = generate_test_data()
    print(f"Test data generation: {'Success' if success else 'Failed'}")