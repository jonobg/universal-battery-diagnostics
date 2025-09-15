# Universal Battery Diagnostics Framework (UBDF)

A comprehensive, production-ready framework for battery health analysis, diagnostics, and visualization across multiple manufacturers and protocols. Integrates cutting-edge research from Milwaukee M18, Makita NEC 78K0, and Arduino-based diagnostic systems.

## 🔋 Comprehensive Manufacturer Support

### Milwaukee M18 Series - Complete Integration
- **All Battery Types**: CP (Compact), XC (Extended), HO (High Output), Forge series
- **184 Register Mapping**: Complete protocol reverse-engineering with full parameter documentation
- **Advanced Diagnostics**: Health scoring, usage analytics, safety event tracking
- **RedLink Protocol**: Charger simulation and communication protocol support
- **Current Analysis**: 20-bucket discharge current analysis (10A-200A+)

### Makita Battery Systems
- **NEC 78K0 MCU**: Complete firmware recovery and programming utility
- **Hardware Interface**: Arduino-based temperature monitoring and diagnostics
- **OneWire Protocol**: Comprehensive communication and sensor integration

### Extensible Architecture
- **Configuration-Driven**: YAML-based manufacturer profiles
- **Modular Design**: Pluggable diagnostic modules and hardware interfaces
- **Research Integration**: Direct incorporation of community battery research

## 🚀 Key Features

### Advanced Health Analysis
- **Multi-Factor Scoring**: Voltage, temperature, usage, and safety event analysis
- **Predictive Analytics**: Machine learning-powered degradation prediction
- **Safety Monitoring**: Overheat, overcurrent, and low-voltage event tracking
- **Cell Balancing**: Individual cell voltage monitoring with imbalance detection

### Professional Diagnostic Capabilities
- **Usage Intelligence**: Comprehensive discharge current bucket analysis
- **Charging Analytics**: RedLink vs standard charger usage tracking
- **Lifecycle Management**: Charge cycle counting and capacity degradation analysis
- **Fleet Management**: Multi-battery tracking with comparative analytics

### Hardware Integration
- **UART Communication**: Direct serial protocol communication
- **Arduino Interface**: OneWire and modular sensor support
- **MCU Programming**: NEC 78K0 firmware recovery and programming
- **Adapter Profiles**: Configurable hardware adapter support

## 📦 Installation & Setup

### Quick Installation
```bash
# Clone the repository
git clone https://github.com/your-username/universal-battery-diagnostics.git
cd universal-battery-diagnostics

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Validate development environment
python scripts/setup_development.py
```

### Hardware Requirements
- **Serial Interface**: USB-to-UART adapter for direct battery communication
- **Arduino (Optional)**: For OneWire diagnostic modules
- **Windows/Linux**: Cross-platform Python 3.8+ support

## 🔧 Usage Examples

### Milwaukee M18 Comprehensive Diagnostics
```python
from ubdf.hardware.manufacturers.milwaukee import M18Diagnostics

# Initialize M18 diagnostics
m18 = M18Diagnostics(port='COM3')

# Run comprehensive health analysis
health = m18.comprehensive_health_analysis()
print(f"Battery Health Score: {health.overall_score}%")
print(f"Safety Events: {health.safety_events}")
print(f"Discharge Analysis: {health.usage_analytics}")

# Generate professional report
report = m18.generate_health_report()
report.export_pdf("battery_health_report.pdf")
```

### Makita Firmware Recovery
```python
from ubdf.hardware.manufacturers.makita import NEC78K0Flasher

# Initialize flasher
flasher = NEC78K0Flasher(port='COM3')

# Program firmware
result = flasher.program_firmware("firmware.hex")
if result.success:
    print("Firmware programming successful!")
    
# Verify programming
verification = flasher.verify_firmware("firmware.hex")
print(f"Verification: {verification.status}")
```

### Arduino Diagnostic Interface
```python
from ubdf.hardware import ArduinoInterface

# Initialize Arduino interface
arduino = ArduinoInterface(port='COM4')

# Run Makita temperature diagnostics
temp_result = arduino.makita_temperature_diagnostic()
print(f"Battery Temperature: {temp_result.temperature}°C")

# Execute modular diagnostics
diagnostics = arduino.run_comprehensive_diagnostics()
print(f"Diagnostic Results: {diagnostics.summary}")
```

## 🛠️ Command Line Interface

### Milwaukee M18 Commands
```bash
# Protocol operations
python -m ubdf.hardware.manufacturers.milwaukee.m18_protocol_core --port COM3 --scan
python -m ubdf.hardware.manufacturers.milwaukee.m18_protocol_core --port COM3 --read-all

# Advanced diagnostics
python -m ubdf.hardware.manufacturers.milwaukee.m18_diagnostics --port COM3 --health-report
python -m ubdf.hardware.manufacturers.milwaukee.m18_diagnostics --port COM3 --usage-analytics
```

### Makita NEC 78K0 Commands
```bash
# Firmware operations
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --list-ports
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --port COM3 --program firmware.hex
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --port COM3 --verify firmware.hex
```

### Arduino Interface Commands
```bash
# Hardware discovery
python -m ubdf.hardware.arduino_interface --discover-ports
python -m ubdf.hardware.arduino_interface --port COM4 --makita-temp
python -m ubdf.hardware.arduino_interface --port COM4 --run-diagnostics
```

## 📊 Supported Hardware

| Manufacturer | Platform | Protocol | Features | Status |
|-------------|----------|----------|----------|---------|
| Milwaukee | M18/M12 | UART Custom | 184 registers, health scoring, RedLink protocol | ✅ **Complete** |
| Makita | NEC 78K0 MCU | Serial Programming | Firmware recovery, hex programming, verification | ✅ **Complete** |
| Arduino OBI | OneWire | Custom Protocol | Temperature monitoring, modular diagnostics | ✅ **Complete** |
| Ryobi | ONE+ 18V | I2C/SMBus | Register mapping, health analysis | 📋 Framework Ready |

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (no hardware required)
pytest tests/integration/ -m "not hardware"

# Run hardware tests (requires physical batteries)
pytest tests/integration/ -m hardware
```

## Project Structure

```
ubdf/
├── hardware/           # Hardware communication protocols
│   ├── base/          # Abstract interfaces
│   └── manufacturers/ # Manufacturer-specific implementations
├── software/          # Data processing and analysis
│   ├── data_processing/
│   └── visualization/
├── core/              # Database and core functionality
└── cli/               # Command line interface

tests/                 # Test suite
configs/               # Configuration files
```

## Hardware Requirements

- UART-to-USB adapter for Milwaukee M18/M12 batteries
- Python 3.8+ with serial communication support
- Compatible battery diagnostic interface (varies by manufacturer)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See `CONTRIBUTING.md` for detailed guidelines.

## License

MIT License - see `LICENSE` file for details.

## Background

This project originated from reverse engineering Milwaukee M18 battery protocols, discovering 442 bytes of diagnostic data including health metrics, usage patterns, and environmental conditions. The framework extends this approach to support multiple battery manufacturers.