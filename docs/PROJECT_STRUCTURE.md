# Universal Battery Diagnostics Framework - Project Structure

## Directory Organization

```
universal-battery-diagnostics/
├── ubdf/                          # Core framework package
│   ├── __init__.py               # Main package initialization
│   ├── cli/                      # Command-line interfaces
│   ├── core/                     # Core diagnostic engine
│   ├── hardware/                 # Hardware interfaces and drivers
│   │   ├── arduino_interface.py  # Arduino-based hardware support
│   │   └── manufacturers/        # Manufacturer-specific modules
│   │       ├── makita/          # Makita battery support
│   │       │   └── nec78k0_flasher.py
│   │       └── milwaukee/       # Milwaukee M18 comprehensive support
│   │           ├── __init__.py
│   │           ├── m18_protocol_core.py
│   │           ├── m18_registers.py
│   │           └── m18_diagnostics.py
│   ├── software/                # Software analysis and algorithms
│   └── testing/                 # Internal testing utilities
├── configs/                     # Configuration files
│   ├── analysis_presets/       # Diagnostic preset configurations
│   ├── hardware_profiles/      # Hardware adapter configurations
│   └── manufacturer_profiles/  # Manufacturer-specific settings
├── tests/                       # Unit and integration tests
├── examples/                    # Example scripts and demonstrations
├── data/                        # Sample data and test databases
├── outputs/                     # Generated reports and visualizations
├── docs/                        # Documentation
├── scripts/                     # Utility and setup scripts
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Project configuration
├── README.md                   # Project overview
└── LICENSE                     # License information
```

## Key Components

### Hardware Support Integration
- **Makita Batteries**: 
  - Complete NEC 78K0 MCU flashing utility for firmware recovery
  - Hex file parsing, verification, and programming capabilities
  - Serial communication with MCU programming interface
- **Milwaukee M18**: 
  - Comprehensive protocol implementation with all 184 registers mapped
  - Charger simulation and RedLink protocol support
  - Advanced diagnostics with health scoring algorithms
- **Arduino Interface**: 
  - OneWire protocol communication for diagnostic modules
  - Makita temperature sensor integration
  - Extensible modular architecture for additional sensors

### Diagnostic Capabilities
- **Health Analysis**: Multi-factor health scoring with safety event tracking
- **Usage Analytics**: 20-bucket discharge current analysis (10A-200A+)
- **Temperature Monitoring**: Dual-sensor thermal health assessment
- **Voltage Analysis**: 5-cell individual voltage monitoring with imbalance detection
- **Charging Intelligence**: RedLink vs standard charger usage tracking
- **Lifecycle Management**: Comprehensive charge cycle and degradation analysis
- **Safety Monitoring**: Overheat, overcurrent, and low-voltage event tracking

### Manufacturer Support
- **Milwaukee M18**: 
  - All battery types: CP (Compact), XC (Extended), HO (High Output), Forge
  - Capacity range: 2Ah-12Ah with cell configuration mapping
  - Complete register database with 184 documented parameters
- **Makita**: 
  - NEC 78K0 MCU-based batteries with firmware recovery
  - Arduino-based temperature monitoring support
- **Extensible Framework**: 
  - Modular manufacturer integration system
  - Configuration-driven protocol support
  - Pluggable diagnostic modules

## Integration Status
✅ **NEC 78K0 Flash Utility**: Complete integration with hex parsing, MCU programming  
✅ **M18 Protocol Research**: Full 184-register mapping with comprehensive diagnostics  
✅ **Open Battery Information**: Arduino interface with OneWire protocol support  
✅ **Configuration System**: Updated manufacturer profiles with complete register mapping  
✅ **Testing Infrastructure**: Unit tests, CLI tests, and mocked hardware validation  
✅ **Modular Architecture**: Extensible manufacturer framework established  

## Available CLI Commands

### Milwaukee M18 Diagnostics
```bash
# Protocol core operations
python -m ubdf.hardware.manufacturers.milwaukee.m18_protocol_core --port COM3 --scan
python -m ubdf.hardware.manufacturers.milwaukee.m18_protocol_core --port COM3 --read-all

# Advanced diagnostics with health scoring
python -m ubdf.hardware.manufacturers.milwaukee.m18_diagnostics --port COM3 --health-report
python -m ubdf.hardware.manufacturers.milwaukee.m18_diagnostics --port COM3 --usage-analytics
```

### Makita NEC 78K0 Flash Operations
```bash
# Flash programming and verification
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --list-ports
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --port COM3 --program firmware.hex
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --port COM3 --verify firmware.hex
```

### Arduino Hardware Interface
```bash
# Hardware discovery and diagnostics
python -m ubdf.hardware.arduino_interface --discover-ports
python -m ubdf.hardware.arduino_interface --port COM4 --makita-temp
python -m ubdf.hardware.arduino_interface --port COM4 --run-diagnostics
```

## Development Workflow
1. **Hardware Integration**: Add manufacturers in `ubdf/hardware/manufacturers/`
2. **Configuration**: Update profiles in `configs/manufacturer_profiles/`
3. **Testing**: Create comprehensive tests in `tests/` directory
4. **CLI Testing**: Validate with scripts in `scripts/`
5. **Documentation**: Update examples and structure documentation
6. **Validation**: Run development setup: `python scripts/setup_development.py`
