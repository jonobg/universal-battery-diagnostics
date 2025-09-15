#!/usr/bin/env python3
"""
Milwaukee M18 Protocol Core Communication Interface
Integrated from mnh-jansson/m18-protocol

This module provides low-level M18 battery communication capabilities
including charger simulation, register access, and diagnostics.
"""

import serial
from serial.tools import list_ports
import time
import struct
import datetime
import logging
from typing import Optional, List, Dict, Union, Tuple
import requests


class M18ProtocolError(Exception):
    """Custom exception for M18 protocol operations"""
    pass


class M18Protocol:
    """
    Milwaukee M18 Battery Communication Protocol
    
    Provides functionality to:
    - Simulate charger communication
    - Read battery registers and diagnostics
    - Monitor battery health and usage statistics
    - Access detailed battery analytics
    """
    
    # Protocol constants
    SYNC_BYTE = 0xAA
    CAL_CMD = 0x55
    CONF_CMD = 0x60
    SNAP_CMD = 0x61
    KEEPALIVE_CMD = 0x62
    
    CUTOFF_CURRENT = 300
    MAX_CURRENT = 6000
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 4800, timeout: float = 0.8):
        """Initialize M18 protocol interface"""
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.port: Optional[serial.Serial] = None
        self.acc = 4
        
        self.print_tx = False
        self.print_rx = False
        self.print_tx_save = False
        self.print_rx_save = False
        
        self.logger = logging.getLogger(__name__)
        
        if port is None:
            self.port_name = self._select_port_interactive()
        
        self._connect()
    
    def _select_port_interactive(self) -> str:
        """Interactive port selection if none specified"""
        print("*** NO PORT SPECIFIED ***")
        print("Available serial ports (choose one that says USB somewhere):")
        ports = list_ports.comports()
        
        for i, p in enumerate(ports, 1):
            print(f"  {i}: {p.device} - {p.manufacturer} - {p.description}")
        
        while True:
            try:
                user_input = input(f"Choose a port (1-{len(ports)}): ")
                port_id = int(user_input)
                if 1 <= port_id <= len(ports):
                    selected_port = ports[port_id - 1]
                    print(f"Selected: \"{selected_port.device} - {selected_port.manufacturer}\"")
                    print(f"Future usage: --port {selected_port.device}")
                    input("Press Enter to continue...")
                    return selected_port.device
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")
    
    def _connect(self) -> bool:
        """Establish serial connection"""
        try:
            self.port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout,
                stopbits=2
            )
            self.idle()
            self.logger.info(f"Connected to M18 battery on {self.port_name}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise M18ProtocolError(f"Failed to connect to {self.port_name}: {e}")
    
    def disconnect(self):
        """Close serial connection"""
        if self.port and self.port.is_open:
            self.idle()
            self.port.close()
            self.logger.info("Disconnected from M18 battery")
    
    def set_debug_printing(self, enable: bool = True):
        """Enable/disable TX/RX debug printing"""
        self.print_tx = enable
        self.print_rx = enable
    
    def save_and_set_debug(self, enable: bool = True):
        """Save current debug state and set new state"""
        self.print_tx_save = self.print_tx
        self.print_rx_save = self.print_rx
        self.set_debug_printing(enable)
    
    def restore_debug(self):
        """Restore previously saved debug state"""
        self.print_tx = self.print_tx_save
        self.print_rx = self.print_rx_save
    
    def reverse_bits(self, byte: int) -> int:
        """Reverse bit order in byte for M18 protocol"""
        return int(f"{byte:08b}"[::-1], 2)
    
    def checksum(self, payload: bytes) -> int:
        """Calculate M18 protocol checksum"""
        checksum = 0
        for byte in payload:
            checksum += byte & 0xFFFF
        return checksum
    
    def add_checksum(self, command: bytes) -> bytes:
        """Add checksum to command"""
        command += struct.pack(">H", self.checksum(command))
        return command
    
    def send(self, command: bytes):
        """Send raw command to M18 battery"""
        self.port.reset_input_buffer()
        debug_print = " ".join(f"{byte:02X}" for byte in command)
        
        # Convert to MSB format for transmission
        msb_command = bytearray(self.reverse_bits(byte) for byte in command)
        
        if self.print_tx:
            print(f"Sending:  {debug_print}")
        
        self.port.write(msb_command)
    
    def send_command(self, command: bytes):
        """Send command with checksum"""
        self.send(self.add_checksum(command))
    
    def read_response(self, expected_size: int) -> bytearray:
        """Read and decode response from M18 battery"""
        msb_response = self.port.read(1)
        if not msb_response or len(msb_response) < 1:
            raise M18ProtocolError("Empty response from battery")
        
        # Handle variable response length
        if self.reverse_bits(msb_response[0]) == 0x82:
            msb_response += self.port.read(1)
        else:
            msb_response += self.port.read(expected_size - 1)
        
        # Convert from MSB to LSB
        lsb_response = bytearray(self.reverse_bits(byte) for byte in msb_response)
        
        debug_print = " ".join(f"{byte:02X}" for byte in lsb_response)
        if self.print_rx:
            print(f"Received: {debug_print}")
        
        return lsb_response
    
    def reset(self) -> bool:
        """
        Reset M18 battery and establish communication
        
        Returns:
            bool: True if battery responds correctly
        """
        self.acc = 4
        
        # Toggle break condition and DTR for reset
        self.port.break_condition = True
        self.port.dtr = True
        time.sleep(0.3)
        self.port.break_condition = False
        self.port.dtr = False
        time.sleep(0.3)
        
        # Send sync byte
        self.send(struct.pack('>B', self.SYNC_BYTE))
        
        try:
            response = self.read_response(1)
            time.sleep(0.01)
            
            if response and response[0] == self.SYNC_BYTE:
                return True
            else:
                self.logger.warning(f"Unexpected sync response: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            return False
    
    def update_acc(self):
        """Update accumulator value for command sequencing"""
        acc_values = [0x04, 0x0C, 0x1C]
        current_index = acc_values.index(self.acc)
        next_index = (current_index + 1) % len(acc_values)
        self.acc = acc_values[next_index]
    
    def configure(self, state: int) -> bytearray:
        """Send configuration command to battery"""
        self.acc = 4
        command = struct.pack('>BBBHHHBB', 
                            self.CONF_CMD, self.acc, 8,
                            self.CUTOFF_CURRENT, self.MAX_CURRENT, self.MAX_CURRENT, 
                            state, 13)
        self.send_command(command)
        return self.read_response(5)
    
    def get_snapchat(self) -> bytearray:
        """Request snapshot data from battery"""
        command = struct.pack('>BBB', self.SNAP_CMD, self.acc, 0)
        self.send_command(command)
        self.update_acc()
        return self.read_response(8)
    
    def keepalive(self) -> bytearray:
        """Send keepalive/charging current request"""
        command = struct.pack('>BBB', self.KEEPALIVE_CMD, self.acc, 0)
        self.send_command(command)
        return self.read_response(9)
    
    def calibrate(self) -> bytearray:
        """Send calibration command"""
        command = struct.pack('>BBB', self.CAL_CMD, self.acc, 0)
        self.send_command(command)
        self.update_acc()
        return self.read_response(8)
    
    def read_register(self, addr_high: int, addr_low: int, length: int, 
                     command: int = 0x01) -> bytearray:
        """
        Read data from battery register
        
        Args:
            addr_high: High byte of register address
            addr_low: Low byte of register address  
            length: Number of bytes to read
            command: Command byte (default 0x01)
            
        Returns:
            Raw response data
        """
        cmd = struct.pack('>BBBBBB', command, 0x04, 0x03, addr_high, addr_low, length)
        self.send_command(cmd)
        return self.read_response(length + 5)  # 3 header + 2 checksum + data
    
    def write_register(self, addr_high: int, addr_low: int, value: int) -> bytearray:
        """Write value to battery register"""
        cmd = struct.pack('>BBBBBB', 0x01, 0x05, 0x03, addr_high, addr_low, value)
        self.send_command(cmd)
        return self.read_response(2)
    
    def idle(self):
        """Set battery to idle state (J2 low)"""
        if self.port:
            self.port.break_condition = True
            self.port.dtr = True
    
    def high(self):
        """Set J2 high (20V simulation)"""
        if self.port:
            self.port.break_condition = False
            self.port.dtr = False
    
    def high_for_duration(self, duration: float):
        """Set J2 high for specified duration then idle"""
        self.high()
        time.sleep(duration)
        self.idle()
    
    def simulate_charger(self, duration: Optional[float] = None):
        """
        Simulate charger communication sequence
        
        Args:
            duration: Time to simulate in seconds (None for indefinite)
        """
        self.logger.info("Starting charger simulation...")
        self.save_and_set_debug(True)
        
        try:
            if not self.reset():
                raise M18ProtocolError("Failed to reset battery")
            
            # Initial configuration sequence
            self.configure(2)
            self.get_snapchat()
            time.sleep(0.6)
            self.keepalive()
            self.configure(1)
            self.get_snapchat()
            
            # Main charging loop
            start_time = time.time()
            while True:
                if duration and (time.time() - start_time) >= duration:
                    break
                    
                time.sleep(0.5)
                self.keepalive()
                
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted by user")
        except Exception as e:
            self.logger.error(f"Simulation failed: {e}")
        finally:
            self.idle()
            self.restore_debug()
            if duration:
                actual_duration = time.time() - start_time
                self.logger.info(f"Simulation duration: {actual_duration:.2f}s")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def main():
    """CLI interface for M18 protocol"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Milwaukee M18 Protocol Interface",
        epilog="Connect UART-TX to M18-J2 and UART-RX to M18-J1 with UART-GND to M18-GND"
    )
    parser.add_argument('--port', type=str, help="Serial port (e.g., COM5)")
    parser.add_argument('--simulate', type=float, help="Simulate charger for N seconds")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        with M18Protocol(port=args.port) as m18:
            if args.debug:
                m18.set_debug_printing(True)
            
            if args.simulate:
                m18.simulate_charger(args.simulate)
            else:
                print("M18 Protocol Interface initialized")
                print("Use m18.simulate_charger() to start simulation")
                print("Use m18.read_register(addr_h, addr_l, length) for diagnostics")
                
                # Start interactive shell
                import code
                code.InteractiveConsole(locals={'m18': m18}).interact()
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
