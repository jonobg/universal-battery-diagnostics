#!/usr/bin/env python3
"""
Unit Tests for Milwaukee M18 Battery Integration
Tests the comprehensive M18 protocol implementation without requiring hardware.
"""

import pytest
import struct
import datetime
from unittest.mock import Mock, patch, MagicMock
import serial

from ubdf.hardware.manufacturers.milwaukee import (
    M18Protocol,
    M18ProtocolError,
    M18RegisterMap,
    RegisterType,
    M18Diagnostics,
    BatteryIdentification,
    VoltageMetrics,
    TemperatureMetrics
)


class TestM18Protocol:
    """Test M18 protocol core functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_serial = Mock(spec=serial.Serial)
        self.mock_serial.is_open = True
        
    @patch('serial.Serial')
    def test_protocol_initialization(self, mock_serial_class):
        """Test M18Protocol initialization"""
        mock_serial_class.return_value = self.mock_serial
        
        protocol = M18Protocol(port="COM5")
        
        assert protocol.port_name == "COM5"
        assert protocol.baudrate == 4800
        assert protocol.timeout == 0.8
        mock_serial_class.assert_called_once()
    
    def test_reverse_bits(self):
        """Test bit reversal for M18 protocol"""
        with patch('serial.Serial'):
            protocol = M18Protocol(port="COM5")
            
        # Test known bit patterns
        assert protocol.reverse_bits(0xAA) == 0x55  # 10101010 -> 01010101
        assert protocol.reverse_bits(0x01) == 0x80  # 00000001 -> 10000000
        assert protocol.reverse_bits(0xFF) == 0xFF  # 11111111 -> 11111111
    
    def test_checksum_calculation(self):
        """Test M18 protocol checksum"""
        with patch('serial.Serial'):
            protocol = M18Protocol(port="COM5")
        
        test_data = b'\x60\x04\x08'
        checksum = protocol.checksum(test_data)
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 0xFFFF
    
    def test_add_checksum(self):
        """Test checksum addition to commands"""
        with patch('serial.Serial'):
            protocol = M18Protocol(port="COM5")
        
        command = b'\x60\x04\x08'
        with_checksum = protocol.add_checksum(command)
        
        assert len(with_checksum) == len(command) + 2
        assert with_checksum[:len(command)] == command
    
    @patch('serial.Serial')
    def test_reset_sequence(self, mock_serial_class):
        """Test battery reset sequence"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.return_value = bytes([0xAA])
        
        protocol = M18Protocol(port="COM5")
        result = protocol.reset()
        
        assert result is True
        self.mock_serial.write.assert_called()
    
    @patch('serial.Serial')
    def test_connection_context_manager(self, mock_serial_class):
        """Test context manager functionality"""
        mock_serial_class.return_value = self.mock_serial
        
        with M18Protocol(port="COM5") as protocol:
            assert protocol.port == self.mock_serial
        
        self.mock_serial.close.assert_called_once()


