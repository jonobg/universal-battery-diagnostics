#!/usr/bin/env python3
"""
Development Environment Setup Script
Sets up the UBDF development environment with proper dependencies and validation.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Verify Python version compatibility"""
    if sys.version_info < (3.8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_dependencies():
    """Install project dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def validate_hardware_modules():
    """Test import of hardware modules"""
    print("🔧 Validating hardware modules...")
    
    modules_to_test = [
        "ubdf.hardware.manufacturers.milwaukee",
        "ubdf.hardware.manufacturers.makita.nec78k0_flasher", 
        "ubdf.hardware.arduino_interface"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    
    return True


def create_sample_config():
    """Create sample configuration file"""
    config_content = """
# UBDF Development Configuration
hardware:
  default_timeout: 5.0
  serial_baudrate: 9600
  
manufacturers:
  milwaukee:
    m18_protocol:
      timeout: 0.8
      baudrate: 4800
  
  makita:
    nec78k0:
      programming_voltage: 5.0
      
logging:
  level: INFO
  console: true
  file: ubdf.log
"""
    
    config_path = Path("configs/dev_config.yaml")
    if not config_path.exists():
        config_path.write_text(config_content.strip())
        print(f"✅ Created {config_path}")
    else:
        print(f"✅ Config exists: {config_path}")


def main():
    """Main setup routine"""
    print("🚀 UBDF Development Environment Setup\n")
    
    if not check_python_version():
        return 1
    
    if not install_dependencies():
        return 1
    
    if not validate_hardware_modules():
        print("⚠️  Hardware module validation failed - check dependencies")
    
    create_sample_config()
    
    print("\n✅ Development environment setup complete!")
    print("\nNext steps:")
    print("  1. Connect hardware for testing")
    print("  2. Run: python examples/simple_viz_test.py")
    print("  3. Run: python -m pytest tests/")
    
    return 0


if __name__ == "__main__":
    exit(main())
