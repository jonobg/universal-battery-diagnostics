#!/usr/bin/env python3
"""
Milwaukee M18 Battery Diagnostics Package
Integrated from mnh-jansson/m18-protocol research

Comprehensive Milwaukee M18 battery analysis and diagnostics including:
- Low-level protocol communication with charger simulation
- Complete register mapping for 184 battery data points  
- Advanced health diagnostics and usage analytics
- Support for all M18 battery types (CP, XC, HO, Forge)
"""

from .m18_protocol_core import M18Protocol, M18ProtocolError
from .m18_registers import (
    M18RegisterMap, 
    RegisterType,
    RegisterDefinition,
    ESSENTIAL_REGISTERS,
    COMPREHENSIVE_REGISTERS,
    DISCHARGE_BUCKETS,
    ALL_REGISTERS
)
from .m18_diagnostics import (
    M18Diagnostics,
    M18BatteryReport,
    BatteryIdentification,
    VoltageMetrics,
    TemperatureMetrics,
    ChargingStatistics,
    UsageStatistics,
    HealthMetrics
)

__version__ = "1.0.0"
__author__ = "Integrated from mnh-jansson/m18-protocol"

# Export main classes for easy import
__all__ = [
    # Core protocol
    'M18Protocol',
    'M18ProtocolError',
    
    # Register mapping
    'M18RegisterMap',
    'RegisterType', 
    'RegisterDefinition',
    
    # Register lists
    'ESSENTIAL_REGISTERS',
    'COMPREHENSIVE_REGISTERS',
    'DISCHARGE_BUCKETS',
    'ALL_REGISTERS',
    
    # Diagnostics
    'M18Diagnostics',
    'M18BatteryReport',
    
    # Data structures
    'BatteryIdentification',
    'VoltageMetrics',
    'TemperatureMetrics',
    'ChargingStatistics',
    'UsageStatistics',
    'HealthMetrics'
]


def create_m18_diagnostics(port: str = None) -> M18Diagnostics:
    """
    Convenience function to create M18 diagnostics interface
    
    Args:
        port: Serial port for M18 communication
        
    Returns:
        Initialized M18Diagnostics instance
    """
    protocol = M18Protocol(port=port)
    return M18Diagnostics(protocol)


def quick_health_check(port: str = None) -> M18BatteryReport:
    """
    Perform quick M18 battery health check
    
    Args:
        port: Serial port for M18 communication
        
    Returns:
        Complete battery diagnostic report
    """
    with M18Protocol(port=port) as protocol:
        diagnostics = M18Diagnostics(protocol)
        return diagnostics.generate_comprehensive_report()


def supported_battery_types():
    """Get dictionary of supported M18 battery types"""
    return M18RegisterMap.BATTERY_TYPES.copy()


def get_package_info():
    """Get package information"""
    return {
        'name': 'Milwaukee M18 Diagnostics',
        'version': __version__,
        'author': __author__,
        'description': 'Comprehensive M18 battery analysis and diagnostics',
        'registers_mapped': len(M18RegisterMap.REGISTERS),
        'battery_types_supported': len(M18RegisterMap.BATTERY_TYPES),
        'features': [
            'Complete register mapping (184 data points)',
            'Advanced health diagnostics with safety event tracking', 
            'Usage analytics with current-based discharge buckets',
            'Charging behavior analysis and cycle counting',
            'Temperature monitoring and thermal health assessment',
            'Cell voltage monitoring with imbalance detection',
            'Charger simulation for communication testing'
        ]
    }


# Package-level constants
M18_BATTERY_VOLTAGE = 18.0  # Nominal voltage
M18_CELL_COUNT = 5  # 5 cells in series
M18_CELL_NOMINAL_VOLTAGE = 3.6  # Nominal cell voltage
