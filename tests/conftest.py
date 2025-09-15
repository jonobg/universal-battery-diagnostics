#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for UBDF testing
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json
import time
from typing import Dict, List, Any

# Import UBDF components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import available UBDF components
from ubdf.hardware.manufacturers.milwaukee import M18Protocol, M18Diagnostics
from ubdf.hardware.manufacturers.makita import NEC78K0Flasher  
from ubdf.hardware import ArduinoOBIInterface


# =================== DATABASE FIXTURES ===================

@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Simple SQLite connection for testing
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS test_results 
                    (id INTEGER PRIMARY KEY, test_name TEXT, result TEXT)""")
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)

@pytest.fixture
def clean_database(test_database):
    """Clean database for each test"""
    with sqlite3.connect(test_database) as conn:
        conn.execute("DELETE FROM test_results")
    return test_database


# =================== MOCK HARDWARE FIXTURES ===================

@pytest.fixture
def mock_serial_interface():
    """Mock serial interface for UART communication"""
    mock_serial = Mock()
    mock_serial.is_open = True
    mock_serial.baudrate = 19200
    mock_serial.timeout = 1.0
    mock_serial.read.return_value = b'\xBB\x04\x15\x0C\xAA'  # Mock Milwaukee response
    mock_serial.write.return_value = 5  # Bytes written
    mock_serial.reset_input_buffer.return_value = None
    mock_serial.reset_output_buffer.return_value = None
    return mock_serial

@pytest.fixture
def milwaukee_mock_data():
    """Realistic Milwaukee M18 mock data"""
    return {
        # Manufacturing info
        4: 8400,    # manufacture_date (days since 2000)
        5: 0x1234,  # serial_number
        6: 0x1809,  # model_code (M18B9)
        
        # Cell voltages (mV)
        12: [3650, 3640, 3655, 3645, 3648],
        
        # Temperature sensors (0.1°C)
        13: [285, 290, 287],
        
        # Usage statistics
        25: 2,      # days_since_last_tool_use
        26: 1,      # days_since_last_charge
        29: 8500,   # total_discharge_ah (mAh)
        30: 145,    # cycle_count
        
        # Health metrics
        70: 25,     # internal_resistance_mohm
        71: 87,     # capacity_remaining_percent
        72: 85,     # health_score
        
        # Discharge histogram (seconds)
        57: 15400,  # 0-25A
        58: 4200,   # 25-50A
        59: 1100,   # 50-75A
        60: 300,    # 75-100A
        61: 150,    # 100-125A
        62: 80,     # 125-150A
        63: 20,     # 150-175A
        64: 10,     # 175-200A
        65: 5,      # >200A
    }

@pytest.fixture
def mock_milwaukee_protocol(milwaukee_mock_data):
    """Mock Milwaukee M18 protocol with realistic data"""
    mock_protocol = Mock(spec=M18Protocol)
    mock_protocol.manufacturer = "Milwaukee"
    mock_protocol.port = "COM3"
    mock_protocol.is_connected = True
    
    # Mock methods
    mock_protocol.connect.return_value = True
    mock_protocol.disconnect.return_value = True
    mock_protocol.get_last_error.return_value = None
    
    # Mock register reading
    def mock_read_register(addr):
        return milwaukee_mock_data.get(addr)
    
    def mock_read_multiple_registers(addresses):
        return {addr: milwaukee_mock_data.get(addr) for addr in addresses 
                if addr in milwaukee_mock_data}
    
    mock_protocol.read_register.side_effect = mock_read_register
    mock_protocol.read_multiple_registers.side_effect = mock_read_multiple_registers
    
    # Mock diagnostics
    def mock_read_diagnostics():
        return {
            'battery_id': "M18_1234_1809",
            'manufacturer': "Milwaukee",
            'model': "M18B9", 
            'timestamp': time.time(),
            'raw_data': b'\x00' * 442,  # 442 bytes of mock data
            'parsed_registers': milwaukee_mock_data,
            'health_metrics': {
                'capacity_percentage': 87,
                'health_score': 85,
                'cycle_count': 145,
                'internal_resistance_mohm': 25,
                'cell_imbalance_mv': 15,
                'milwaukee_health_score': 85
            },
            'communication_stats': {'total_commands': 10, 'successful_commands': 10}
        }
    
    mock_protocol.read_diagnostics.side_effect = mock_read_diagnostics
    return mock_protocol


# =================== CLI TESTING FIXTURES ===================

@pytest.fixture
def temp_workspace():
    """Temporary workspace for CLI testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create required directories
        (workspace / "reports").mkdir()
        (workspace / "configs").mkdir()
        (workspace / "data").mkdir()
        (workspace / "exports").mkdir()
        
        yield workspace

@pytest.fixture
def mock_cli_runner():
    """Click CLI runner for testing commands"""
    from click.testing import CliRunner
    return CliRunner()


# =================== INTEGRATION TEST FIXTURES ===================

@pytest.fixture
def complete_test_setup(clean_database, mock_milwaukee_protocol):
    """Complete setup for integration testing"""
    return {
        'database': clean_database,
        'protocol': mock_milwaukee_protocol,
        'workspace': tempfile.mkdtemp()
    }

@pytest.fixture
def sample_battery_fleet(clean_database):
    """Pre-populated battery fleet for testing"""
    batteries = []
    
    # Add sample test data
    with sqlite3.connect(clean_database) as conn:
        for i in range(5):
            battery_name = f"TEST_BAT_{i:03d}"
            manufacturer = "Milwaukee" if i < 3 else "Makita" 
            model = f"M18B{4+i}" if i < 3 else f"BL186{i}B"
            
            conn.execute("INSERT INTO test_results (test_name, result) VALUES (?, ?)",
                        (f"{battery_name}_{manufacturer}_{model}", "success"))
            batteries.append(f"{battery_name}_{manufacturer}_{model}")
    
    return batteries


# =================== PYTEST CONFIGURATION ===================

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "hardware: tests requiring actual hardware")
    config.addinivalue_line("markers", "slow: slow running tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "cli: CLI interface tests")
    config.addinivalue_line("markers", "database: database-specific tests")
    config.addinivalue_line("markers", "protocol: protocol communication tests")

def pytest_collection_modifyitems(config, items):
    """Automatically skip hardware tests"""
    skip_hardware = pytest.mark.skip(reason="No hardware available")
    
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hardware)