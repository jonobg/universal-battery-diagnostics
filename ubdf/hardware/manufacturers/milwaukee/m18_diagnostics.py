#!/usr/bin/env python3
"""
Milwaukee M18 Battery Advanced Diagnostics
Integrated from mnh-jansson/m18-protocol research

Provides comprehensive battery health analysis, usage analytics, and diagnostics
with support for all M18 battery types and detailed reporting capabilities.
"""

import datetime
import struct
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

from .m18_protocol_core import M18Protocol, M18ProtocolError
from .m18_registers import M18RegisterMap, RegisterType, COMPREHENSIVE_REGISTERS, DISCHARGE_BUCKETS


@dataclass
class BatteryIdentification:
    """Battery identification and manufacturing information"""
    battery_type: str
    electronic_serial: str
    capacity_ah: int
    description: str
    manufacture_date: Optional[datetime.datetime]
    days_since_first_charge: Optional[int]


@dataclass
class VoltageMetrics:
    """Battery voltage and electrical measurements"""
    pack_voltage: float
    cell_voltages: List[int]  # mV
    cell_imbalance: int  # mV
    min_cell_voltage: int  # mV
    max_cell_voltage: int  # mV


@dataclass
class TemperatureMetrics:
    """Temperature measurements from available sensors"""
    temperature_adc: Optional[float]  # °C
    temperature_forge: Optional[float]  # °C
    has_temperature_data: bool


@dataclass
class ChargingStatistics:
    """Comprehensive charging behavior statistics"""
    redlink_charge_count: int
    dumb_charge_count: int
    total_charge_count: int
    total_charge_time: int  # seconds
    charger_idle_time: int  # seconds
    low_voltage_charges: int
    days_since_last_charge: Optional[int]


@dataclass
class UsageStatistics:
    """Battery usage and discharge analytics"""
    total_discharge_ah: float
    total_discharge_cycles: float
    discharge_to_empty_count: int
    days_since_tool_use: Optional[int]
    total_tool_time: int  # seconds (>10A usage)
    discharge_time_buckets: Dict[str, int]  # Current range -> seconds


@dataclass
class HealthMetrics:
    """Battery health and safety event counters"""
    overheat_events: int
    overcurrent_events: int
    low_voltage_events: int
    low_voltage_bounce: int
    health_score: float  # 0-100%
    warnings: List[str]


@dataclass
class M18BatteryReport:
    """Comprehensive M18 battery diagnostic report"""
    identification: BatteryIdentification
    voltage_metrics: VoltageMetrics
    temperature_metrics: TemperatureMetrics
    charging_stats: ChargingStatistics
    usage_stats: UsageStatistics
    health_metrics: HealthMetrics
    system_date: Optional[datetime.datetime]
    report_timestamp: datetime.datetime


