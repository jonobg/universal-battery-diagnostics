#!/usr/bin/env python3
"""
Arduino-Based Battery Interface Integration
Integrated from open-battery-information project

Provides hardware communication interface for Arduino-based battery diagnostic
systems with support for OneWire protocols and modular device management.
"""

import serial
import time
import struct
import logging
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ArduinoCommand(Enum):
    """Arduino OBI command codes"""
    VERSION = 0x01
    MAKITA_TEMP_1 = 0x31
    MAKITA_TEMP_2 = 0x32
    MAKITA_GENERAL = 0x33
    ONEWIRE_CC = 0xCC


@dataclass
class ArduinoVersion:
    """Arduino OBI firmware version information"""
    major: int
    minor: int
    patch: int
    
    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


class ArduinoOBIInterface:
    """
    Arduino Open Battery Information Interface
    
    Provides communication with Arduino-based battery diagnostic hardware
    supporting OneWire protocols for various battery types including Makita.
    """
    
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 2.0):
        """Initialize Arduino interface"""
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port: Optional[serial.Serial] = None
        self.logger = logging.getLogger(__name__)
        self.firmware_version: Optional[ArduinoVersion] = None
        
        self._connect()
        self._get_version()
    
    def _connect(self):
        """Establish serial connection to Arduino"""
        try:
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=1
            )
            time.sleep(2)  # Arduino reset delay
            self.logger.info(f"Connected to Arduino OBI on {self.port_name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            raise
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("Disconnected from Arduino OBI")
    
    def _send_command(self, command: ArduinoCommand, data: bytes = b'', 
                     expected_response_len: int = 0) -> bytes:
        """
        Send command to Arduino and receive response
        
        Protocol format:
        TX: [0x01] [data_len] [response_len] [command] [data...]
        RX: [command] [response_len] [data...]
        """
        if not self.serial_port or not self.serial_port.is_open:
            raise ConnectionError("Arduino not connected")
        
        # Construct command packet
        packet = struct.pack('BBBB', 0x01, len(data), expected_response_len, command.value)
        packet += data
        
        # Clear input buffer and send command
        self.serial_port.reset_input_buffer()
        self.serial_port.write(packet)
        self.serial_port.flush()
        
        # Read response header (command + length)
        response_header = self.serial_port.read(2)
        if len(response_header) != 2:
            raise TimeoutError("No response from Arduino")
        
        response_cmd, response_len = struct.unpack('BB', response_header)
        
        # Verify command echo
        if response_cmd != command.value:
            raise ValueError(f"Command mismatch: sent {command.value}, got {response_cmd}")
        
        # Read response data
        response_data = self.serial_port.read(response_len)
        if len(response_data) != response_len:
            raise TimeoutError(f"Incomplete response: expected {response_len}, got {len(response_data)}")
        
        return response_data
    
    def _get_version(self):
        """Get Arduino firmware version"""
        try:
            response = self._send_command(ArduinoCommand.VERSION, expected_response_len=3)
            if len(response) >= 3:
                major, minor, patch = struct.unpack('BBB', response[:3])
                self.firmware_version = ArduinoVersion(major, minor, patch)
                self.logger.info(f"Arduino OBI firmware version: {self.firmware_version}")
        except Exception as e:
            self.logger.warning(f"Failed to get firmware version: {e}")
    
    def get_firmware_version(self) -> Optional[ArduinoVersion]:
        """Get current firmware version"""
        return self.firmware_version
    
    def read_makita_temperature_1(self) -> Optional[Tuple[int, int]]:
        """Read Makita battery temperature using command 0x31"""
        try:
            response = self._send_command(ArduinoCommand.MAKITA_TEMP_1, expected_response_len=2)
            if len(response) >= 2:
                temp1, temp2 = struct.unpack('BB', response[:2])
                return (temp2, temp1)  # Arduino returns in reverse order
        except Exception as e:
            self.logger.error(f"Failed to read Makita temperature 1: {e}")
        return None
    
    def read_makita_temperature_2(self) -> Optional[Tuple[int, int]]:
        """Read Makita battery temperature using command 0x32"""
        try:
            response = self._send_command(ArduinoCommand.MAKITA_TEMP_2, expected_response_len=2)
            if len(response) >= 2:
                temp1, temp2 = struct.unpack('BB', response[:2])
                return (temp2, temp1)  # Arduino returns in reverse order
        except Exception as e:
            self.logger.error(f"Failed to read Makita temperature 2: {e}")
        return None
    
    def makita_command_0x33(self, command_data: bytes, response_length: int) -> Optional[bytes]:
        """Execute Makita battery command 0x33 with custom data"""
        try:
            response = self._send_command(
                ArduinoCommand.MAKITA_GENERAL, 
                command_data, 
                response_length
            )
            return response
        except Exception as e:
            self.logger.error(f"Failed to execute Makita command 0x33: {e}")
        return None
    
    def onewire_command_cc(self, command_data: bytes, response_length: int) -> Optional[bytes]:
        """Execute OneWire command 0xCC with custom data"""
        try:
            response = self._send_command(
                ArduinoCommand.ONEWIRE_CC,
                command_data,
                response_length
            )
            return response
        except Exception as e:
            self.logger.error(f"Failed to execute OneWire command 0xCC: {e}")
        return None
    
    def test_connection(self) -> bool:
        """Test Arduino connection and functionality"""
        try:
            version = self.get_firmware_version()
            if version:
                self.logger.info(f"Arduino connection test passed (v{version})")
                return True
        except Exception as e:
            self.logger.error(f"Arduino connection test failed: {e}")
        return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class BatteryModuleInterface:
    """
    Base interface for modular battery diagnostic components
    
    Inspired by the open-battery-information modular architecture
    """
    
    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def get_display_name(self) -> str:
        """Get human-readable module name"""
        return self.display_name
    
    def initialize(self, arduino_interface: ArduinoOBIInterface) -> bool:
        """Initialize module with Arduino interface"""
        raise NotImplementedError("Subclasses must implement initialize()")
    
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run module-specific diagnostics"""
        raise NotImplementedError("Subclasses must implement run_diagnostics()")
    
    def get_capabilities(self) -> List[str]:
        """Get list of module capabilities"""
        raise NotImplementedError("Subclasses must implement get_capabilities()")


class MakitaBatteryModule(BatteryModuleInterface):
    """Makita battery diagnostics module using Arduino interface"""
    
    def __init__(self):
        super().__init__("makita_arduino", "Makita Battery (Arduino)")
        self.arduino: Optional[ArduinoOBIInterface] = None
    
    def initialize(self, arduino_interface: ArduinoOBIInterface) -> bool:
        """Initialize with Arduino interface"""
        self.arduino = arduino_interface
        return self.arduino.test_connection()
    
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run Makita battery diagnostics via Arduino"""
        if not self.arduino:
            raise RuntimeError("Module not initialized")
        
        results = {
            'module': self.name,
            'timestamp': time.time(),
            'success': False,
            'data': {}
        }
        
        try:
            # Read temperature sensors
            temp1 = self.arduino.read_makita_temperature_1()
            temp2 = self.arduino.read_makita_temperature_2()
            
            results['data'] = {
                'temperature_1': temp1,
                'temperature_2': temp2,
                'firmware_version': str(self.arduino.get_firmware_version())
            }
            results['success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(f"Diagnostics failed: {e}")
        
        return results
    
    def get_capabilities(self) -> List[str]:
        """Get module capabilities"""
        return [
            'temperature_monitoring',
            'onewire_communication',
            'makita_protocol_support',
            'arduino_hardware_interface'
        ]
    
    def read_custom_register(self, register_command: bytes, response_len: int) -> Optional[bytes]:
        """Read custom Makita register via Arduino"""
        if not self.arduino:
            return None
        
        return self.arduino.makita_command_0x33(register_command, response_len)


def discover_arduino_ports() -> List[str]:
    """Discover available Arduino serial ports"""
    import serial.tools.list_ports
    
    arduino_ports = []
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # Look for common Arduino identifiers
        if any(keyword in (port.description or '').lower() for keyword in 
               ['arduino', 'ch340', 'ch341', 'ftdi', 'usb']):
            arduino_ports.append(port.device)
    
    return arduino_ports


def main():
    """CLI interface for Arduino OBI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Arduino Open Battery Information Interface")
    parser.add_argument('--port', type=str, help="Serial port (e.g., COM3)")
    parser.add_argument('--discover', action='store_true', help="Discover Arduino ports")
    parser.add_argument('--test', action='store_true', help="Test connection")
    parser.add_argument('--makita-temp', action='store_true', help="Read Makita temperatures")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.discover:
        ports = discover_arduino_ports()
        print("Discovered Arduino ports:")
        for port in ports:
            print(f"  {port}")
        return
    
    if not args.port:
        print("Port required. Use --discover to find available ports.")
        return 1
    
    try:
        with ArduinoOBIInterface(args.port) as arduino:
            if args.test:
                success = arduino.test_connection()
                print(f"Connection test: {'PASSED' if success else 'FAILED'}")
            
            if args.makita_temp:
                makita = MakitaBatteryModule()
                makita.initialize(arduino)
                results = makita.run_diagnostics()
                print(f"Makita diagnostics: {results}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
