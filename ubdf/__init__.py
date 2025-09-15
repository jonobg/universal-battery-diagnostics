"""
Universal Battery Diagnostics Framework (UBDF)
Professional multi-manufacturer battery testing and analysis platform.
"""

__version__ = "0.1.0"
__author__ = "Battery Reverse Engineering Community"
__description__ = "Professional multi-manufacturer battery diagnostics framework"

from .hardware.base.protocol_interface import BatteryProtocol, ProtocolType, BatteryDiagnostics
from .hardware.manufacturers.milwaukee.m18_protocol import MilwaukeeM18Protocol
from .hardware.manufacturers.makita.lxt_protocol import MakitaLXTProtocol
from .hardware.manufacturers.dewalt.xr_protocol import DeWaltXRProtocol
from .hardware.manufacturers.ryobi.one_plus_protocol import RyobiOnePlusProtocol

__all__ = [
    "BatteryProtocol",
    "ProtocolType", 
    "BatteryDiagnostics",
    "MilwaukeeM18Protocol",
    "MakitaLXTProtocol",
    "DeWaltXRProtocol",
    "RyobiOnePlusProtocol",
]