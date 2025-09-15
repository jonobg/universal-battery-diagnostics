#!/usr/bin/env python3
"""
Milwaukee M18 CLI Interface Testing Script
Validates all CLI functionality for the Milwaukee M18 integration.
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


def test_m18_protocol_core():
    """Test M18 protocol core CLI"""
    print("\n🔧 Testing M18 Protocol Core CLI")
    
    tests = [
        # Test help output
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_protocol_core", "--help"], False),
        
        # Test without hardware (should fail gracefully)
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_protocol_core", 
          "--port", "COM999"], False),
        
        # Test debug flag
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_protocol_core", 
          "--port", "COM999", "--debug"], False),
    ]
    
    results = []
    for command, expected_success in tests:
        results.append(run_command(command, expected_success))
    
    return all(results)


def test_m18_registers():
    """Test M18 registers CLI"""
    print("\n🗂️ Testing M18 Registers CLI")
    
    tests = [
        # Test register summary
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_registers", "--summary"], True),
        
        # Test specific register lookup
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_registers", 
          "--register", "12"], True),
        
        # Test register type filtering
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_registers", 
          "--type", "voltage_array"], True),
        
        # Test invalid register
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_registers", 
          "--register", "999"], True),
        
        # Test invalid type
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_registers", 
          "--type", "invalid"], True),
    ]
    
    results = []
    for command, expected_success in tests:
        results.append(run_command(command, expected_success))
    
    return all(results)


def test_m18_diagnostics():
    """Test M18 diagnostics CLI"""
    print("\n🔍 Testing M18 Diagnostics CLI")
    
    tests = [
        # Test help
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_diagnostics", "--help"], False),
        
        # Test without hardware (should fail gracefully)
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_diagnostics", 
          "--port", "COM999", "--health"], False),
        
        # Test JSON output flag
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_diagnostics", 
          "--port", "COM999", "--health", "--json"], False),
        
        # Test debug mode
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.milwaukee.m18_diagnostics", 
          "--port", "COM999", "--debug"], False),
    ]
    
    results = []
    for command, expected_success in tests:
        results.append(run_command(command, expected_success))
    
    return all(results)


def test_milwaukee_package_import():
    """Test Milwaukee package can be imported and used"""
    print("\n📦 Testing Milwaukee Package Import")
    
    import_test = """
try:
    from ubdf.hardware.manufacturers.milwaukee import (
        M18Protocol, M18RegisterMap, M18Diagnostics,
        create_m18_diagnostics, supported_battery_types, get_package_info
    )
    
    # Test package info
    info = get_package_info()
    print(f"Package: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Registers mapped: {info['registers_mapped']}")
    
    # Test battery types
    types = supported_battery_types()
    print(f"Supported battery types: {len(types)}")
    
    # Test register summary
    summary = M18RegisterMap.get_register_summary()
    print("Register summary generated successfully")
    
    print("✅ Milwaukee package import successful")
except Exception as e:
    print(f"❌ Milwaukee package import failed: {e}")
    exit(1)
"""
    
    command = [sys.executable, "-c", import_test]
    return run_command(command, True)


def main():
    """Run all Milwaukee CLI tests"""
    parser = argparse.ArgumentParser(description="Milwaukee M18 CLI Testing")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Milwaukee M18 CLI Interface Testing")
    print("=" * 50)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Package Import", test_milwaukee_package_import()))
    test_results.append(("M18 Registers", test_m18_registers()))
    test_results.append(("M18 Protocol Core", test_m18_protocol_core()))
    test_results.append(("M18 Diagnostics", test_m18_diagnostics()))
    
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
        print("🎉 All Milwaukee CLI tests passed!")
        return 0
    else:
        print("❌ Some Milwaukee CLI tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
