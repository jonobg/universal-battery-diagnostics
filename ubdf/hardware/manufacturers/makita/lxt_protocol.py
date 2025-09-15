#!/usr/bin/env python3
"""
Makita LXT Battery Protocol Implementation

This module implements the Makita LXT battery communication protocol
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
class MakitaLXTProtocol(BatteryProtocol):
    """
    Makita LXT battery protocol implementation
    
    Supports Makita 18V LXT and 36V LXT battery packs with CAN-based
    communication protocol.
    """
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.manufacturer = "Makita"
        self._baud_rate = 19200  # Makita uses different baud rate
        self._timeout = 2.0
        self._last_error = None
        
        # Makita-specific command sequences
        self._init_sequence = [0x55, 0xAA, 0x01]
        self._wake_sequence = [0x47, 0x4D, 0x00]
        
    def get_register_map(self) -> Dict[int, RegisterDefinition]:
        """Get Makita LXT register definitions"""
        return {
            # Battery identification
            0x10: RegisterDefinition(
                address=0x10, name="model_code", data_type="uint16",
                unit="", description="Makita model identification code"
            ),
            0x11: RegisterDefinition(
                address=0x11, name="serial_number", data_type="uint32",
                unit="", description="Battery serial number"
            ),
            0x12: RegisterDefinition(
                address=0x12, name="manufacture_date", data_type="uint16",
                unit="days", description="Days since 2000-01-01"
            ),
            
            # Voltage measurements
            0x20: RegisterDefinition(
                address=0x20, name="pack_voltage", data_type="uint16",
                unit="mV", description="Total pack voltage"
            ),
            0x21: RegisterDefinition(
                address=0x21, name="cell_voltages", data_type="array",
                unit="mV", description="Individual cell voltages",
                array_length=5
            ),
            
            # Current measurements  
            0x25: RegisterDefinition(
                address=0x25, name="pack_current", data_type="int16",
                unit="mA", description="Pack current (+ = discharge)"
            ),
            
            # Temperature sensors
            0x30: RegisterDefinition(
                address=0x30, name="cell_temperatures", data_type="array",
                unit="0.1°C", description="Cell temperatures",
                array_length=3
            ),
            0x31: RegisterDefinition(
                address=0x31, name="pcb_temperature", data_type="int16",
                unit="0.1°C", description="PCB temperature"
            ),
            
            # Capacity and health
            0x40: RegisterDefinition(
                address=0x40, name="remaining_capacity", data_type="uint16",
                unit="mAh", description="Remaining capacity"
            ),
            0x41: RegisterDefinition(
                address=0x41, name="full_charge_capacity", data_type="uint16",
                unit="mAh", description="Full charge capacity"
            ),
            0x42: RegisterDefinition(
                address=0x42, name="design_capacity", data_type="uint16", 
                unit="mAh", description="Design capacity"
            ),
            0x43: RegisterDefinition(
                address=0x43, name="state_of_charge", data_type="uint8",
                unit="%", description="State of charge percentage"
            ),
            0x44: RegisterDefinition(
                address=0x44, name="state_of_health", data_type="uint8",
                unit="%", description="State of health percentage"
            ),
            
            # Cycle counts and usage
            0x50: RegisterDefinition(
                address=0x50, name="cycle_count", data_type="uint16",
                unit="cycles", description="Charge cycle count"
            ),
            0x51: RegisterDefinition(
                address=0x51, name="deep_discharge_count", data_type="uint16",
                unit="events", description="Deep discharge events"
            ),
            
            # Status and protection
            0x60: RegisterDefinition(
                address=0x60, name="battery_status", data_type="uint16",
                unit="flags", description="Battery status flags"
            ),
            0x61: RegisterDefinition(
                address=0x61, name="protection_status", data_type="uint16",
                unit="flags", description="Protection circuit status"
            ),
            
            # Internal resistance
            0x70: RegisterDefinition(
                address=0x70, name="internal_resistance", data_type="uint16",
                unit="mOhm", description="Pack internal resistance"
            ),
        }
    
    def connect(self) -> bool:
        """Connect to Makita battery"""
        try:
            self.serial_port = serial.Serial(
                port=self.connection_string,
                baudrate=self._baud_rate,
                timeout=self._timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Makita initialization sequence
            time.sleep(0.1)
            self.serial_port.write(bytes(self._wake_sequence))
            time.sleep(0.1)
            self.serial_port.write(bytes(self._init_sequence))
            
            # Wait for response
            response = self.serial_port.read(3)
            if len(response) >= 2 and response[0] == 0x4D and response[1] == 0x4B:
                self.state = BatteryState.CONNECTED
                return True
            else:
                self._last_error = "Invalid initialization response"
                return False
                
        except Exception as e:
            self._last_error = f"Connection failed: {str(e)}"
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Makita battery"""
        try:
            if hasattr(self, 'serial_port') and self.serial_port:
                # Send sleep command
                self.serial_port.write(bytes([0x47, 0x4D, 0xFF]))
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
            time.sleep(0.05)
            
            response = self.serial_port.read(20)  # Makita responses vary in length
            return self._parse_register_response(register_address, response)
            
        except Exception as e:
            self._last_error = f"Register {register_address} read failed: {str(e)}"
            return None
    
    def write_register(self, register_address: int, value: int) -> bool:
        """Write register value (limited functionality for Makita)"""
        # Makita batteries have very limited write capabilities
        self._last_error = "Write operations not supported on Makita batteries"
        return False
    
    def _build_read_command(self, register_address: int) -> bytes:
        """Build Makita-specific read command"""
        # Makita command format: [HEADER] [CMD] [ADDR] [LEN] [CHECKSUM]
        cmd = bytearray()
        cmd.append(0x47)  # Header byte
        cmd.append(0x52)  # Read command
        cmd.append(register_address & 0xFF)  # Register address
        cmd.append(0x01)  # Read length
        
        # Calculate checksum (sum of bytes modulo 256)
        checksum = sum(cmd) & 0xFF
        cmd.append((256 - checksum) & 0xFF)
        
        return bytes(cmd)
    
    def _parse_register_response(self, register_address: int, response: bytes) -> Optional[Any]:
        """Parse Makita register response"""
        if len(response) < 4:
            return None
            
        # Makita response format: [HEADER] [ADDR] [DATA...] [CHECKSUM]
        if response[0] != 0x4D:  # 'M' for Makita
            return None
            
        # Verify checksum
        calc_checksum = sum(response[:-1]) & 0xFF
        expected_checksum = (256 - calc_checksum) & 0xFF
        if response[-1] != expected_checksum:
            return None
            
        reg_map = self.get_register_map()
        if register_address not in reg_map:
            # Handle unknown registers
            if len(response) >= 5:
                value = (response[2] << 8) | response[3]
                return value
            return None
            
        reg_def = reg_map[register_address]
        
        if reg_def.data_type == "array":
            values = []
            data_start = 2
            for i in range(reg_def.array_length or 1):
                if data_start + 1 < len(response) - 1:
                    value = (response[data_start] << 8) | response[data_start + 1]
                    values.append(value)
                    data_start += 2
            return values
        elif reg_def.data_type == "uint32":
            if len(response) >= 7:
                value = (response[2] << 24) | (response[3] << 16) | (response[4] << 8) | response[5]
                return value
        elif reg_def.data_type == "int16":
            if len(response) >= 5:
                value = (response[2] << 8) | response[3]
                # Convert to signed
                if value > 32767:
                    value -= 65536
                return value
        elif reg_def.data_type == "uint16":
            if len(response) >= 5:
                value = (response[2] << 8) | response[3]
                return value
        elif reg_def.data_type == "uint8":
            if len(response) >= 4:
                return response[2]
                
        return None
    
    def _calculate_health_metrics(self, registers: Dict[int, Any]) -> Dict[str, Any]:
        """Calculate Makita-specific health metrics"""
        metrics = super()._calculate_health_metrics(registers)
        
        # Makita-specific calculations
        soc = registers.get(0x43, 0)
        soh = registers.get(0x44, 0) 
        cycle_count = registers.get(0x50, 0)
        internal_resistance = registers.get(0x70, 0)
        
        # Cell balance analysis
        cell_voltages = registers.get(0x21, [])
        if cell_voltages and len(cell_voltages) >= 5:
            cell_imbalance = max(cell_voltages) - min(cell_voltages)
            metrics["cell_imbalance_mv"] = cell_imbalance
            
        # Temperature analysis  
        cell_temps = registers.get(0x30, [])
        if cell_temps:
            avg_temp = sum(cell_temps) / len(cell_temps)
            max_temp = max(cell_temps)
            metrics["average_temperature_c"] = avg_temp / 10.0
            metrics["max_temperature_c"] = max_temp / 10.0
            
        # Makita health score algorithm
        health_factors = []
        if soh > 0:
            health_factors.append(soh)
        if cycle_count > 0:
            cycle_factor = max(0, 100 - (cycle_count / 10))  # Assume 1000 cycle life
            health_factors.append(cycle_factor)
        if internal_resistance > 0:
            resistance_factor = max(0, 100 - (internal_resistance / 5))  # Assume 500mOhm max
            health_factors.append(resistance_factor)
            
        if health_factors:
            makita_health_score = sum(health_factors) / len(health_factors)
            metrics["makita_health_score"] = int(makita_health_score)
        
        # Capacity analysis
        remaining = registers.get(0x40, 0)
        full_charge = registers.get(0x41, 0)
        design = registers.get(0x42, 0)
        
        if design > 0:
            if full_charge > 0:
                capacity_retention = (full_charge / design) * 100
                metrics["capacity_retention_pct"] = capacity_retention
            if remaining > 0:
                energy_remaining = (remaining / design) * 100
                metrics["energy_remaining_pct"] = energy_remaining
        
        metrics.update({
            "state_of_charge": soc,
            "state_of_health": soh,
            "cycle_count": cycle_count,
            "internal_resistance_mohm": internal_resistance,
            "deep_discharge_events": registers.get(0x51, 0),
        })
        
        return metrics
    
    def _generate_battery_id(self, registers: Dict[int, Any]) -> str:
        """Generate Makita battery ID"""
        serial = registers.get(0x11, 0)
        model = registers.get(0x10, 0)
        return f"LXT_{serial:08X}_{model:04X}"
        
    def _detect_model(self, registers: Dict[int, Any]) -> str:
        """Detect Makita battery model"""
        model_code = registers.get(0x10, 0)
        
        # Makita LXT model mappings
        model_map = {
            0x1830: "BL1830B",  # 18V 3.0Ah
            0x1840: "BL1840B",  # 18V 4.0Ah 
            0x1850: "BL1850B",  # 18V 5.0Ah
            0x1860: "BL1860B",  # 18V 6.0Ah
            0x3640: "BL3640",   # 36V 4.0Ah
            0x3650: "BL3650",   # 36V 5.0Ah
            0x4050: "BL4050F",  # 40V 5.0Ah
        }
        
        return model_map.get(model_code, f"Unknown_LXT_{model_code:04X}")


# Utility functions
def discover_makita_batteries(port_pattern: str = "/dev/ttyUSB*") -> List[str]:
    """Discover Makita batteries on available ports"""
    import glob
    discovered = []
    
    ports = glob.glob(port_pattern)
    for port in ports:
        try:
            protocol = MakitaLXTProtocol(port)
            if protocol.connect():
                success, test_results = protocol.test_connection()
                if success:
                    discovered.append(port)
                protocol.disconnect()
        except:
            pass
            
    return discovered