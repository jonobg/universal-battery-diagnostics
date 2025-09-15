#!/usr/bin/env python3
"""
Unit tests for Milwaukee M18 protocol implementation
"""

import pytest
from unittest.mock import Mock, patch
import time

from ubdf.hardware.manufacturers.milwaukee.m18_protocol import MilwaukeeM18Protocol
from ubdf.hardware.base.protocol_interface import ProtocolType, BatteryState


class TestMilwaukeeM18Protocol:
    """Test Milwaukee M18 protocol functionality"""
    
    def test_protocol_properties(self):
        """Test basic protocol properties"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        assert protocol.protocol_type == ProtocolType.UART_CUSTOM
        assert protocol.manufacturer == "Milwaukee"
        assert "M18B9" in protocol.supported_models
        assert "M12B4" in protocol.supported_models
    
    def test_register_map_structure(self):
        """Test register map contains expected registers"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        reg_map = protocol.get_register_map()
        
        # Check essential registers exist
        essential_registers = [4, 5, 6, 12, 13, 25, 26, 29, 30, 70, 71]
        for reg_addr in essential_registers:
            assert reg_addr in reg_map
            assert reg_map[reg_addr].name is not None
            assert reg_map[reg_addr].description is not None
    
    def test_register_definitions(self):
        """Test specific register definitions"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        reg_map = protocol.get_register_map()
        
        # Test cell voltages register (array type)
        cell_reg = reg_map[12]
        assert cell_reg.name == "cell_voltages"
        assert cell_reg.data_type == "array"
        assert cell_reg.array_length == 5
        assert cell_reg.unit == "mV"
        
        # Test capacity register
        capacity_reg = reg_map[71]
        assert capacity_reg.name == "capacity_remaining"
        assert capacity_reg.data_type == "uint8"
        assert capacity_reg.unit == "%"
    
    @patch('serial.Serial')
    def test_connection_success(self, mock_serial_class, mock_serial_interface):
        """Test successful connection to battery"""
        mock_serial_class.return_value = mock_serial_interface
        
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        with patch.object(protocol, '_initialize_communication', return_value=True):
            result = protocol.connect()
            
        assert result is True
        assert protocol.state == BatteryState.CONNECTED
        mock_serial_class.assert_called_once()
    
    @patch('serial.Serial')
    def test_connection_failure(self, mock_serial_class):
        """Test connection failure handling"""
        mock_serial_class.side_effect = Exception("Port not found")
        
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        result = protocol.connect()
        
        assert result is False
        assert protocol.get_last_error() is not None
        assert "Connection failed" in protocol.get_last_error()
    
    def test_command_building(self):
        """Test Milwaukee command packet construction"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        # Test read command for register 71 (capacity)
        cmd = protocol._build_read_command(71)
        
        assert len(cmd) == 5  # START + READ_CMD + ADDR_HIGH + ADDR_LOW + CHECKSUM
        assert cmd[0] == 0xAA  # Start byte
        assert cmd[1] == 0x01  # Read command
        assert cmd[2] == 0x00  # Address high byte (71 = 0x0047)
        assert cmd[3] == 0x47  # Address low byte
        
        # Verify checksum
        expected_checksum = 0xAA ^ 0x01 ^ 0x00 ^ 0x47
        assert cmd[4] == expected_checksum
    
    def test_response_parsing_single_value(self):
        """Test parsing single register response"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        # Mock response for capacity register (87%)
        response = bytes([0xBB, 0x47, 0x00, 0x57, 0x1F])  # 0x0057 = 87
        
        result = protocol._parse_register_response(71, response)
        assert result == 87
    
    def test_response_parsing_array_value(self):
        """Test parsing array register response (cell voltages)"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        # Mock response for cell voltages: [3650, 3640, 3655, 3645, 3648] mV
        response = bytes([
            0xBB, 0x0C,  # Start + register address
            0x0E, 0x42,  # 3650 mV (0x0E42)
            0x0E, 0x38,  # 3640 mV (0x0E38)
            0x0E, 0x47,  # 3655 mV (0x0E47)
            0x0E, 0x3D,  # 3645 mV (0x0E3D)
            0x0E, 0x40,  # 3648 mV (0x0E40)
            0x00         # Checksum (simplified)
        ])
        
        result = protocol._parse_register_response(12, response)
        assert isinstance(result, list)
        assert len(result) == 5
        assert result[0] == 3650
        assert result[4] == 3648
    
    def test_health_metrics_calculation(self):
        """Test Milwaukee-specific health metrics calculation"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        mock_registers = {
            71: 87,  # capacity_percentage
            70: 25,  # internal_resistance_mohm
            30: 145, # cycle_count
            12: [3650, 3640, 3655, 3645, 3648],  # cell_voltages
            13: [285, 290, 287]  # temperatures
        }
        
        health_metrics = protocol._calculate_health_metrics(mock_registers)
        
        assert 'milwaukee_health_score' in health_metrics
        assert 'cell_imbalance_mv' in health_metrics
        assert 'average_temperature_c' in health_metrics
        
        # Check cell imbalance calculation
        expected_imbalance = 3655 - 3640  # 15 mV
        assert health_metrics['cell_imbalance_mv'] == expected_imbalance
        
        # Check temperature conversion
        expected_avg_temp = (285 + 290 + 287) / 3 / 10  # 28.73°C
        assert abs(health_metrics['average_temperature_c'] - expected_avg_temp) < 0.1
    
    def test_battery_id_generation(self):
        """Test battery ID generation from registers"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        mock_registers = {
            5: 0x1234,  # serial_number
            6: 0x1809   # model_code
        }
        
        battery_id = protocol._generate_battery_id(mock_registers)
        assert battery_id == "M18_1234_1809"
    
    def test_model_detection(self):
        """Test battery model detection from registers"""
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
        
        # Test M18B9 detection
        mock_registers = {'6': 0x1809}
        model = protocol._detect_model(mock_registers)
        assert model == "M18B9"
        
        # Test unknown model
        mock_registers = {'6': 0x9999}
        model = protocol._detect_model(mock_registers)
        assert "Unknown_M18_9999" in model


