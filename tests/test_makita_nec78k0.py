#!/usr/bin/env python3
"""
Unit Tests for Makita NEC 78K0 Flash Utility Integration
Tests the NEC 78K0 flasher without requiring hardware.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import serial

from ubdf.hardware.manufacturers.makita.nec78k0_flasher import (
    NEC78K0Flasher,
    NEC78K0FlashError
)


class TestNEC78K0Flasher:
    """Test NEC 78K0 flasher functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_serial = Mock(spec=serial.Serial)
        self.mock_serial.is_open = True
        
    @patch('serial.Serial')
    def test_flasher_initialization(self, mock_serial_class):
        """Test flasher initialization"""
        mock_serial_class.return_value = self.mock_serial
        
        flasher = NEC78K0Flasher(port="COM3")
        
        assert flasher.port_name == "COM3"
        assert flasher.baudrate == 9600
        mock_serial_class.assert_called_once()
    
    def test_calculate_checksum(self):
        """Test checksum calculation for flash commands"""
        with patch('serial.Serial'):
            flasher = NEC78K0Flasher(port="COM3")
        
        # Test known data pattern
        test_data = bytes([0x01, 0x02, 0x03, 0x04])
        checksum = flasher.calculate_checksum(test_data)
        
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 0xFF
    
    def test_command_framing(self):
        """Test command frame construction"""
        with patch('serial.Serial'):
            flasher = NEC78K0Flasher(port="COM3")
        
        # Test frame construction
        command = FlashCommand.SILICON_SIGNATURE
        data = b'\x00\x10'  # Address
        frame = flasher.build_command_frame(command, data)
        
        assert len(frame) >= len(data) + 4  # STX + CMD + data + checksum + ETX
        assert frame[0] == 0x01  # STX
        assert frame[1] == command.value
        assert frame[-1] == 0x03  # ETX
    
    @patch('serial.Serial')
    def test_silicon_signature_read(self, mock_serial_class):
        """Test silicon signature reading"""
        mock_serial_class.return_value = self.mock_serial
        
        # Mock successful signature response
        signature_data = b'\x01\x90\x00\x78\x4B\x30\x03'  # Mock signature
        self.mock_serial.read.side_effect = [bytes([b]) for b in signature_data]
        
        flasher = NEC78K0Flasher(port="COM3")
        signature = flasher.read_silicon_signature()
        
        assert signature is not None
        self.mock_serial.write.assert_called()
    
    @patch('serial.Serial')  
    def test_block_verification(self, mock_serial_class):
        """Test memory block verification"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.return_value = b'\x06'  # ACK response
        
        flasher = NEC78K0Flasher(port="COM3")
        
        # Test block verification
        test_data = b'\xFF' * 256  # Empty block
        result = flasher.verify_block(0x1000, test_data)
        
        assert isinstance(result, bool)
    
    @patch('serial.Serial')
    def test_programming_sequence(self, mock_serial_class):
        """Test flash programming sequence"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.return_value = b'\x06'  # ACK response
        
        flasher = NEC78K0Flasher(port="COM3") 
        
        # Test programming with mock data
        test_data = b'\x12\x34\x56\x78' * 64  # 256 bytes
        result = flasher.program_block(0x2000, test_data)
        
        assert isinstance(result, bool)
        self.mock_serial.write.assert_called()
    
    def test_hex_file_parsing(self):
        """Test Intel HEX file parsing"""
        with patch('serial.Serial'):
            flasher = NEC78K0Flasher(port="COM3")
        
        # Mock Intel HEX content
        hex_content = """
:020000020000FC
:10000000010203040506070809101112131415164B
:00000001FF
"""
        
        with patch('builtins.open', mock_open(read_data=hex_content.strip())):
            data = flasher.parse_hex_file("test.hex")
        
        assert isinstance(data, dict)
        assert 0x0000 in data  # Should have address 0x0000
        assert len(data[0x0000]) == 16  # 16 bytes of data
    
    @patch('serial.Serial')
    def test_error_handling(self, mock_serial_class):
        """Test error response handling"""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.read.return_value = b'\x15'  # NAK response
        
        flasher = NEC78K0Flasher(port="COM3")
        
        with pytest.raises(NEC78K0FlashError):
            flasher.read_silicon_signature()
    
    def test_address_validation(self):
        """Test flash address validation"""
        with patch('serial.Serial'):
            flasher = NEC78K0Flasher(port="COM3")
        
        # Test valid addresses
        assert flasher.validate_address(0x1000)
        assert flasher.validate_address(0x7FFF)
        
        # Test invalid addresses  
        assert not flasher.validate_address(0x0000)  # Protected area
        assert not flasher.validate_address(0xFFFF)  # Out of range


class TestNEC78K0Integration:
    """Integration tests for NEC 78K0 system"""
    
    @pytest.mark.hardware
    def test_hardware_integration_placeholder(self):
        """Placeholder for hardware integration tests"""
        pytest.skip("Requires Makita battery and programming hardware")
    
    def test_module_imports(self):
        """Test that NEC 78K0 components can be imported"""
        from ubdf.hardware.manufacturers.makita.nec78k0_flasher import (
            NEC78K0Flasher, NEC78K0FlashError
        )
        
        # Test enum values
        assert FlashCommand.SILICON_SIGNATURE.value == 0x90
        assert FlashResponse.ACK.value == 0x06
        assert FlashResponse.NAK.value == 0x15
    
    def test_cli_functionality(self):
        """Test CLI argument parsing"""
        import sys
        from io import StringIO
        from ubdf.hardware.manufacturers.makita.nec78k0_flasher import main
        
        # Test help output
        with patch.object(sys, 'argv', ['nec78k0_flasher.py', '--help']):
            with patch('sys.stdout', new_callable=StringIO):
                with pytest.raises(SystemExit):
                    main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
