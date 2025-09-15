#!/usr/bin/env python3
"""
Ryobi ONE+ Battery Protocol Implementation

This module implements the Ryobi ONE+ battery communication protocol
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
class RyobiOnePlusProtocol(BatteryProtocol):
    """
    Ryobi ONE+ battery protocol implementation
    
    Supports Ryobi 18V ONE+ and 40V battery packs with
    proprietary communication protocol.
    """
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.manufacturer = "Ryobi"
        self._baud_rate = 38400  # Ryobi uses higher baud rate
        self._timeout = 1.0
        self._last_error = None
        
        # Ryobi-specific command sequences
        self._wake_command = [0x52, 0x59, 0x4F]  # "RYO" wake sequence
        self._auth_key = 0x42  # Ryobi authentication key
        
    def get_register_map(self) -> Dict[int, RegisterDefinition]:
        """Get Ryobi ONE+ register definitions"""
        return {
            # System identification
            0x01: RegisterDefinition(
                address=0x01, name="system_status", data_type="uint8",
                unit="flags", description="System status flags"
            ),
            0x02: RegisterDefinition(
                address=0x02, name="battery_type", data_type="uint8",
                unit="", description="Battery type identifier"
            ),
            0x03: RegisterDefinition(
                address=0x03, name="firmware_version", data_type="uint16",
                unit="", description="Firmware version"
            ),
            0x04: RegisterDefinition(
                address=0x04, name="hardware_version", data_type="uint8",
                unit="", description="Hardware version"
            ),
            
            # Voltage and current
            0x10: RegisterDefinition(
                address=0x10, name="pack_voltage", data_type="uint16",
                unit="mV", description="Pack voltage"
            ),
            0x11: RegisterDefinition(
                address=0x11, name="pack_current", data_type="int16", 
                unit="mA", description="Pack current"
            ),
            0x12: RegisterDefinition(
                address=0x12, name="cell_voltage_1", data_type="uint16",
                unit="mV", description="Cell 1 voltage"
            ),
            0x13: RegisterDefinition(
                address=0x13, name="cell_voltage_2", data_type="uint16",
                unit="mV", description="Cell 2 voltage"
            ),
            0x14: RegisterDefinition(
                address=0x14, name="cell_voltage_3", data_type="uint16",
                unit="mV", description="Cell 3 voltage"
            ),
            0x15: RegisterDefinition(
                address=0x15, name="cell_voltage_4", data_type="uint16",
                unit="mV", description="Cell 4 voltage"
            ),
            0x16: RegisterDefinition(
                address=0x16, name="cell_voltage_5", data_type="uint16",
                unit="mV", description="Cell 5 voltage"
            ),
            
            # Temperature sensors
            0x20: RegisterDefinition(
                address=0x20, name="temp_sensor_1", data_type="int16",
                unit="0.1°C", description="Temperature sensor 1"
            ),
            0x21: RegisterDefinition(
                address=0x21, name="temp_sensor_2", data_type="int16",
                unit="0.1°C", description="Temperature sensor 2"
            ),
            0x22: RegisterDefinition(
                address=0x22, name="ambient_temp", data_type="int16",
                unit="0.1°C", description="Ambient temperature"
            ),
            
            # Capacity and state
            0x30: RegisterDefinition(
                address=0x30, name="state_of_charge", data_type="uint8",
                unit="%", description="State of charge"
            ),
            0x31: RegisterDefinition(
                address=0x31, name="remaining_capacity", data_type="uint16",
                unit="mAh", description="Remaining capacity"
            ),
            0x32: RegisterDefinition(
                address=0x32, name="full_charge_capacity", data_type="uint16",
                unit="mAh", description="Full charge capacity"
            ),
            0x33: RegisterDefinition(
                address=0x33, name="design_capacity", data_type="uint16",
                unit="mAh", description="Design capacity"
            ),
            0x34: RegisterDefinition(
                address=0x34, name="capacity_percentage", data_type="uint8",
                unit="%", description="Capacity percentage vs design"
            ),
            
            # Cycle information
            0x40: RegisterDefinition(
                address=0x40, name="cycle_count", data_type="uint16",
                unit="cycles", description="Charge cycle count"
            ),
            0x41: RegisterDefinition(
                address=0x41, name="deep_cycle_count", data_type="uint16",
                unit="cycles", description="Deep discharge cycles"
            ),
            0x42: RegisterDefinition(
                address=0x42, name="charge_time_total", data_type="uint32",
                unit="hours", description="Total charging time"
            ),
            0x43: RegisterDefinition(
                address=0x43, name="discharge_time_total", data_type="uint32",
                unit="hours", description="Total discharge time"
            ),
            
            # Manufacturing data
            0x50: RegisterDefinition(
                address=0x50, name="manufacture_date", data_type="uint16",
                unit="date", description="Manufacture date code"
            ),
            0x51: RegisterDefinition(
                address=0x51, name="serial_number", data_type="uint32",
                unit="", description="Battery serial number"
            ),
            0x52: RegisterDefinition(
                address=0x52, name="part_number", data_type="uint16",
                unit="", description="Part number code"
            ),
            
            # Protection and safety
            0x60: RegisterDefinition(
                address=0x60, name="protection_flags", data_type="uint16",
                unit="flags", description="Protection status flags"
            ),
            0x61: RegisterDefinition(
                address=0x61, name="alarm_flags", data_type="uint16", 
                unit="flags", description="Alarm status flags"
            ),
            0x62: RegisterDefinition(
                address=0x62, name="error_code", data_type="uint8",
                unit="", description="Last error code"
            ),
            
            # Internal resistance (estimated)
            0x70: RegisterDefinition(
                address=0x70, name="internal_resistance", data_type="uint16",
                unit="mOhm", description="Estimated internal resistance"
            ),
        }
    
    def connect(self) -> bool:
        """Connect to Ryobi battery"""
        try:
            self.serial_port = serial.Serial(
                port=self.connection_string,
                baudrate=self._baud_rate,
                timeout=self._timeout,
                parity=serial.PARITY_EVEN,  # Ryobi uses even parity
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Ryobi wake and authentication sequence
            time.sleep(0.1)
            self.serial_port.write(bytes(self._wake_command))
            time.sleep(0.05)
            
            # Send authentication key
            auth_cmd = [0x41, self._auth_key, 0x00]  # Auth command
            self.serial_port.write(bytes(auth_cmd))
            
            # Wait for authentication response
            response = self.serial_port.read(4)
            if len(response) >= 2 and response[0] == 0x52 and response[1] == 0x4F:  # "RO" response
                self.state = BatteryState.CONNECTED
                return True
            else:
                self._last_error = "Authentication failed"
                return False
                
        except Exception as e:
            self._last_error = f"Connection failed: {str(e)}"
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Ryobi battery"""
        try:
            if hasattr(self, 'serial_port') and self.serial_port:
                # Send disconnect command
                self.serial_port.write(bytes([0x44, 0x43]))  # "DC" disconnect
                time.sleep(0.1)
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
            time.sleep(0.02)  # Ryobi needs shorter delays
            
            response = self.serial_port.read(8)
            return self._parse_register_response(register_address, response)
            
        except Exception as e:
            self._last_error = f"Register {register_address} read failed: {str(e)}"
            return None
    
    def write_register(self, register_address: int, value: int) -> bool:
        """Write register value (very limited on Ryobi)"""
        # Ryobi batteries allow almost no write operations for safety
        self._last_error = "Write operations not supported on Ryobi batteries"
        return False
    
    def _build_read_command(self, register_address: int) -> bytes:
        """Build Ryobi-specific read command"""
        # Ryobi command format: [CMD] [ADDR] [LEN] [CRC]
        cmd = bytearray()
        cmd.append(0x52)  # Read command 'R'
        cmd.append(register_address)
        cmd.append(0x04)  # Read 4 bytes max
        
        # Simple CRC calculation (XOR of bytes)
        crc = 0
        for byte in cmd:
            crc ^= byte
        cmd.append(crc)
        
        return bytes(cmd)
    
    def _parse_register_response(self, register_address: int, response: bytes) -> Optional[Any]:
        """Parse Ryobi register response"""
        if len(response) < 3:
            return None
            
        # Ryobi response format: [STATUS] [LEN] [DATA...] [CRC]
        if response[0] != 0x4F:  # 'O' for OK
            return None
            
        data_length = response[1]
        if data_length == 0 or len(response) < data_length + 3:
            return None
            
        # Extract data
        data = response[2:2+data_length]
        
        reg_map = self.get_register_map()
        if register_address not in reg_map:
            # Handle unknown registers
            if data_length >= 2:
                value = (data[0] << 8) | data[1]
                return value
            elif data_length >= 1:
                return data[0]
            return None
            
        reg_def = reg_map[register_address]
        
        if reg_def.data_type == "uint32":
            if data_length >= 4:
                value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
                return value
        elif reg_def.data_type == "int16":
            if data_length >= 2:
                value = (data[0] << 8) | data[1]
                # Convert to signed
                if value > 32767:
                    value -= 65536
                return value
        elif reg_def.data_type == "uint16":
            if data_length >= 2:
                value = (data[0] << 8) | data[1]
                return value
        elif reg_def.data_type == "uint8":
            if data_length >= 1:
                return data[0]
                
        return None
    
    def _calculate_health_metrics(self, registers: Dict[int, Any]) -> Dict[str, Any]:
        """Calculate Ryobi-specific health metrics"""
        metrics = super()._calculate_health_metrics(registers)
        
        # Ryobi-specific calculations
        soc = registers.get(0x30, 0)
        capacity_pct = registers.get(0x34, 0)
        cycle_count = registers.get(0x40, 0)
        deep_cycles = registers.get(0x41, 0)
        
        # Cell voltage analysis
        cell_voltages = []
        for i in range(0x12, 0x17):  # Cells 1-5
            voltage = registers.get(i, 0)
            if voltage > 0:
                cell_voltages.append(voltage)
                
        if cell_voltages:
            cell_imbalance = max(cell_voltages) - min(cell_voltages)
            metrics["cell_imbalance_mv"] = cell_imbalance
            metrics["cell_count"] = len(cell_voltages)
            
        # Temperature analysis
        temps = []
        for temp_reg in [0x20, 0x21, 0x22]:
            temp = registers.get(temp_reg, 0)
            if temp != 0:
                temps.append(temp / 10.0)  # Convert to Celsius
                
        if temps:
            metrics["average_temperature_c"] = sum(temps) / len(temps)
            metrics["max_temperature_c"] = max(temps)
            
        # Capacity analysis
        remaining = registers.get(0x31, 0)
        full_charge = registers.get(0x32, 0)
        design = registers.get(0x33, 0)
        
        if design > 0:
            if full_charge > 0:
                retention = (full_charge / design) * 100
                metrics["capacity_retention_pct"] = retention
            if remaining > 0:
                energy_remaining = (remaining / design) * 100
                metrics["energy_remaining_pct"] = energy_remaining
                
        # Usage analysis
        charge_time = registers.get(0x42, 0)
        discharge_time = registers.get(0x43, 0)
        if charge_time > 0 and discharge_time > 0:
            usage_ratio = discharge_time / (charge_time + discharge_time)
            metrics["usage_ratio"] = usage_ratio
            
        # Ryobi health score algorithm
        health_factors = []
        if capacity_pct > 0:
            health_factors.append(capacity_pct)
        if cycle_count > 0:
            cycle_factor = max(0, 100 - (cycle_count / 10))  # Assume 1000 cycle life
            health_factors.append(cycle_factor)
        if deep_cycles > 0 and cycle_count > 0:
            deep_cycle_ratio = (deep_cycles / cycle_count) * 100
            deep_factor = max(0, 100 - deep_cycle_ratio)  # Penalize deep cycles
            health_factors.append(deep_factor)
            
        if health_factors:
            ryobi_health_score = sum(health_factors) / len(health_factors)
            metrics["ryobi_health_score"] = int(ryobi_health_score)
        
        metrics.update({
            "state_of_charge": soc,
            "capacity_percentage": capacity_pct,
            "cycle_count": cycle_count,
            "deep_cycle_count": deep_cycles,
            "internal_resistance_mohm": registers.get(0x70, 0),
        })
        
        return metrics
    
    def _generate_battery_id(self, registers: Dict[int, Any]) -> str:
        """Generate Ryobi battery ID"""
        serial = registers.get(0x51, 0)
        part_number = registers.get(0x52, 0)
        return f"ONE+_{serial:08X}_{part_number:04X}"
        
    def _detect_model(self, registers: Dict[int, Any]) -> str:
        """Detect Ryobi battery model"""
        battery_type = registers.get(0x02, 0)
        part_number = registers.get(0x52, 0)
        design_capacity = registers.get(0x33, 0)
        
        # Ryobi model detection logic
        if battery_type == 0x18:  # 18V ONE+ batteries
            if design_capacity >= 6000:
                return "P193"   # 18V 6.0Ah HP
            elif design_capacity >= 4000:
                return "P191"   # 18V 4.0Ah HP 
            elif design_capacity >= 2500:
                return "P108"   # 18V 2.5Ah
            elif design_capacity >= 1500:
                return "P107"   # 18V 1.5Ah
            else:
                return "P102"   # 18V 1.3Ah
        elif battery_type == 0x40:  # 40V batteries
            if design_capacity >= 6000:
                return "OP4060A"  # 40V 6.0Ah
            elif design_capacity >= 4000:
                return "OP4040"   # 40V 4.0Ah
            else:
                return "OP4026"   # 40V 2.6Ah
        else:
            return f"Unknown_ONE+_{battery_type:02X}_{design_capacity}mAh"


# Utility functions
def discover_ryobi_batteries(port_pattern: str = "/dev/ttyUSB*") -> List[str]:
    """Discover Ryobi batteries on available ports"""
    import glob
    discovered = []
    
    ports = glob.glob(port_pattern)
    for port in ports:
        try:
            protocol = RyobiOnePlusProtocol(port)
            if protocol.connect():
                success, test_results = protocol.test_connection()
                if success:
                    discovered.append(port)
                protocol.disconnect()
        except:
            pass
            
    return discovered