@pytest.mark.integration
class TestMilwaukeeIntegration:
    """Integration tests with mock hardware"""
    
    def test_full_diagnostic_workflow(self, mock_milwaukee_protocol):
        """Test complete diagnostic workflow"""
        protocol = mock_milwaukee_protocol
        
        # Test connection
        assert protocol.connect()
        assert protocol.is_connected()
        
        # Test diagnostics
        diagnostics = protocol.read_diagnostics()
        assert diagnostics is not None
        assert diagnostics.manufacturer == "Milwaukee"
        assert diagnostics.model == "M18B9"
        assert diagnostics.battery_id == "M18_1234_1809"
        
        # Test health metrics
        health = diagnostics.health_metrics
        assert health['capacity_percentage'] == 87
        assert health['cycle_count'] == 145
        
        # Test parsed registers
        registers = diagnostics.parsed_registers
        assert 71 in registers  # capacity register
        assert 30 in registers  # cycle count register
        
        # Test disconnection
        assert protocol.disconnect()
    
    def test_communication_error_handling(self, mock_milwaukee_protocol):
        """Test error handling during communication"""
        protocol = mock_milwaukee_protocol
        
        # Simulate communication failure
        protocol.read_register.side_effect = Exception("Communication timeout")
        
        # Should handle gracefully
        result = protocol.read_register(71)
        assert result is None
        
        # Error should be recorded
        assert protocol.get_last_error() is not None
    
    def test_register_value_parsing(self, mock_milwaukee_protocol):
        """Test register value parsing with different data types"""
        protocol = mock_milwaukee_protocol
        reg_map = protocol.get_register_map()
        
        # Test uint16 parsing
        uint16_reg = reg_map[30]  # cycle_count
        parsed = protocol._parse_register_value(145, uint16_reg)
        assert parsed == 145
        
        # Test percentage conversion
        pct_reg = reg_map[71]  # capacity_remaining
        parsed = protocol._parse_register_value(87, pct_reg)
        assert parsed == 87
        
        # Test array parsing
        array_reg = reg_map[12]  # cell_voltages
        cell_data = [3650, 3640, 3655, 3645, 3648]
        parsed = protocol._parse_register_value(cell_data, array_reg)
        assert parsed == cell_data


@pytest.mark.hardware 
class TestMilwaukeeHardware:
    """Hardware tests requiring actual Milwaukee battery"""
    
    def test_real_milwaukee_connection(self):
        """Test connection to actual Milwaukee battery"""
        # Skip if no hardware available
        pytest.skip("Requires actual Milwaukee M18 battery and UART adapter")
        
        protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")  # Adjust port
        
        try:
            assert protocol.connect()
            diagnostics = protocol.read_diagnostics()
            assert diagnostics is not None
            
            # Validate real data ranges
            health = diagnostics.health_metrics
            assert 0 <= health.get('capacity_percentage', 50) <= 100
            assert health.get('cycle_count', 0) >= 0
            
        finally:
            protocol.disconnect()