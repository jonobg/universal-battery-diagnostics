#!/usr/bin/env python3
"""
Abstract base classes for battery protocol interfaces.
Provides standardized API for all manufacturer implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class ProtocolType(Enum):
    """Communication protocol types"""
    UART_CUSTOM = "uart_custom"
    UART_STANDARD = "uart_standard" 
    SMBUS_STANDARD = "smbus_standard"
    I2C_BASIC = "i2c_basic"
    SPI_BASIC = "spi_basic"
    BLUETOOTH_LE = "bluetooth_le"


class BatteryState(Enum):
    """Battery connection states"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    COMMUNICATING = "communicating"
    ERROR = "error"


@dataclass
class RegisterDefinition:
    """Definition of a battery register"""
    address: int
    name: str
    description: str
    data_type: str  # uint8, uint16, uint32, int8, int16, int32, float, array
    unit: Optional[str] = None
    multiplier: float = 1.0
    offset: float = 0.0
    read_only: bool = True
    array_length: Optional[int] = None


@dataclass
class BatteryDiagnostics:
    """Complete diagnostic data from a battery"""
    battery_id: str
    manufacturer: str
    model: str
    timestamp: float
    raw_data: bytes
    parsed_registers: Dict[int, Any]
    health_metrics: Dict[str, Any]
    communication_stats: Dict[str, Any]


@dataclass
class CommunicationStats:
    """Statistics about communication session"""
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    session_duration: float = 0.0
    error_messages: List[str] = None