class TestM18RegisterMap:
    """Test M18 register mapping and data handling"""
    
    def test_register_definitions(self):
        """Test register definition structure"""
        # Test known registers exist
        assert 0 in M18RegisterMap.REGISTERS  # Manufacturing date
        assert 12 in M18RegisterMap.REGISTERS  # Cell voltages
        assert 29 in M18RegisterMap.REGISTERS  # Total discharge
        
        # Test register properties
        voltage_reg = M18RegisterMap.get_register_definition(12)
        assert voltage_reg.name == "cell_voltages"
        assert voltage_reg.data_type == RegisterType.VOLTAGE_ARRAY
        assert voltage_reg.length == 10
    
    def test_battery_type_lookup(self):
        """Test battery type identification"""
        # Test known battery types
        known_types = ["37", "40", "107", "384"]
        for battery_type in known_types:
            assert battery_type in M18RegisterMap.BATTERY_TYPES
        
        # Test type decoding
        capacity, description, serial = M18RegisterMap.decode_battery_type("Type 107 Serial 123456")
        assert capacity == 8
        assert "8Ah HO" in description
        assert serial == "123456"
    
    def test_voltage_array_decoding(self):
        """Test cell voltage array decoding"""
        # Mock 5 cells at 3.7V each (3700mV)
        mock_data = struct.pack('<5H', 3700, 3702, 3698, 3701, 3699)
        
        voltages = M18RegisterMap.decode_voltage_array(mock_data)
        
        assert len(voltages) == 5
        assert all(3690 <= v <= 3710 for v in voltages)
        assert voltages == [3700, 3702, 3698, 3701, 3699]
    
    def test_temperature_decoding(self):
        """Test temperature sensor decoding"""
        # Test ADC temperature (register 13)
        adc_data = struct.pack('<H', 1250)  # Should be 25.0°C
        temp = M18RegisterMap.decode_temperature(adc_data, 13)
        assert temp == 25.0
        
        # Test Forge temperature (register 18)
        forge_data = struct.pack('<H', 42)
        temp = M18RegisterMap.decode_temperature(forge_data, 18)
        assert temp == 42.0
        
        # Test invalid data
        invalid_data = struct.pack('<H', 0)
        temp = M18RegisterMap.decode_temperature(invalid_data, 13)
        assert temp is None
    
    def test_date_decoding(self):
        """Test date/timestamp decoding"""
        # Test valid timestamp
        timestamp = int(datetime.datetime(2023, 9, 15, 12, 0).timestamp())
        date_data = struct.pack('<I', timestamp)
        
        decoded_date = M18RegisterMap.decode_date(date_data)
        assert decoded_date is not None
        assert decoded_date.year == 2023
        assert decoded_date.month == 9
    
    def test_discharge_cycles_calculation(self):
        """Test discharge cycle calculation"""
        # 8Ah battery with 28800 A-s discharge (1 full cycle)
        cycles = M18RegisterMap.calculate_discharge_cycles(28800, 8)
        assert cycles == 1.0
        
        # Partial cycle
        cycles = M18RegisterMap.calculate_discharge_cycles(14400, 8)  
        assert cycles == 0.5


