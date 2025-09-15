# UBDF Examples

This directory contains example scripts and demonstrations of the Universal Battery Diagnostics Framework capabilities.

## Visualization Examples

### Basic Charts
- `simple_viz_test.py` - Basic battery visualization example
- `quick_viz_test.py` - Quick visualization demonstration
- `compelling_viz_test.py` - Advanced compelling visualization features

### Time Series Analysis
- `timeseries_viz_test.py` - Time series battery analysis
- `test_visualizations.py` - Comprehensive visualization testing

## Usage

```bash
# Run from project root
cd /path/to/universal-battery-diagnostics

# Basic visualization
python examples/simple_viz_test.py

# Time series analysis
python examples/timeseries_viz_test.py

# Advanced features
python examples/compelling_viz_test.py
```

## Generated Outputs

All visualization outputs are automatically saved to the `outputs/` directory:
- HTML interactive charts
- PDF reports
- JSON analysis data

## Hardware Examples

For hardware-specific examples with actual battery communication:

```bash
# Milwaukee M18 diagnostics
python -m ubdf.hardware.manufacturers.milwaukee.m18_diagnostics --port COM5 --health

# Makita NEC 78K0 flashing
python -m ubdf.hardware.manufacturers.makita.nec78k0_flasher --port COM3 --scan

# Arduino interface
python -m ubdf.hardware.arduino_interface --port COM4 --test
```
