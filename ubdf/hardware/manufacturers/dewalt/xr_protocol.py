#!/usr/bin/env python3
"""
DeWalt XR Battery Protocol Implementation

This module implements the DeWalt XR battery communication protocol
for diagnostic data extraction and analysis.
"""

import serial
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ubdf.hardware.base.protocol_interface import (
    BatteryProtocol, RegisterDefinition, BatteryDiagnostics,
    BatteryState
)


@dataclass
class DeWaltXRProtocol(BatteryProtocol):
    """
    DeWalt XR battery protocol implementation
    
    Supports DeWalt 20V MAX XR and FLEXVOLT battery packs with
    I2C-based communication protocol.
    """
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.manufacturer = "DeWalt"
        self._baud_rate = 9600  # DeWalt uses standard I2C speeds
        self._timeout = 1.5
        self._last_error = None
        
        # DeWalt-specific I2C addresses
        self._battery_address = 0x0B
        self._auth_sequence = [0xDE, 0xA1, 0x7E]  # DeWalt authentication
        
    def get_register_map(self) -> Dict[int, RegisterDefinition]:
        """Get DeWalt XR register definitions"""
        return {
            # Battery identification
            0x00: RegisterDefinition(
                address=0x00, name="battery_mode", data_type="uint16",
                unit="flags", description="Battery mode and status flags"
            ),
            0x01: RegisterDefinition(
                address=0x01, name="temperature", data_type="uint16",
                unit="K", description="Battery temperature in Kelvin"
            ),
            0x02: RegisterDefinition(
                address=0x02, name="voltage", data_type="uint16",
                unit="mV", description="Battery voltage"
            ),
            0x03: RegisterDefinition(
                address=0x03, name="current", data_type="int16",
                unit="mA", description="Battery current"
            ),
            0x04: RegisterDefinition(
                address=0x04, name="average_current", data_type="int16",
                unit="mA", description="Average current"
            ),
            0x05: RegisterDefinition(
                address=0x05, name="max_error", data_type="uint8",
                unit="%", description="Max error percentage"
            ),
            0x06: RegisterDefinition(
                address=0x06, name="relative_soc", data_type="uint8",
                unit="%", description="Relative state of charge"
            ),
            0x07: RegisterDefinition(
                address=0x07, name="absolute_soc", data_type="uint8",
                unit="%", description="Absolute state of charge"
            ),
            0x08: RegisterDefinition(
                address=0x08, name="remaining_capacity", data_type="uint16",
                unit="mAh", description="Remaining capacity"
            ),
            0x09: RegisterDefinition(
                address=0x09, name="full_charge_capacity", data_type="uint16",
                unit="mAh", description="Full charge capacity"
            ),
            0x0A: RegisterDefinition(
                address=0x0A, name="run_time_to_empty", data_type="uint16",
                unit="min", description="Run time to empty"
            ),
            0x0B: RegisterDefinition(
                address=0x0B, name="average_time_to_empty", data_type="uint16",
                unit="min", description="Average time to empty"
            ),
            0x0C: RegisterDefinition(
                address=0x0C, name="time_to_full", data_type="uint16",
                unit="min", description="Time to full charge"
            ),
            0x0D: RegisterDefinition(
                address=0x0D, name="charging_current", data_type="uint16",
                unit="mA", description="Charging current"
            ),
            0x0E: RegisterDefinition(
                address=0x0E, name="charging_voltage", data_type="uint16",
                unit="mV", description="Charging voltage"
            ),
            0x0F: RegisterDefinition(
                address=0x0F, name="battery_status", data_type="uint16",
                unit="flags", description="Battery status flags"
            ),
            0x10: RegisterDefinition(
                address=0x10, name="cycle_count", data_type="uint16",
                unit="cycles", description="Cycle count"
            ),
            0x11: RegisterDefinition(
                address=0x11, name="design_capacity", data_type="uint16",
                unit="mAh", description="Design capacity"
            ),
            0x12: RegisterDefinition(
                address=0x12, name="design_voltage", data_type="uint16",
                unit="mV", description="Design voltage"
            ),
            0x13: RegisterDefinition(
                address=0x13, name="manufacture_date", data_type="uint16",
                unit="date", description="Manufacture date"
            ),
            0x14: RegisterDefinition(
                address=0x14, name="serial_number", data_type="uint16",
                unit="", description="Serial number"
            ),
            
            # Extended DeWalt-specific registers
            0x20: RegisterDefinition(
                address=0x20, name="cell_voltage_1", data_type="uint16",
                unit="mV", description="Cell 1 voltage"
            ),
            0x21: RegisterDefinition(
                address=0x21, name="cell_voltage_2", data_type="uint16",
                unit="mV", description="Cell 2 voltage"
            ),
            0x22: RegisterDefinition(
                address=0x22, name="cell_voltage_3", data_type="uint16",
                unit="mV", description="Cell 3 voltage"
            ),
            0x23: RegisterDefinition(
                address=0x23, name="cell_voltage_4", data_type="uint16",
                unit="mV", description="Cell 4 voltage"
            ),
            0x24: RegisterDefinition(
                address=0x24, name="cell_voltage_5", data_type="uint16",
                unit="mV", description="Cell 5 voltage"
            ),
            
            # Protection and safety
            0x30: RegisterDefinition(
                address=0x30, name="protection_status", data_type="uint16",
                unit="flags", description="Protection status"
            ),
            0x31: RegisterDefinition(
                address=0x31, name="alarm_status", data_type="uint16",
                unit="flags", description="Alarm status"
            ),
            0x32: RegisterDefinition(
                address=0x32, name="safety_status", data_type="uint16",
                unit="flags", description="Safety status"
            ),
        }
    
    def connect(self) -> bool:
        """Connect to DeWalt battery"""
        try:
            self.serial_port = serial.Serial(
                port=self.connection_string,
                baudrate=self._baud_rate,
                timeout=self._timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # DeWalt authentication sequence
            time.sleep(0.1)
            self.serial_port.write(bytes(self._auth_sequence))
            time.sleep(0.1)
            
            # Test communication with voltage read
            test_response = self.read_register(0x02)  # Voltage register
            if test_response is not None:
                self.state = BatteryState.CONNECTED
                return True
            else:
                self._last_error = "No response from DeWalt battery"
                return False
                
        except Exception as e:
            self._last_error = f"Connection failed: {str(e)}"
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from DeWalt battery"""
        try:
            if hasattr(self, 'serial_port') and self.serial_port:
                self.serial_port.close()
            self.state = BatteryState.DISCONNECTED
            return True
        except Exception as e:
            self._last_error = f"Disconnect failed: {str(e)}"
            return False
    
    def read_register(self, register_address: int) -> Optional[Any]:
        """Read single register value"""
        if not self.is_connected():
            return None
            
        try:
            cmd = self._build_read_command(register_address)
            self.serial_port.write(cmd)
            time.sleep(0.05)
            
            response = self.serial_port.read(10)
            return self._parse_register_response(register_address, response)
            
        except Exception as e:
            self._last_error = f"Register {register_address} read failed: {str(e)}"
            return None
    
    def write_register(self, register_address: int, value: int) -> bool:
        """Write register value (limited functionality)"""
        # DeWalt has limited write capabilities for safety
        if register_address not in [0x00, 0x0D, 0x0E]:  # Only mode and charging params
            self._last_error = f"Register {register_address} is read-only"
            return False
            
        try:
            cmd = self._build_write_command(register_address, value)
            self.serial_port.write(cmd)
            
            # Wait for acknowledgment
            response = self.serial_port.read(3)
            return len(response) > 0 and response[0] == 0xAC  # ACK
            
        except Exception as e:
            self._last_error = f"Register {register_address} write failed: {str(e)}"
            return False
    
    def _build_read_command(self, register_address: int) -> bytes:
        """Build DeWalt-specific read command"""
        # DeWalt I2C-style command: [ADDR] [READ_CMD] [REG] [LEN]
        cmd = bytearray()
        cmd.append(self._battery_address)  # Battery I2C address
        cmd.append(0x03)  # Read command
        cmd.append(register_address)
        cmd.append(0x02)  # Read 2 bytes (most registers are 16-bit)
        
        return bytes(cmd)
    
    def _build_write_command(self, register_address: int, value: int) -> bytes:
        """Build DeWalt-specific write command"""
        cmd = bytearray()
        cmd.append(self._battery_address)
        cmd.append(0x06)  # Write command
        cmd.append(register_address)
        cmd.append((value >> 8) & 0xFF)  # High byte
        cmd.append(value & 0xFF)         # Low byte
        
        return bytes(cmd)
    
    def _parse_register_response(self, register_address: int, response: bytes) -> Optional[Any]:
        """Parse DeWalt register response"""
        if len(response) < 3:
            return None
        
        # DeWalt response format: [LEN] [DATA...] or error
        data_length = response[0]
        if data_length == 0 or len(response) < data_length + 1:
            return None
            
        reg_map = self.get_register_map()
        if register_address not in reg_map:
            # Handle unknown registers
            if data_length >= 2:
                value = (response[1] << 8) | response[2]
                return value
            return None
            
        reg_def = reg_map[register_address]
        
        if reg_def.data_type == "int16":
            if data_length >= 2:
                value = (response[1] << 8) | response[2]
                # Convert to signed
                if value > 32767:
                    value -= 65536
                return value
        elif reg_def.data_type == "uint16":
            if data_length >= 2:
                value = (response[1] << 8) | response[2]
                return value
        elif reg_def.data_type == "uint8":
            if data_length >= 1:
                return response[1]
                
        return None
    
    def _calculate_health_metrics(self, registers: Dict[int, Any]) -> Dict[str, Any]:
        """Calculate DeWalt-specific health metrics"""
        metrics = super()._calculate_health_metrics(registers)
        
        # DeWalt-specific calculations
        soc = registers.get(0x06, 0)  # Relative SOC
        cycle_count = registers.get(0x10, 0)
        full_capacity = registers.get(0x09, 0)
        design_capacity = registers.get(0x11, 0)
        
        # Cell voltage analysis
        cell_voltages = []
        for i in range(0x20, 0x25):  # Cells 1-5
            voltage = registers.get(i, 0)
            if voltage > 0:
                cell_voltages.append(voltage)
                
        if cell_voltages:
            cell_imbalance = max(cell_voltages) - min(cell_voltages)
            metrics["cell_imbalance_mv"] = cell_imbalance
            metrics["min_cell_voltage_mv"] = min(cell_voltages)
            metrics["max_cell_voltage_mv"] = max(cell_voltages)
            
        # Temperature analysis
        temp_k = registers.get(0x01, 0)
        if temp_k > 0:
            temp_c = temp_k - 273.15  # Convert Kelvin to Celsius
            metrics["temperature_c"] = temp_c
            
        # Capacity retention
        if design_capacity > 0 and full_capacity > 0:
            capacity_retention = (full_capacity / design_capacity) * 100
            metrics["capacity_retention_pct"] = capacity_retention
            
        # DeWalt health score algorithm
        health_factors = []
        if capacity_retention > 0:
            health_factors.append(min(100, capacity_retention))
        if cycle_count > 0:
            cycle_factor = max(0, 100 - (cycle_count / 15))  # Assume 1500 cycle life
            health_factors.append(cycle_factor)
        if cell_voltages:
            voltage_factor = 100 - (cell_imbalance / 50)  # Penalize imbalance
            health_factors.append(max(0, voltage_factor))
            
        if health_factors:
            dewalt_health_score = sum(health_factors) / len(health_factors)
            metrics["dewalt_health_score"] = int(dewalt_health_score)
        
        # Power analysis
        voltage = registers.get(0x02, 0)
        current = registers.get(0x03, 0)
        if voltage > 0 and current != 0:
            power_w = (voltage * abs(current)) / 1000000  # Convert to watts
            metrics["instantaneous_power_w"] = power_w
        
        metrics.update({
            "state_of_charge": soc,
            "cycle_count": cycle_count,
            "full_charge_capacity_mah": full_capacity,
            "design_capacity_mah": design_capacity,
        })
        
        return metrics
    
    def _generate_battery_id(self, registers: Dict[int, Any]) -> str:
        """Generate DeWalt battery ID"""
        serial = registers.get(0x14, 0)
        voltage = registers.get(0x12, 0)  # Design voltage
        return f"XR_{serial:04X}_{voltage}V"
        
    def _detect_model(self, registers: Dict[int, Any]) -> str:
        """Detect DeWalt battery model"""
        design_voltage = registers.get(0x12, 0)
        design_capacity = registers.get(0x11, 0)
        
        # DeWalt model detection based on voltage and capacity
        if design_voltage >= 18000:  # 18V+ batteries
            if design_capacity >= 9000:
                return "DCB609"  # FLEXVOLT 9.0Ah
            elif design_capacity >= 6000:
                return "DCB606"  # FLEXVOLT 6.0Ah
            elif design_capacity >= 5000:
                return "DCB205"  # 20V MAX XR 5.0Ah
            elif design_capacity >= 4000:
                return "DCB204"  # 20V MAX XR 4.0Ah
            elif design_capacity >= 2000:
                return "DCB203"  # 20V MAX XR 2.0Ah
            else:
                return "DCB201"  # 20V MAX 1.3Ah
        elif design_voltage >= 12000:  # 12V batteries
            if design_capacity >= 3000:
                return "DCB127"  # 12V MAX 3.0Ah
            else:
                return "DCB120"  # 12V MAX 1.3Ah
        else:
            return f"Unknown_XR_{design_voltage}mV_{design_capacity}mAh"


# Utility functions
def discover_dewalt_batteries(port_pattern: str = "/dev/ttyUSB*") -> List[str]:
    """Discover DeWalt batteries on available ports"""
    import glob
    discovered = []
    
    ports = glob.glob(port_pattern)
    for port in ports:
        try:
            protocol = DeWaltXRProtocol(port)
            if protocol.connect():
                success, test_results = protocol.test_connection()
                if success:
                    discovered.append(port)
                protocol.disconnect()
        except:
            pass
            
    return discovered