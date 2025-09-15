# Contributing to UBDF

Thank you for your interest in contributing to the Universal Battery Diagnostics Framework!

## Ways to Contribute

- **Protocol Implementation**: Add support for new battery manufacturers
- **Hardware Adapters**: Support for additional communication interfaces
- **Analysis Algorithms**: Improve health metrics and predictive models
- **Documentation**: Improve guides and API documentation
- **Testing**: Add test coverage and hardware simulation
- **Bug Reports**: Report issues with existing functionality

## Development Setup

1. Fork and clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # When available
   ```
3. Run tests to ensure everything works:
   ```bash
   pytest tests/
   ```

## Adding a New Manufacturer

1. Create manufacturer directory: `ubdf/hardware/manufacturers/your_manufacturer/`
2. Implement the protocol class inheriting from `BatteryProtocol`
3. Define register mappings and communication methods
4. Add manufacturer-specific tests
5. Update documentation

## Protocol Implementation Guidelines

- Inherit from `ubdf.hardware.base.protocol_interface.BatteryProtocol`
- Implement all abstract methods
- Use manufacturer-specific register definitions
- Handle communication errors gracefully
- Include comprehensive docstrings

## Testing Requirements

- All new code must include tests
- Hardware tests should use mock interfaces when possible
- Integration tests should be marked appropriately
- Maintain existing test coverage levels

## Code Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for all public methods
- Write descriptive commit messages

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Update documentation as needed
4. Ensure all tests pass
5. Submit pull request with clear description

## Hardware Testing

If you have physical battery hardware:
- Mark tests with `@pytest.mark.hardware`
- Document required hardware setup
- Provide mock alternatives for CI/CD

## Questions?

Open an issue for discussion before starting major changes.