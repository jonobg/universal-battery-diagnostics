# UBDF Testing Guide

## Quick Start Testing

### 1. **Install Test Dependencies**
```bash
cd D:\Projects\universal-battery-diagnostics
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

### 2. **Run All Tests**
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=ubdf --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/ -v

# Run integration tests (slower)
pytest tests/integration/ -v
```

### 3. **Test Categories**

**Unit Tests** (No hardware required):
- Protocol implementations
- Database operations
- Health calculations
- Register parsing

**Integration Tests** (Mock hardware):
- Complete workflows
- CLI commands  
- Database integrity
- Error handling

**Hardware Tests** (Requires real batteries):
- Actual Milwaukee M18 communication
- Real hardware validation

## Test What You Built

### **Framework Core**
```bash
# Test protocol interfaces
pytest tests/unit/test_milwaukee_protocol.py::TestMilwaukeeM18Protocol::test_protocol_properties -v

# Test database operations
pytest tests/integration/test_full_workflow.py::TestDatabaseIntegrity::test_concurrent_sessions -v
```

### **CLI Interface**
```bash
# Test CLI commands
pytest tests/integration/test_cli_commands.py -v

# Test specific CLI functions
python -m ubdf.cli.main --help
python -m ubdf.cli.main init
python -m ubdf.cli.main scan --manufacturer milwaukee
```

### **End-to-End Workflow**
```bash
# Test complete diagnostic workflow
pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_complete_diagnostic_workflow -v

# Test multi-battery fleet
pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_multi_battery_fleet_analysis -v
```

## Validate Core Components

### **1. Protocol System**
```python
# Test in Python console
from ubdf.hardware.manufacturers.milwaukee.m18_protocol import MilwaukeeM18Protocol

protocol = MilwaukeeM18Protocol("/dev/ttyUSB0")
print(f"Manufacturer: {protocol.manufacturer}")
print(f"Supported models: {protocol.supported_models}")

# Test register map
reg_map = protocol.get_register_map()
print(f"Total registers: {len(reg_map)}")
print(f"Cell voltage register: {reg_map[12]}")
```

### **2. Database System**
```python
# Test database functionality
from ubdf.core.database.models import BatteryDatabase

db = BatteryDatabase("test_battery.db")
battery_id = db.register_battery("TEST001", "Milwaukee", "M18B9", 9.0)
print(f"Registered battery ID: {battery_id}")

stats = db.get_database_stats()
print(f"Database stats: {stats}")
```

### **3. Visualization System**
```python
# Test visualization (requires matplotlib/plotly)
from ubdf.software.visualization.plotly_dashboards import UniversalBatteryVisualizationDashboard

dashboard = UniversalBatteryVisualizationDashboard("test_battery.db")
# Will create empty dashboard if no data
```

## Performance Validation

### **Load Testing**
```bash
# Test with larger datasets
pytest tests/integration/test_full_workflow.py::TestDatabaseIntegrity::test_large_dataset_performance -v

# Memory usage monitoring
python -c "
import tracemalloc
tracemalloc.start()
# Run your test code here
from ubdf.core.database.models import BatteryDatabase
db = BatteryDatabase('perf_test.db')
for i in range(100):
    db.register_battery(f'PERF_{i}', 'Milwaukee', 'M18B9', 9.0)
current, peak = tracemalloc.get_traced_memory()
print(f'Memory usage: {current / 1024 / 1024:.1f} MB')
tracemalloc.stop()
"
```

## Troubleshooting Tests

### **Common Test Issues**

**Import Errors:**
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:D:/Projects/universal-battery-diagnostics"
# Or for Windows
set PYTHONPATH=%PYTHONPATH%;D:\Projects\universal-battery-diagnostics
```

**Database Errors:**
```bash
# Clear test databases
rm -f test_*.db
rm -f *.db
```

**Mock Hardware Issues:**
```bash
# Test mock setup
pytest tests/conftest.py::test_mock_setup -v
```

## Manual Testing Scenarios

### **Scenario 1: New User Setup**
```bash
cd D:\Projects\universal-battery-diagnostics
python -m ubdf.cli.main init
ls -la reports/ configs/ data/
```

### **Scenario 2: Battery Discovery**
```bash
# Mock discovery (no hardware)
python -m ubdf.cli.main scan --manufacturer milwaukee --output discovery.json
cat discovery.json
```

### **Scenario 3: Database Operations**
```python
# Manual database testing
from ubdf.core.database.models import BatteryDatabase

db = BatteryDatabase("manual_test.db")

# Add test battery
battery_id = db.register_battery("MANUAL001", "Milwaukee", "M18B9", 9.0)
session_id = db.start_diagnostic_session(battery_id, "manual_test")

# Add mock health data
health_metrics = {
    'capacity_percentage': 85,
    'health_score': 80,
    'cycle_count': 200,
    'internal_resistance_mohm': 30
}
db.store_health_metrics(session_id, health_metrics)
db.complete_diagnostic_session(session_id, True)

# Verify data
stats = db.get_database_stats()
print(f"Test results: {stats}")
```

## Success Criteria

**✅ All tests passing:**
- Unit tests: 15+ tests
- Integration tests: 8+ tests  
- No critical failures

**✅ Core functionality working:**
- Protocol interfaces load without errors
- Database operations complete successfully
- CLI commands execute properly
- Mock hardware simulation functional

**✅ Performance acceptable:**
- 100 batteries + 500 sessions < 10 seconds
- Memory usage < 100MB for typical operations
- Database queries respond < 1 second

## Next Steps After Testing

1. **Add Real Hardware**: Connect actual Milwaukee M18 battery
2. **Extend Protocols**: Add Makita, DeWalt implementations  
3. **Enhance Analytics**: Add predictive models
4. **Deploy Production**: Set up continuous integration

## Test Output Examples

**Successful Test Run:**
```
========== test session starts ==========
tests/unit/test_milwaukee_protocol.py ................ [100%]
tests/integration/test_cli_commands.py ........ [100%]
tests/integration/test_full_workflow.py ............ [100%]

========== 24 passed in 5.23s ==========
```

**CLI Test Success:**
```
$ python -m ubdf.cli.main scan
🔍 Scanning - Battery Discovery Scan
Manufacturer: auto
Port: Auto-detect
✅ Results: Found 1 simulated battery
```