class BatteryProtocol(ABC):
    """
    Abstract base class for battery communication protocols.
    All manufacturer-specific implementations must inherit from this class.
    """
    
    def __init__(self, connection_string: str, config: Dict[str, Any] = None):
        self.connection_string = connection_string
        self.config = config or {}
        self.state = BatteryState.DISCONNECTED
        self.communication_stats = CommunicationStats()
        self._connection_handle = None
        self._last_error: Optional[str] = None
        
    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        """Return the protocol type this implementation uses"""
        pass
        
    @property
    @abstractmethod 
    def manufacturer(self) -> str:
        """Return manufacturer name (e.g., 'Milwaukee', 'Makita')"""
        pass
        
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported battery models"""
        pass
        
    @abstractmethod
    def get_register_map(self) -> Dict[int, RegisterDefinition]:
        """Return complete register map for this protocol"""
        pass
        
    # Connection Management
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to battery.
        Returns True if successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to battery.
        Returns True if successful, False otherwise.
        """
        pass
        
    def is_connected(self) -> bool:
        """Check if currently connected to battery"""
        return self.state in [BatteryState.CONNECTED, BatteryState.COMMUNICATING]
        
    # Core Communication
    @abstractmethod
    def read_register(self, register_address: int) -> Optional[Any]:
        """
        Read single register value.
        Returns parsed value or None if failed.
        """
        pass
        
    @abstractmethod
    def read_multiple_registers(self, register_addresses: List[int]) -> Dict[int, Any]:
        """
        Read multiple registers efficiently.
        Returns dict mapping register_address -> value
        """
        pass
        
    @abstractmethod
    def write_register(self, register_address: int, value: Any) -> bool:
        """
        Write to register (if supported).
        Returns True if successful, False otherwise.
        """
        pass
        
    # High-Level Operations  
    def read_diagnostics(self) -> Optional[BatteryDiagnostics]:
        """
        Read complete diagnostic data from battery.
        This is the main method called by analysis tools.
        """
        if not self.is_connected():
            self._last_error = "Not connected to battery"
            return None
            
        start_time = time.time()
        self.state = BatteryState.COMMUNICATING
        
        try:
            # Get register map
            register_map = self.get_register_map()
            
            # Read all registers
            register_addresses = list(register_map.keys())
            raw_registers = self.read_multiple_registers(register_addresses)
            
            # Parse register values using definitions
            parsed_registers = {}
            for addr, raw_value in raw_registers.items():
                if addr in register_map:
                    reg_def = register_map[addr]
                    parsed_value = self._parse_register_value(raw_value, reg_def)
                    parsed_registers[addr] = parsed_value
                    
            # Calculate basic health metrics
            health_metrics = self._calculate_health_metrics(parsed_registers)
            
            # Generate diagnostics object
            diagnostics = BatteryDiagnostics(
                battery_id=self._generate_battery_id(parsed_registers),
                manufacturer=self.manufacturer,
                model=self._detect_model(parsed_registers),
                timestamp=time.time(),
                raw_data=self._serialize_raw_data(raw_registers),
                parsed_registers=parsed_registers,
                health_metrics=health_metrics,
                communication_stats=self.communication_stats.__dict__.copy()
            )
            
            self.state = BatteryState.CONNECTED
            return diagnostics
            
        except Exception as e:
            self._last_error = f"Diagnostic read failed: {str(e)}"
            self.state = BatteryState.ERROR
            return None
        finally:
            self.communication_stats.session_duration = time.time() - start_time
            
    # Protocol-Specific Implementations (can be overridden)
    def _parse_register_value(self, raw_value: Any, reg_def: RegisterDefinition) -> Any:
        """Parse raw register value using register definition"""
        if raw_value is None:
            return None
            
        # Apply data type conversion
        if reg_def.data_type == "uint8":
            value = int(raw_value) & 0xFF
        elif reg_def.data_type == "uint16":
            value = int(raw_value) & 0xFFFF  
        elif reg_def.data_type == "uint32":
            value = int(raw_value) & 0xFFFFFFFF
        elif reg_def.data_type == "int8":
            value = int(raw_value)
            if value > 127: value -= 256
        elif reg_def.data_type == "int16": 
            value = int(raw_value)
            if value > 32767: value -= 65536
        elif reg_def.data_type == "float":
            value = float(raw_value)
        else:
            value = raw_value
            
        # Apply scaling
        if isinstance(value, (int, float)):
            value = (value * reg_def.multiplier) + reg_def.offset
            
        return value
        
    def _calculate_health_metrics(self, registers: Dict[int, Any]) -> Dict[str, Any]:
        """Calculate basic health metrics from register values"""
        # Override in manufacturer-specific classes for detailed calculations
        return {
            "timestamp": time.time(),
            "communication_quality": self._calculate_communication_quality(),
            "register_count": len(registers),
        }
        
    def _calculate_communication_quality(self) -> float:
        """Calculate communication quality percentage"""
        stats = self.communication_stats
        if stats.total_commands == 0:
            return 0.0
        return (stats.successful_commands / stats.total_commands) * 100.0
        
    def _generate_battery_id(self, registers: Dict[int, Any]) -> str:
        """Generate unique battery ID from registers"""
        # Override in manufacturer classes for proper ID extraction
        return f"{self.manufacturer}_{int(time.time())}"
        
    def _detect_model(self, registers: Dict[int, Any]) -> str:
        """Detect battery model from register data"""
        # Override in manufacturer classes for model detection
        return "Unknown"
        
    def _serialize_raw_data(self, raw_registers: Dict[int, Any]) -> bytes:
        """Serialize raw register data to bytes"""
        # Simple serialization - can be overridden
        data = []
        for addr in sorted(raw_registers.keys()):
            value = raw_registers[addr]
            if isinstance(value, int):
                data.extend(value.to_bytes(2, 'little', signed=False))
            elif isinstance(value, list):
                for item in value:
                    data.extend(int(item).to_bytes(2, 'little', signed=False))
        return bytes(data)
        
    # Error Handling
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self._last_error
        
    def clear_error(self):
        """Clear error state"""
        self._last_error = None
        if self.state == BatteryState.ERROR:
            self.state = BatteryState.DISCONNECTED
            
    # Utility Methods
    def test_connection(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Test connection and return diagnostic info.
        Returns (success, test_results)
        """
        test_results = {
            "connection_test": False,
            "register_read_test": False,
            "communication_speed": 0.0,
            "error_rate": 0.0,
        }
        
        # Test connection
        if not self.connect():
            return False, test_results
            
        test_results["connection_test"] = True
        
        # Test register reading
        register_map = self.get_register_map()
        if register_map:
            test_addr = next(iter(register_map.keys()))
            start_time = time.time()
            value = self.read_register(test_addr)
            test_results["communication_speed"] = time.time() - start_time
            test_results["register_read_test"] = value is not None
            
        # Calculate error rate
        stats = self.communication_stats
        if stats.total_commands > 0:
            test_results["error_rate"] = (stats.failed_commands / stats.total_commands) * 100.0
            
        return test_results["register_read_test"], test_results
        
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.manufacturer}, {self.connection_string})"
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(connection='{self.connection_string}', state={self.state.value})"