class M18Diagnostics:
    """
    Advanced M18 battery diagnostics and health analysis
    
    Provides comprehensive battery analysis including:
    - Complete health reporting with safety event tracking
    - Usage analytics with current-based discharge analysis
    - Charging behavior analysis and cycle counting
    - Temperature monitoring and thermal health assessment
    - Voltage monitoring with cell balance analysis
    """
    
    def __init__(self, protocol: M18Protocol):
        """Initialize diagnostics with M18 protocol instance"""
        self.protocol = protocol
        self.logger = logging.getLogger(__name__)
        
        # Health scoring thresholds
        self.health_thresholds = {
            'cell_imbalance_warning': 100,  # mV
            'cell_imbalance_critical': 200,  # mV
            'overheat_warning': 5,
            'overcurrent_warning': 10,
            'low_voltage_warning': 20,
            'cycle_count_warning': 500,
            'cycle_count_critical': 1000
        }
    
    def read_register_data(self, register_list: List[int], 
                          force_refresh: bool = False) -> Dict[int, Any]:
        """
        Read and decode data from multiple registers
        
        Args:
            register_list: List of register IDs to read
            force_refresh: Force fresh read from battery
            
        Returns:
            Dictionary mapping register IDs to decoded values
        """
        decoded_data = {}
        
        # Save debug state and disable for bulk reading
        self.protocol.save_and_set_debug(False)
        
        try:
            for reg_id in register_list:
                reg_def = M18RegisterMap.get_register_definition(reg_id)
                if not reg_def:
                    continue
                
                try:
                    # Read raw data from battery
                    response = self.protocol.read_register(
                        (reg_id >> 8) & 0xFF,  # High byte
                        reg_id & 0xFF,         # Low byte
                        reg_def.length
                    )
                    
                    # Extract payload (skip header and checksum)
                    if len(response) >= reg_def.length + 5:
                        raw_data = response[3:3+reg_def.length]
                        decoded_value = self._decode_register_value(reg_def, raw_data)
                        decoded_data[reg_id] = decoded_value
                    
                except Exception as e:
                    self.logger.warning(f"Failed to read register {reg_id}: {e}")
                    decoded_data[reg_id] = None
        
        finally:
            self.protocol.restore_debug()
        
        return decoded_data
    
    def _decode_register_value(self, reg_def, raw_data: bytes) -> Any:
        """Decode raw register data based on register type"""
        if reg_def.data_type == RegisterType.DATE:
            return M18RegisterMap.decode_date(raw_data)
        elif reg_def.data_type == RegisterType.VOLTAGE_ARRAY:
            return M18RegisterMap.decode_voltage_array(raw_data)
        elif reg_def.data_type == RegisterType.TEMPERATURE:
            return M18RegisterMap.decode_temperature(raw_data, reg_def.address)
        elif reg_def.data_type == RegisterType.ASCII:
            return raw_data.decode('ascii', errors='ignore').strip('\x00')
        elif reg_def.data_type == RegisterType.UINT16:
            return struct.unpack('<H', raw_data[:2])[0] if len(raw_data) >= 2 else 0
        elif reg_def.data_type == RegisterType.UINT32:
            return struct.unpack('<I', raw_data[:4])[0] if len(raw_data) >= 4 else 0
        elif reg_def.data_type == RegisterType.UINT8:
            return raw_data[0] if len(raw_data) >= 1 else 0
        else:
            return raw_data
    
    def get_battery_identification(self, register_data: Dict[int, Any]) -> BatteryIdentification:
        """Extract battery identification information"""
        type_serial = register_data.get(2, "")
        capacity, description, e_serial = M18RegisterMap.decode_battery_type(str(type_serial))
        
        # Extract battery type from serial data
        numbers = re.findall(r'\d+\.?\d*', str(type_serial))
        battery_type = numbers[0] if numbers else "Unknown"
        
        return BatteryIdentification(
            battery_type=battery_type,
            electronic_serial=e_serial,
            capacity_ah=capacity,
            description=description,
            manufacture_date=register_data.get(0),
            days_since_first_charge=register_data.get(1)
        )
    
    def get_voltage_metrics(self, register_data: Dict[int, Any]) -> VoltageMetrics:
        """Extract voltage measurements and calculate metrics"""
        cell_voltages = register_data.get(12, [])
        if not cell_voltages:
            cell_voltages = [0] * 5
        
        pack_voltage = M18RegisterMap.calculate_pack_voltage(cell_voltages)
        cell_imbalance = M18RegisterMap.calculate_cell_imbalance(cell_voltages)
        
        return VoltageMetrics(
            pack_voltage=pack_voltage,
            cell_voltages=cell_voltages,
            cell_imbalance=cell_imbalance,
            min_cell_voltage=min(cell_voltages) if cell_voltages else 0,
            max_cell_voltage=max(cell_voltages) if cell_voltages else 0
        )
    
    def get_temperature_metrics(self, register_data: Dict[int, Any]) -> TemperatureMetrics:
        """Extract temperature measurements from available sensors"""
        temp_adc = register_data.get(13)
        temp_forge = register_data.get(18)
        
        return TemperatureMetrics(
            temperature_adc=temp_adc,
            temperature_forge=temp_forge,
            has_temperature_data=temp_adc is not None or temp_forge is not None
        )
    
    def get_charging_statistics(self, register_data: Dict[int, Any]) -> ChargingStatistics:
        """Extract comprehensive charging statistics"""
        return ChargingStatistics(
            redlink_charge_count=register_data.get(31, 0),
            dumb_charge_count=register_data.get(32, 0),
            total_charge_count=register_data.get(33, 0),
            total_charge_time=register_data.get(35, 0),
            charger_idle_time=register_data.get(36, 0),
            low_voltage_charges=register_data.get(38, 0),
            days_since_last_charge=register_data.get(26)
        )
    
    def get_usage_statistics(self, register_data: Dict[int, Any], 
                           battery_capacity: int) -> UsageStatistics:
        """Extract usage statistics and discharge analytics"""
        total_discharge_as = register_data.get(29, 0)
        total_discharge_ah = total_discharge_as / 3600
        
        # Calculate discharge cycles
        total_cycles = M18RegisterMap.calculate_discharge_cycles(
            total_discharge_as, battery_capacity
        )
        
        # Build discharge time buckets
        discharge_buckets = {}
        total_tool_time = 0
        
        for i, reg_id in enumerate(DISCHARGE_BUCKETS):
            bucket_time = register_data.get(reg_id, 0)
            total_tool_time += bucket_time
            
            if i < 19:  # 10A-200A buckets
                amp_range = f"{(i+1)*10}-{(i+2)*10}A"
            else:  # >200A bucket
                amp_range = ">200A"
            
            discharge_buckets[amp_range] = bucket_time
        
        return UsageStatistics(
            total_discharge_ah=total_discharge_ah,
            total_discharge_cycles=total_cycles,
            discharge_to_empty_count=register_data.get(39, 0),
            days_since_tool_use=register_data.get(25),
            total_tool_time=total_tool_time,
            discharge_time_buckets=discharge_buckets
        )
    
    def get_health_metrics(self, register_data: Dict[int, Any],
                          voltage_metrics: VoltageMetrics,
                          usage_stats: UsageStatistics) -> HealthMetrics:
        """Calculate comprehensive health metrics and warnings"""
        warnings = []
        health_score = 100.0
        
        # Extract safety event counts
        overheat = register_data.get(40, 0)
        overcurrent = register_data.get(41, 0) 
        low_voltage = register_data.get(42, 0)
        low_voltage_bounce = register_data.get(43, 0)
        
        # Analyze cell imbalance
        if voltage_metrics.cell_imbalance > self.health_thresholds['cell_imbalance_critical']:
            warnings.append("Critical cell imbalance detected")
            health_score -= 30
        elif voltage_metrics.cell_imbalance > self.health_thresholds['cell_imbalance_warning']:
            warnings.append("Cell imbalance warning")
            health_score -= 10
        
        # Analyze safety events
        if overheat > self.health_thresholds['overheat_warning']:
            warnings.append(f"Excessive overheat events: {overheat}")
            health_score -= min(20, overheat * 2)
        
        if overcurrent > self.health_thresholds['overcurrent_warning']:
            warnings.append(f"Excessive overcurrent events: {overcurrent}")
            health_score -= min(15, overcurrent * 1.5)
        
        if low_voltage > self.health_thresholds['low_voltage_warning']:
            warnings.append(f"Excessive low voltage events: {low_voltage}")
            health_score -= min(25, low_voltage * 1.2)
        
        # Analyze cycle count
        if usage_stats.total_discharge_cycles > self.health_thresholds['cycle_count_critical']:
            warnings.append("Battery nearing end of life (high cycle count)")
            health_score -= 40
        elif usage_stats.total_discharge_cycles > self.health_thresholds['cycle_count_warning']:
            warnings.append("High cycle count - monitor battery health")
            health_score -= 15
        
        # Check for low cell voltages
        if any(v < 3000 for v in voltage_metrics.cell_voltages if v > 0):
            warnings.append("Low cell voltage detected")
            health_score -= 20
        
        health_score = max(0.0, health_score)
        
        return HealthMetrics(
            overheat_events=overheat,
            overcurrent_events=overcurrent,
            low_voltage_events=low_voltage,
            low_voltage_bounce=low_voltage_bounce,
            health_score=health_score,
            warnings=warnings
        )
    
    def generate_comprehensive_report(self, force_refresh: bool = False) -> M18BatteryReport:
        """
        Generate comprehensive battery diagnostic report
        
        Args:
            force_refresh: Force fresh read from battery
            
        Returns:
            Complete diagnostic report with all metrics
        """
        self.logger.info("Generating comprehensive M18 battery report...")
        
        # Read all required registers
        register_data = self.read_register_data(COMPREHENSIVE_REGISTERS, force_refresh)
        
        # Extract identification first to get battery capacity
        identification = self.get_battery_identification(register_data)
        
        # Extract all metrics
        voltage_metrics = self.get_voltage_metrics(register_data)
        temperature_metrics = self.get_temperature_metrics(register_data)
        charging_stats = self.get_charging_statistics(register_data)
        usage_stats = self.get_usage_statistics(register_data, identification.capacity_ah)
        health_metrics = self.get_health_metrics(register_data, voltage_metrics, usage_stats)
        
        return M18BatteryReport(
            identification=identification,
            voltage_metrics=voltage_metrics,
            temperature_metrics=temperature_metrics,
            charging_stats=charging_stats,
            usage_stats=usage_stats,
            health_metrics=health_metrics,
            system_date=register_data.get(8),
            report_timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
    
    def print_health_summary(self, report: M18BatteryReport):
        """Print formatted health summary to console"""
        print("\n" + "="*60)
        print("M18 BATTERY HEALTH SUMMARY")
        print("="*60)
        
        # Battery identification
        print(f"Type: {report.identification.battery_type} [{report.identification.description}]")
        print(f"Electronic Serial: {report.identification.electronic_serial}")
        if report.identification.manufacture_date:
            print(f"Manufactured: {report.identification.manufacture_date.strftime('%Y-%m-%d')}")
        
        # Health score and warnings
        print(f"\nHealth Score: {report.health_metrics.health_score:.1f}%")
        if report.health_metrics.warnings:
            print("WARNINGS:")
            for warning in report.health_metrics.warnings:
                print(f"  ⚠ {warning}")
        
        # Current status
        print(f"\nCurrent Status:")
        print(f"  Pack Voltage: {report.voltage_metrics.pack_voltage:.2f}V")
        print(f"  Cell Voltages: {report.voltage_metrics.cell_voltages} mV")
        print(f"  Cell Imbalance: {report.voltage_metrics.cell_imbalance} mV")
        
        if report.temperature_metrics.has_temperature_data:
            if report.temperature_metrics.temperature_adc:
                print(f"  Temperature: {report.temperature_metrics.temperature_adc:.1f}°C")
            if report.temperature_metrics.temperature_forge:
                print(f"  Forge Temperature: {report.temperature_metrics.temperature_forge:.1f}°C")
        
        # Usage statistics
        print(f"\nUsage Statistics:")
        print(f"  Total Discharge: {report.usage_stats.total_discharge_ah:.2f} Ah")
        print(f"  Discharge Cycles: {report.usage_stats.total_discharge_cycles:.1f}")
        print(f"  Empty Discharges: {report.usage_stats.discharge_to_empty_count}")
        print(f"  Tool Time (>10A): {datetime.timedelta(seconds=report.usage_stats.total_tool_time)}")
        
        # Charging statistics  
        print(f"\nCharging Statistics:")
        print(f"  Total Charges: {report.charging_stats.total_charge_count} " +
              f"[RedLink: {report.charging_stats.redlink_charge_count}, " +
              f"Standard: {report.charging_stats.dumb_charge_count}]")
        print(f"  Charge Time: {datetime.timedelta(seconds=report.charging_stats.total_charge_time)}")
        print(f"  Low Voltage Charges: {report.charging_stats.low_voltage_charges}")
        
        # Safety events
        safety_total = (report.health_metrics.overheat_events + 
                       report.health_metrics.overcurrent_events +
                       report.health_metrics.low_voltage_events)
        print(f"\nSafety Events: {safety_total} total")
        if safety_total > 0:
            print(f"  Overheats: {report.health_metrics.overheat_events}")
            print(f"  Overcurrents: {report.health_metrics.overcurrent_events}")
            print(f"  Low Voltage: {report.health_metrics.low_voltage_events}")
    
    def export_report_json(self, report: M18BatteryReport) -> str:
        """Export report as JSON string"""
        import json
        
        def datetime_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(asdict(report), indent=2, default=datetime_serializer)


def main():
    """CLI interface for M18 diagnostics"""
    import argparse
    
    parser = argparse.ArgumentParser(description="M18 Battery Diagnostics")
    parser.add_argument('--port', type=str, help="Serial port (e.g., COM5)")
    parser.add_argument('--health', action='store_true', help="Generate health report")
    parser.add_argument('--json', action='store_true', help="Output JSON format")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
    
    try:
        with M18Protocol(port=args.port) as protocol:
            diagnostics = M18Diagnostics(protocol)
            
            if args.health:
                report = diagnostics.generate_comprehensive_report()
                
                if args.json:
                    print(diagnostics.export_report_json(report))
                else:
                    diagnostics.print_health_summary(report)
            else:
                print("M18 Diagnostics initialized. Use --health for battery analysis.")
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
