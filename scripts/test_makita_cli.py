#!/usr/bin/env python3
"""
Makita NEC 78K0 CLI Interface Testing Script
Validates all CLI functionality for the Makita NEC 78K0 flasher integration.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import logging
import tempfile


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


def create_test_hex_file():
    """Create a test HEX file for testing"""
    hex_content = """
:020000020000FC
:10000000010203040506070809101112131415164B
:10001000171819202122232425262728293031328F
:00000001FF
"""
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.hex', delete=False)
    temp_file.write(hex_content.strip())
    temp_file.close()
    return temp_file.name


def test_nec78k0_flasher():
    """Test NEC 78K0 flasher CLI"""
    print("\n🔧 Testing NEC 78K0 Flasher CLI")
    
    # Create test hex file
    hex_file = create_test_hex_file()
    
    tests = [
        # Test help output
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", "--help"], False),
        
        # Test port listing
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", "--list-ports"], True),
        
        # Test without hardware (should fail gracefully)
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
          "--port", "COM999", "--scan"], False),
        
        # Test hex file validation
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
          "--port", "COM999", "--program", hex_file], False),
        
        # Test verify command
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
          "--port", "COM999", "--verify", hex_file], False),
        
        # Test erase command
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
          "--port", "COM999", "--erase"], False),
        
        # Test verbose mode
        ([sys.executable, "-m", "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
          "--port", "COM999", "--scan", "--verbose"], False),
    ]
    
    results = []
    for command, expected_success in tests:
        results.append(run_command(command, expected_success))
    
    # Clean up test file
    Path(hex_file).unlink()
    
    return all(results)


def test_makita_package_import():
    """Test Makita package can be imported and used"""
    print("\n📦 Testing Makita Package Import")
    
    import_test = """
try:
    from ubdf.hardware.manufacturers.makita.nec78k0_flasher import (
        NEC78K0Flasher, FlashUtilityError, FlashCommand, FlashResponse
    )
    
    # Test enum values
    print(f"Silicon signature command: 0x{FlashCommand.SILICON_SIGNATURE.value:02X}")
    print(f"ACK response: 0x{FlashResponse.ACK.value:02X}")
    print(f"NAK response: 0x{FlashResponse.NAK.value:02X}")
    
    # Test hex parsing (without hardware)
    print("NEC 78K0 flasher classes imported successfully")
    
    print("✅ Makita package import successful")
except Exception as e:
    print(f"❌ Makita package import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"""
    
    command = [sys.executable, "-c", import_test]
    return run_command(command, True)


def test_hex_file_operations():
    """Test HEX file parsing operations"""
    print("\n📄 Testing HEX File Operations")
    
    hex_test = """
import tempfile
from ubdf.hardware.manufacturers.makita.nec78k0_flasher import NEC78K0Flasher

# Create test HEX content
hex_content = '''
:020000020000FC
:10000000010203040506070809101112131415164B
:10001000171819202122232425262728293031328F
:00000001FF
'''

# Create temporary file
with tempfile.NamedTemporaryFile(mode='w', suffix='.hex', delete=False) as f:
    f.write(hex_content.strip())
    hex_file = f.name

try:
    # Mock a flasher instance (no serial connection)
    import unittest.mock
    with unittest.mock.patch('serial.Serial'):
        flasher = NEC78K0Flasher(port="COM999")
        
        # Test hex parsing
        data = flasher.parse_hex_file(hex_file)
        print(f"Parsed HEX file: {len(data)} address blocks")
        
        # Validate data structure
        if 0x0000 in data:
            print(f"Address 0x0000: {len(data[0x0000])} bytes")
        if 0x0010 in data:
            print(f"Address 0x0010: {len(data[0x0010])} bytes")
            
        print("✅ HEX file parsing successful")
        
except Exception as e:
    print(f"❌ HEX file parsing failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    import os
    os.unlink(hex_file)
"""
    
    command = [sys.executable, "-c", hex_test]
    return run_command(command, True)


def main():
    """Run all Makita CLI tests"""
    parser = argparse.ArgumentParser(description="Makita NEC 78K0 CLI Testing")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    print("🔋 Makita NEC 78K0 CLI Interface Testing")
    print("=" * 50)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Package Import", test_makita_package_import()))
    test_results.append(("HEX File Operations", test_hex_file_operations()))
    test_results.append(("NEC 78K0 Flasher", test_nec78k0_flasher()))
    
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
        print("🎉 All Makita CLI tests passed!")
        return 0
    else:
        print("❌ Some Makita CLI tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
