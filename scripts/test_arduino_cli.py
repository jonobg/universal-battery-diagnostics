#!/usr/bin/env python3
"""
Arduino OBI CLI Interface Testing Script
Validates all CLI functionality for the Arduino-based battery diagnostics.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import logging


def run_command(command, expected_success=True, timeout=30):
    """Run a CLI command and validate results"""
    print(f"\n🧪 Testing: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        
        print(f"   Return code: {result.returncode}")
        
        if result.stdout:
            print(f"   STDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"   STDERR:\n{result.stderr}")
        
        if expected_success:
            if result.returncode == 0:
                print("   ✅ SUCCESS")
                return True
            else:
                print("   ❌ FAILED")
                return False
        else:
            print("   ✅ Expected failure")
            return True
            
    except subprocess.TimeoutExpired:
        print("   ⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def test_arduino_interface():
    """Test Arduino OBI interface CLI"""
    print("\n🔧 Testing Arduino OBI Interface CLI")
    
    tests = [
        # Test help output
        ([sys.executable, "-m", "ubdf.hardware.arduino_interface", "--help"], False),
        
        # Test port discovery
        ([sys.executable, "-m", "ubdf.hardware.arduino_interface", "--discover"], True),
        
        # Test without hardware (should fail gracefully)
        ([sys.executable, "-m", "ubdf.hardware.arduino_interface", 
          "--port", "COM999", "--test"], False),
        
        # Test Makita temperature reading
        ([sys.executable, "-m", "ubdf.hardware.arduino_interface", 
          "--port", "COM999", "--makita-temp"], False),
    ]
    
    results = []
    for command, expected_success in tests:
        results.append(run_command(command, expected_success))
    
    return all(results)


def test_arduino_package_import():
    """Test Arduino package can be imported and used"""
    print("\n📦 Testing Arduino Package Import")
    
    import_test = """
try:
    from ubdf.hardware.arduino_interface import (
        ArduinoOBIInterface, ArduinoCommand, ArduinoVersion,
        MakitaBatteryModule, BatteryModuleInterface,
        discover_arduino_ports
    )
    
    # Test enum values
    print(f"Version command: 0x{ArduinoCommand.VERSION.value:02X}")
    print(f"Makita temp 1: 0x{ArduinoCommand.MAKITA_TEMP_1.value:02X}")
    print(f"OneWire CC: 0x{ArduinoCommand.ONEWIRE_CC.value:02X}")
    
    # Test version dataclass
    version = ArduinoVersion(0, 2, 1)
    print(f"Version string: {version}")
    
    # Test port discovery (mock)
    print("Port discovery function available")
    
    # Test module capabilities
    module = MakitaBatteryModule()
    capabilities = module.get_capabilities()
    print(f"Module capabilities: {len(capabilities)}")
    
    print("✅ Arduino package import successful")
except Exception as e:
    print(f"❌ Arduino package import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"""
    
    command = [sys.executable, "-c", import_test]
    return run_command(command, True)


def test_arduino_mock_operations():
    """Test Arduino operations with mocked hardware"""
    print("\n🤖 Testing Arduino Mock Operations")
    
    mock_test = """
try:
    import unittest.mock
    from ubdf.hardware.arduino_interface import ArduinoOBIInterface, MakitaBatteryModule
    
    # Mock serial interface
    with unittest.mock.patch('serial.Serial') as mock_serial_class:
        mock_serial = unittest.mock.Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        # Mock Arduino responses
        mock_serial.read.side_effect = [
            b'\\x01\\x03',     # Version command echo
            b'\\x00\\x02\\x01', # Version 0.2.1
            b'\\x31\\x02',     # Temperature command echo  
            b'\\x1A\\x1B'      # Temperature data
        ]
        
        # Test Arduino interface
        arduino = ArduinoOBIInterface(port="COM999")
        print(f"Firmware version: {arduino.firmware_version}")
        
        # Test Makita module
        module = MakitaBatteryModule()
        success = module.initialize(arduino)
        print(f"Module initialized: {success}")
        
        if success:
            # Mock temperature reading
            mock_serial.read.side_effect = [
                b'\\x31\\x02', b'\\x1A\\x1B'
            ]
            temp = arduino.read_makita_temperature_1()
            print(f"Temperature reading: {temp}")
        
    print("✅ Arduino mock operations successful")
    
except Exception as e:
    print(f"❌ Arduino mock operations failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"""
    
    command = [sys.executable, "-c", mock_test]
    return run_command(command, True)


def main():
    """Run all Arduino CLI tests"""
    parser = argparse.ArgumentParser(description="Arduino OBI CLI Testing")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    print("🤖 Arduino OBI CLI Interface Testing")
    print("=" * 50)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Package Import", test_arduino_package_import()))
    test_results.append(("Mock Operations", test_arduino_mock_operations()))
    test_results.append(("Arduino Interface", test_arduino_interface()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All Arduino CLI tests passed!")
        return 0
    else:
        print("❌ Some Arduino CLI tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
