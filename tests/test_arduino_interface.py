#!/usr/bin/env python3
"""
Unit Tests for Arduino OBI Interface Integration
Tests the Arduino-based battery diagnostics interface.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import serial
import struct

from ubdf.hardware.arduino_interface import (
    ArduinoOBIInterface,
    ArduinoCommand,
    ArduinoVersion,
    MakitaBatteryModule,
    BatteryModuleInterface,
    discover_arduino_ports
)


class TestArduinoOBIInterface:
    """Test Arduino OBI interface functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_serial = Mock(spec=serial.Serial)
        self.mock_serial.is_open = True
        
    @patch('serial.Serial')
    @patch('time.sleep')
    def test_arduino_initialization(self, mock_sleep, mock_serial_class):
        """Test Arduino interface initialization"""
        mock_serial_class.return_value = self.mock_serial
        
        # Mock version response
        self.mock_serial.read.side_effect = [
            b'\x01\x03',  # Version command echo + length
            b'\x00\x02\x01'  # Version 0.2.1
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        assert arduino.port_name == "COM4"
        assert arduino.baudrate == 9600
        assert arduino.firmware_version.major == 0
        assert arduino.firmware_version.minor == 2
        assert arduino.firmware_version.patch == 1
    
    def test_version_dataclass(self):
        """Test Arduino version dataclass"""
        version = ArduinoVersion(1, 2, 3)
        assert str(version) == "1.2.3"
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    @patch('serial.Serial')
    def test_command_protocol(self, mock_serial_class):
        """Test Arduino command protocol"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.side_effect = [
            b'\x01\x03',  # Version response header
            b'\x00\x02\x01',  # Version data
            b'\x31\x02',  # Temperature command header  
            b'\x1A\x1B'  # Temperature data
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        # Test temperature reading
        temp_result = arduino.read_makita_temperature_1()
        
        assert temp_result is not None
        assert len(temp_result) == 2
        assert isinstance(temp_result[0], int)
        assert isinstance(temp_result[1], int)
    
    @patch('serial.Serial')
    def test_makita_commands(self, mock_serial_class):
        """Test Makita-specific commands"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.side_effect = [
            b'\x01\x03', b'\x00\x02\x01',  # Version
            b'\x33\x04', b'\x12\x34\x56\x78'  # Makita 0x33 command
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        # Test custom Makita command
        result = arduino.makita_command_0x33(b'\x01\x02', 4)
        
        assert result == b'\x12\x34\x56\x78'
    
    @patch('serial.Serial')
    def test_onewire_commands(self, mock_serial_class):
        """Test OneWire protocol commands"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.side_effect = [
            b'\x01\x03', b'\x00\x02\x01',  # Version
            b'\xCC\x02', b'\xAB\xCD'  # OneWire response
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        # Test OneWire command
        result = arduino.onewire_command_cc(b'\x99', 2)
        
        assert result == b'\xAB\xCD'
    
    @patch('serial.Serial')
    def test_connection_test(self, mock_serial_class):
        """Test Arduino connection validation"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.side_effect = [
            b'\x01\x03', b'\x00\x02\x01'  # Version response
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        assert arduino.test_connection() is True
        assert arduino.firmware_version is not None
    
    @patch('serial.Serial')
    def test_error_handling(self, mock_serial_class):
        """Test error response handling"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.side_effect = [
            b'\x01\x03', b'\x00\x02\x01',  # Version OK
            b'',  # Empty response for temperature
        ]
        
        arduino = ArduinoOBIInterface(port="COM4")
        
        # Should handle timeout gracefully
        result = arduino.read_makita_temperature_1()
        assert result is None


class TestMakitaBatteryModule:
    """Test Makita battery module functionality"""
    
    def setup_method(self):
        """Setup module test fixtures"""
        self.mock_arduino = Mock(spec=ArduinoOBIInterface)
        self.module = MakitaBatteryModule()
    
    def test_module_initialization(self):
        """Test module initialization"""
        assert self.module.name == "makita_arduino"
        assert self.module.display_name == "Makita Battery (Arduino)"
        
        # Test initialization with Arduino
        self.mock_arduino.test_connection.return_value = True
        result = self.module.initialize(self.mock_arduino)
        
        assert result is True
        assert self.module.arduino == self.mock_arduino
    
    def test_capabilities(self):
        """Test module capabilities"""
        capabilities = self.module.get_capabilities()
        
        assert 'temperature_monitoring' in capabilities
        assert 'onewire_communication' in capabilities
        assert 'makita_protocol_support' in capabilities
        assert 'arduino_hardware_interface' in capabilities
    
    def test_diagnostics_execution(self):
        """Test diagnostic execution"""
        self.mock_arduino.test_connection.return_value = True
        self.mock_arduino.read_makita_temperature_1.return_value = (25, 26)
        self.mock_arduino.read_makita_temperature_2.return_value = (24, 27)
        self.mock_arduino.get_firmware_version.return_value = ArduinoVersion(0, 2, 1)
        
        self.module.initialize(self.mock_arduino)
        results = self.module.run_diagnostics()
        
        assert results['success'] is True
        assert 'temperature_1' in results['data']
        assert 'temperature_2' in results['data']
        assert 'firmware_version' in results['data']
        assert results['data']['temperature_1'] == (25, 26)
    
    def test_custom_register_reading(self):
        """Test custom register reading capability"""
        self.mock_arduino.makita_command_0x33.return_value = b'\x12\x34'
        
        self.module.initialize(self.mock_arduino)
        result = self.module.read_custom_register(b'\x01\x02', 2)
        
        assert result == b'\x12\x34'
        self.mock_arduino.makita_command_0x33.assert_called_with(b'\x01\x02', 2)


class TestBatteryModuleInterface:
    """Test base battery module interface"""
    
    def test_abstract_interface(self):
        """Test that base interface enforces implementation"""
        
        class TestModule(BatteryModuleInterface):
            def __init__(self):
                super().__init__("test", "Test Module")
        
        module = TestModule()
        
        # Should raise NotImplementedError for abstract methods
        with pytest.raises(NotImplementedError):
            module.initialize(None)
        
        with pytest.raises(NotImplementedError):
            module.run_diagnostics()
        
        with pytest.raises(NotImplementedError):
            module.get_capabilities()


class TestArduinoDiscovery:
    """Test Arduino port discovery"""
    
    @patch('serial.tools.list_ports.comports')
    def test_port_discovery(self, mock_comports):
        """Test Arduino port discovery"""
        # Mock available ports
        mock_port1 = Mock()
        mock_port1.device = "COM3"
        mock_port1.description = "Arduino Uno"
        
        mock_port2 = Mock()
        mock_port2.device = "COM4"  
        mock_port2.description = "USB Serial Device"
        
        mock_port3 = Mock()
        mock_port3.device = "COM5"
        mock_port3.description = "Standard Serial Port"
        
        mock_comports.return_value = [mock_port1, mock_port2, mock_port3]
        
        discovered_ports = discover_arduino_ports()
        
        # Should find Arduino and USB ports
        assert "COM3" in discovered_ports  # Arduino Uno
        assert "COM4" in discovered_ports  # USB Serial
        assert "COM5" not in discovered_ports  # Standard serial excluded


class TestArduinoIntegration:
    """Integration tests for Arduino system"""
    
    @pytest.mark.hardware
    def test_hardware_integration_placeholder(self):
        """Placeholder for hardware integration tests"""
        pytest.skip("Requires Arduino OBI hardware")
    
    def test_module_imports(self):
        """Test that Arduino components can be imported"""
        from ubdf.hardware.arduino_interface import (
            ArduinoOBIInterface, ArduinoCommand, ArduinoVersion,
            MakitaBatteryModule, discover_arduino_ports
        )
        
        # Test enum values
        assert ArduinoCommand.VERSION.value == 0x01
        assert ArduinoCommand.MAKITA_TEMP_1.value == 0x31
        assert ArduinoCommand.ONEWIRE_CC.value == 0xCC
    
    def test_cli_functionality(self):
        """Test CLI argument parsing"""
        import sys
        from io import StringIO
        from ubdf.hardware.arduino_interface import main
        
        # Test discovery function
        with patch.object(sys, 'argv', ['arduino_interface.py', '--discover']):
            with patch('ubdf.hardware.arduino_interface.discover_arduino_ports', 
                      return_value=['COM3', 'COM4']):
                result = main()
                assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