class TestM18Diagnostics:
    """Test M18 diagnostics and reporting"""
    
    def setup_method(self):
        """Setup diagnostic test fixtures"""
        self.mock_protocol = Mock(spec=M18Protocol)
        self.diagnostics = M18Diagnostics(self.mock_protocol)
    
    def test_diagnostics_initialization(self):
        """Test diagnostics initialization"""
        assert self.diagnostics.protocol == self.mock_protocol
        assert hasattr(self.diagnostics, 'health_thresholds')
        assert 'cell_imbalance_warning' in self.diagnostics.health_thresholds
    
    def test_battery_identification_extraction(self):
        """Test battery identification data extraction"""
        mock_data = {
            2: "Type 107 Serial 123456",  # Type and serial
            0: datetime.datetime(2023, 1, 15),  # Manufacturing date
            1: 45  # Days since first charge
        }
        
        identification = self.diagnostics.get_battery_identification(mock_data)
        
        assert identification.battery_type == "107"
        assert identification.electronic_serial == "123456"
        assert identification.capacity_ah == 8
        assert "8Ah HO" in identification.description
        assert identification.manufacture_date.year == 2023
        assert identification.days_since_first_charge == 45
    
    def test_voltage_metrics_calculation(self):
        """Test voltage metrics calculation"""
        mock_data = {
            12: [3700, 3702, 3698, 3701, 3699]  # Cell voltages in mV
        }
        
        voltage_metrics = self.diagnostics.get_voltage_metrics(mock_data)
        
        assert voltage_metrics.pack_voltage == pytest.approx(18.5, rel=1e-2)
        assert voltage_metrics.cell_imbalance == 4  # 3702 - 3698
        assert voltage_metrics.min_cell_voltage == 3698
        assert voltage_metrics.max_cell_voltage == 3702
    
    def test_health_metrics_calculation(self):
        """Test health scoring and warnings"""
        mock_register_data = {
            40: 2,   # Overheat events
            41: 1,   # Overcurrent events  
            42: 5,   # Low voltage events
            43: 0    # Low voltage bounce
        }
        
        mock_voltage_metrics = VoltageMetrics(
            pack_voltage=18.5,
            cell_voltages=[3700, 3702, 3698, 3701, 3699],
            cell_imbalance=4,
            min_cell_voltage=3698,
            max_cell_voltage=3702
        )
        
        # Mock usage stats
        from ubdf.hardware.manufacturers.milwaukee.m18_diagnostics import UsageStatistics
        mock_usage_stats = UsageStatistics(
            total_discharge_ah=100.0,
            total_discharge_cycles=12.5,
            discharge_to_empty_count=3,
            days_since_tool_use=5,
            total_tool_time=3600,
            discharge_time_buckets={}
        )
        
        health_metrics = self.diagnostics.get_health_metrics(
            mock_register_data, mock_voltage_metrics, mock_usage_stats
        )
        
        assert health_metrics.overheat_events == 2
        assert health_metrics.overcurrent_events == 1
        assert health_metrics.low_voltage_events == 5
        assert 0 <= health_metrics.health_score <= 100
        
        # Should have warnings for low voltage events
        assert any("voltage" in warning.lower() for warning in health_metrics.warnings)
    
    def test_register_data_reading_mock(self):
        """Test register data reading with mocked responses"""
        # Mock protocol responses
        mock_responses = {
            2: b'Type 107 Serial 123456\x00\x00',  # Type/serial
            12: struct.pack('<5H', 3700, 3702, 3698, 3701, 3699),  # Voltages
            29: struct.pack('<I', 28800),  # Total discharge
        }
        
        def mock_read_register(addr_h, addr_l, length):
            reg_id = (addr_h << 8) | addr_l
            if reg_id in mock_responses:
                # Simulate protocol response with header + data + checksum
                data = mock_responses[reg_id]
                return b'\x01\x04' + bytes([length]) + data + b'\x00\x00'
            return b'\x01\x04\x00\x00\x00'
        
        self.mock_protocol.read_register.side_effect = mock_read_register
        self.mock_protocol.save_and_set_debug = Mock()
        self.mock_protocol.restore_debug = Mock()
        
        register_data = self.diagnostics.read_register_data([2, 12, 29])
        
        assert 2 in register_data
        assert 12 in register_data  
        assert 29 in register_data


class TestM18Integration:
    """Integration tests for M18 system"""
    
    @pytest.mark.hardware
    def test_hardware_integration_placeholder(self):
        """Placeholder for hardware integration tests"""
        # This test requires actual hardware and should be run manually
        # Mark with @pytest.mark.hardware to skip in CI
        pytest.skip("Requires M18 battery hardware")
    
    def test_package_imports(self):
        """Test that all M18 components can be imported"""
        from ubdf.hardware.manufacturers.milwaukee import (
            M18Protocol, M18RegisterMap, M18Diagnostics,
            create_m18_diagnostics, quick_health_check, supported_battery_types
        )
        
        # Test package info
        from ubdf.hardware.manufacturers.milwaukee import get_package_info
        info = get_package_info()
        
        assert info['name'] == 'Milwaukee M18 Diagnostics'
        assert 'registers_mapped' in info
        assert info['registers_mapped'] > 0
    
    def test_register_constants(self):
        """Test exported register constants"""
        from ubdf.hardware.manufacturers.milwaukee import (
            ESSENTIAL_REGISTERS, COMPREHENSIVE_REGISTERS, DISCHARGE_BUCKETS
        )
        
        assert isinstance(ESSENTIAL_REGISTERS, list)
        assert isinstance(COMPREHENSIVE_REGISTERS, list) 
        assert isinstance(DISCHARGE_BUCKETS, list)
        assert len(DISCHARGE_BUCKETS) == 20  # 44-63 discharge buckets


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_milwaukee_m18.py -v
    pytest.main([__file__, "-v"])
