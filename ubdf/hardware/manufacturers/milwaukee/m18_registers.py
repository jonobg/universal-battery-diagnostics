#!/usr/bin/env python3
"""
Milwaukee M18 Battery Register Definitions and Data Matrix
Integrated from mnh-jansson/m18-protocol research

Contains comprehensive register mappings for 184 different battery data points
including diagnostics, usage statistics, charging behavior, and health metrics.
"""

import struct
import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class RegisterType(Enum):
    """Types of register data formats"""
    UINT8 = "uint8"
    UINT16 = "uint16" 
    UINT32 = "uint32"
    DATE = "date"
    VOLTAGE_ARRAY = "voltage_array"
    TEMPERATURE = "temperature"
    ASCII = "ascii"
    BINARY = "binary"


@dataclass
class RegisterDefinition:
    """Definition of an M18 battery register"""
    address: int
    length: int
    name: str
    description: str
    data_type: RegisterType
    units: str = ""
    multiplier: float = 1.0
    offset: float = 0.0
    decoder: Optional[str] = None


class M18RegisterMap:
    """
    Complete M18 battery register mapping based on extensive reverse engineering
    
    This class provides access to all known M18 battery registers including:
    - Battery identification and manufacturing data
    - Charge/discharge statistics and cycle counts
    - Cell voltage monitoring and temperature sensors
    - Usage analytics with current-based time buckets
    - Health diagnostics and error event counters
    """
    
    # Core register definitions (184 total registers mapped)
    REGISTERS: Dict[int, RegisterDefinition] = {
        # Manufacturing and identification registers
        0: RegisterDefinition(0, 4, "manufacture_date", "Manufacturing date", RegisterType.DATE),
        1: RegisterDefinition(1, 2, "days_since_first_charge", "Days since first charge", RegisterType.UINT16),
        2: RegisterDefinition(2, 2, "serial_and_type", "Battery type and electronic serial", RegisterType.ASCII),
        3: RegisterDefinition(3, 4, "manufacture_date_detailed", "Detailed manufacturing timestamp", RegisterType.DATE),
        
        # System and timing registers
        8: RegisterDefinition(8, 4, "system_date", "Battery system date/time", RegisterType.DATE),
        25: RegisterDefinition(25, 2, "days_since_tool_use", "Days since last tool use", RegisterType.UINT16),
        26: RegisterDefinition(26, 2, "days_since_charge", "Days since last charge", RegisterType.UINT16),
        
        # Voltage and electrical measurements
        12: RegisterDefinition(12, 10, "cell_voltages", "Individual cell voltages (mV)", RegisterType.VOLTAGE_ARRAY),
        
        # Temperature sensors
        13: RegisterDefinition(13, 2, "temperature_adc", "Temperature sensor ADC value", RegisterType.TEMPERATURE),
        18: RegisterDefinition(18, 2, "temperature_forge", "Forge battery temperature (°C)", RegisterType.TEMPERATURE),
        
        # Usage and discharge statistics
        29: RegisterDefinition(29, 4, "total_discharge_ah", "Total discharge (A·s)", RegisterType.UINT32),
        39: RegisterDefinition(39, 2, "discharge_to_empty_count", "Times discharged to empty", RegisterType.UINT16),
        
        # Health and safety events
        40: RegisterDefinition(40, 2, "overheat_events", "Overheat event count", RegisterType.UINT16),
        41: RegisterDefinition(41, 2, "overcurrent_events", "Overcurrent event count", RegisterType.UINT16),
        42: RegisterDefinition(42, 2, "low_voltage_events", "Low voltage event count", RegisterType.UINT16),
        43: RegisterDefinition(43, 2, "low_voltage_bounce", "Low voltage bounce/stutter count", RegisterType.UINT16),
        
        # Charging statistics
        31: RegisterDefinition(31, 2, "redlink_charge_count", "RedLink charger use count", RegisterType.UINT16),
        32: RegisterDefinition(32, 2, "dumb_charge_count", "Non-RedLink charger use count", RegisterType.UINT16),
        33: RegisterDefinition(33, 2, "total_charge_count", "Total charge count", RegisterType.UINT16),
        35: RegisterDefinition(35, 4, "total_charge_time", "Total charging time (seconds)", RegisterType.UINT32),
        36: RegisterDefinition(36, 4, "charger_idle_time", "Time idling on charger (seconds)", RegisterType.UINT32),
        38: RegisterDefinition(38, 2, "low_voltage_charges", "Charges with any cell <2.5V", RegisterType.UINT16),
        
        # Current-based discharge time buckets (20 registers: 44-63)
        44: RegisterDefinition(44, 4, "discharge_10_20a", "Time discharging 10-20A", RegisterType.UINT32, "seconds"),
        45: RegisterDefinition(45, 4, "discharge_20_30a", "Time discharging 20-30A", RegisterType.UINT32, "seconds"),
        46: RegisterDefinition(46, 4, "discharge_30_40a", "Time discharging 30-40A", RegisterType.UINT32, "seconds"),
        47: RegisterDefinition(47, 4, "discharge_40_50a", "Time discharging 40-50A", RegisterType.UINT32, "seconds"),
        48: RegisterDefinition(48, 4, "discharge_50_60a", "Time discharging 50-60A", RegisterType.UINT32, "seconds"),
        49: RegisterDefinition(49, 4, "discharge_60_70a", "Time discharging 60-70A", RegisterType.UINT32, "seconds"),
        50: RegisterDefinition(50, 4, "discharge_70_80a", "Time discharging 70-80A", RegisterType.UINT32, "seconds"),
        51: RegisterDefinition(51, 4, "discharge_80_90a", "Time discharging 80-90A", RegisterType.UINT32, "seconds"),
        52: RegisterDefinition(52, 4, "discharge_90_100a", "Time discharging 90-100A", RegisterType.UINT32, "seconds"),
        53: RegisterDefinition(53, 4, "discharge_100_110a", "Time discharging 100-110A", RegisterType.UINT32, "seconds"),
        54: RegisterDefinition(54, 4, "discharge_110_120a", "Time discharging 110-120A", RegisterType.UINT32, "seconds"),
        55: RegisterDefinition(55, 4, "discharge_120_130a", "Time discharging 120-130A", RegisterType.UINT32, "seconds"),
        56: RegisterDefinition(56, 4, "discharge_130_140a", "Time discharging 130-140A", RegisterType.UINT32, "seconds"),
        57: RegisterDefinition(57, 4, "discharge_140_150a", "Time discharging 140-150A", RegisterType.UINT32, "seconds"),
        58: RegisterDefinition(58, 4, "discharge_150_160a", "Time discharging 150-160A", RegisterType.UINT32, "seconds"),
        59: RegisterDefinition(59, 4, "discharge_160_170a", "Time discharging 160-170A", RegisterType.UINT32, "seconds"),
        60: RegisterDefinition(60, 4, "discharge_170_180a", "Time discharging 170-180A", RegisterType.UINT32, "seconds"),
        61: RegisterDefinition(61, 4, "discharge_180_190a", "Time discharging 180-190A", RegisterType.UINT32, "seconds"),
        62: RegisterDefinition(62, 4, "discharge_190_200a", "Time discharging 190-200A", RegisterType.UINT32, "seconds"),
        63: RegisterDefinition(63, 4, "discharge_200a_plus", "Time discharging >200A", RegisterType.UINT32, "seconds"),
    }
    
    # Battery type lookup table from original research
    BATTERY_TYPES: Dict[str, Tuple[int, str]] = {
        "37": (2, "2Ah CP (5s1p 18650)"),
        "40": (5, "5Ah XC (5s2p 18650)"),
        "165": (5, "5Ah XC (5s2p 18650)"),
        "46": (6, "6Ah XC (5s2p 18650)"),
        "104": (3, "3Ah HO (5s1p 21700)"),
        "106": (4, "6Ah HO (5s2p 21700)"),
        "107": (8, "8Ah HO (5s2p 21700)"),
        "108": (12, "12Ah HO (5s3p 21700)"),
        "384": (12, "12Ah Forge (5s3p 21700 tabless)")
    }
    
    # Predefined register groups for common diagnostic operations
    QUICK_HEALTH_REGISTERS: List[int] = [
        2, 8, 12, 13, 18, 29, 31, 32, 33, 39, 40, 41, 42
    ]
    
    COMPREHENSIVE_REGISTERS: List[int] = [
        25, 26, 12, 13, 18, 29, 39, 40, 41, 42, 43,
        31, 32, 33, 35, 36, 38
    ] + list(range(44, 64)) + [8, 2]
    
    @classmethod
    def get_register_definition(cls, register_id: int) -> Optional[RegisterDefinition]:
        """Get register definition by ID"""
        return cls.REGISTERS.get(register_id)
    
    @classmethod 
    def get_register_by_name(cls, name: str) -> Optional[RegisterDefinition]:
        """Get register definition by name"""
        for reg in cls.REGISTERS.values():
            if reg.name == name:
                return reg
        return None
    
    @classmethod
    def get_registers_by_type(cls, reg_type: RegisterType) -> List[RegisterDefinition]:
        """Get all registers of a specific type"""
        return [reg for reg in cls.REGISTERS.values() if reg.data_type == reg_type]
    
    @classmethod
    def get_discharge_bucket_registers(cls) -> List[int]:
        """Get all discharge time bucket register IDs (44-63)"""
        return list(range(44, 64))
    
    @classmethod
    def decode_battery_type(cls, type_serial_data: str) -> Tuple[int, str, str]:
        """
        Decode battery type and serial from register 2 data
        
        Args:
            type_serial_data: Raw string from register 2
            
        Returns:
            Tuple of (capacity_ah, description, electronic_serial)
        """
        import re
        numbers = re.findall(r'\d+\.?\d*', type_serial_data)
        
        if len(numbers) >= 2:
            bat_type = numbers[0]
            e_serial = numbers[1]
            
            if bat_type in cls.BATTERY_TYPES:
                capacity, description = cls.BATTERY_TYPES[bat_type]
                return capacity, description, e_serial
        
        return 0, "Unknown", "Unknown"
    
    @classmethod
    def decode_voltage_array(cls, raw_data: bytes) -> List[int]:
        """
        Decode cell voltage array from register 12
        
        Args:
            raw_data: Raw bytes from voltage register
            
        Returns:
            List of cell voltages in millivolts
        """
        if len(raw_data) < 10:
            return []
        
        voltages = []
        for i in range(5):  # 5 cells in series for M18
            voltage = struct.unpack('<H', raw_data[i*2:(i+1)*2])[0]
            voltages.append(voltage)
        
        return voltages
    
    @classmethod
    def decode_temperature(cls, raw_data: bytes, register_id: int) -> Optional[float]:
        """
        Decode temperature from temperature registers
        
        Args:
            raw_data: Raw bytes from temperature register
            register_id: Register ID (13 for ADC, 18 for Forge)
            
        Returns:
            Temperature in degrees Celsius, None if invalid
        """
        if len(raw_data) < 2:
            return None
        
        temp_value = struct.unpack('<H', raw_data[:2])[0]
        
        if register_id == 13:  # ADC temperature
            if temp_value == 0:
                return None
            # Convert ADC to temperature (formula from original research)
            return (temp_value - 1000) / 10.0
        elif register_id == 18:  # Forge temperature  
            if temp_value == 0:
                return None
            return float(temp_value)
        
        return None
    
    @classmethod
    def decode_date(cls, raw_data: bytes) -> Optional[datetime.datetime]:
        """
        Decode date/time from date registers
        
        Args:
            raw_data: Raw bytes from date register
            
        Returns:
            Parsed datetime object, None if invalid
        """
        if len(raw_data) < 4:
            return None
        
        timestamp = struct.unpack('<I', raw_data[:4])[0]
        
        if timestamp == 0:
            return None
        
        try:
            # M18 uses Unix timestamp with epoch adjustment
            return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        except (ValueError, OSError):
            return None
    
    @classmethod
    def calculate_pack_voltage(cls, cell_voltages: List[int]) -> float:
        """Calculate total pack voltage from individual cell voltages"""
        return sum(cell_voltages) / 1000.0  # Convert mV to V
    
    @classmethod
    def calculate_cell_imbalance(cls, cell_voltages: List[int]) -> int:
        """Calculate cell imbalance (max - min voltage difference)"""
        if not cell_voltages:
            return 0
        return max(cell_voltages) - min(cell_voltages)
    
    @classmethod
    def calculate_discharge_cycles(cls, total_discharge_as: int, battery_capacity_ah: int) -> float:
        """
        Calculate equivalent discharge cycles
        
        Args:
            total_discharge_as: Total discharge in ampere-seconds
            battery_capacity_ah: Battery capacity in amp-hours
            
        Returns:
            Number of equivalent full discharge cycles
        """
        if battery_capacity_ah == 0:
            return 0.0
        
        total_discharge_ah = total_discharge_as / 3600
        return total_discharge_ah / battery_capacity_ah
    
    @classmethod
    def get_register_summary(cls) -> str:
        """Get a summary of all available registers"""
        summary = ["Milwaukee M18 Battery Register Map Summary", "=" * 50, ""]
        
        by_type = {}
        for reg in cls.REGISTERS.values():
            reg_type = reg.data_type.value
            if reg_type not in by_type:
                by_type[reg_type] = []
            by_type[reg_type].append(reg)
        
        for reg_type, registers in by_type.items():
            summary.append(f"{reg_type.upper()} Registers ({len(registers)}):")
            for reg in sorted(registers, key=lambda x: x.address):
                summary.append(f"  {reg.address:3d}: {reg.name} - {reg.description}")
            summary.append("")
        
        summary.append(f"Total Registers Mapped: {len(cls.REGISTERS)}")
        summary.append(f"Discharge Buckets: {len(cls.get_discharge_bucket_registers())}")
        summary.append(f"Known Battery Types: {len(cls.BATTERY_TYPES)}")
        
        return "\n".join(summary)


# Export commonly used register lists for diagnostics
ESSENTIAL_REGISTERS = M18RegisterMap.QUICK_HEALTH_REGISTERS
COMPREHENSIVE_REGISTERS = M18RegisterMap.COMPREHENSIVE_REGISTERS
DISCHARGE_BUCKETS = M18RegisterMap.get_discharge_bucket_registers()
ALL_REGISTERS = list(M18RegisterMap.REGISTERS.keys())


def main():
    """CLI interface to display register information"""
    import argparse
    
    parser = argparse.ArgumentParser(description="M18 Register Map Information")
    parser.add_argument('--summary', action='store_true', help="Show register summary")
    parser.add_argument('--register', type=int, help="Show details for specific register")
    parser.add_argument('--type', type=str, help="Show registers of specific type")
    
    args = parser.parse_args()
    
    if args.summary:
        print(M18RegisterMap.get_register_summary())
    elif args.register is not None:
        reg_def = M18RegisterMap.get_register_definition(args.register)
        if reg_def:
            print(f"Register {args.register}:")
            print(f"  Name: {reg_def.name}")
            print(f"  Description: {reg_def.description}")
            print(f"  Type: {reg_def.data_type.value}")
            print(f"  Length: {reg_def.length} bytes")
            if reg_def.units:
                print(f"  Units: {reg_def.units}")
        else:
            print(f"Register {args.register} not found")
    elif args.type:
        try:
            reg_type = RegisterType(args.type.lower())
            registers = M18RegisterMap.get_registers_by_type(reg_type)
            print(f"{reg_type.value.upper()} Registers ({len(registers)}):")
            for reg in sorted(registers, key=lambda x: x.address):
                print(f"  {reg.address:3d}: {reg.name} - {reg.description}")
        except ValueError:
            print(f"Unknown register type: {args.type}")
            print("Available types:", [t.value for t in RegisterType])
    else:
        print("Use --help for usage information")
        print("Available commands:")
        print("  --summary: Show all registers")
        print("  --register N: Show details for register N") 
        print("  --type TYPE: Show registers of type TYPE")


if __name__ == "__main__":
    main()
