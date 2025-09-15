#!/usr/bin/env python3
"""
NEC 78K0 Flash Utility for Makita Battery BMS
Integrated from mnh-jansson/78k0-flash-utility

This module provides low-level flash programming capabilities for Makita batteries
using NEC 78K0 microcontrollers. Supports firmware recovery and analysis.
"""

import time
import serial
import sys
import os.path
from os import path
import binascii
import logging
from typing import Optional, Dict, List, Union


class NEC78K0FlashError(Exception):
    """Custom exception for NEC 78K0 flash operations"""
    pass


class NEC78K0Flasher:
    """
    NEC 78K0 Flash Programming Interface for Makita Batteries
    
    Provides functionality to:
    - Program firmware blocks
    - Verify firmware integrity
    - Erase blocks/chip
    - Check empty blocks
    - Recover original firmware
    """
    
    # Number of blocks in PD78F0513 (Makita BMS MCU)
    N_BLOCKS = 32
    BLOCK_SIZE = 1024
    
    STATUS_CODES = {
        0x00: "No data",
        0x04: "Command number error", 
        0x05: "Parameter error",
        0x06: "Normal acknowledgment (ACK)",
        0x07: "Checksum error",
        0x0F: "Verify error",
        0x10: "Protect error",
        0x15: "Negative acknowledgment (NACK)",
        0x1A: "MRG10 error",
        0x1B: "MRG11 error", 
        0x1C: "Write error",
        0x20: "Read error",
        0xFF: "Processing in progress (BUSY)",
    }
    
    def __init__(self, port: str = "COM1", baudrate: int = 9600, timeout: float = 1.0):
        """Initialize NEC 78K0 flasher"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("NEC 78K0 Flasher initialized")
    
    def connect(self) -> bool:
        """
        Establish connection to NEC 78K0 microcontroller
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info(f"Connecting to serial port {self.port}...")
            
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )
            
            if not self.ser.is_open:
                self.ser.open()
            
            # Reset microcontroller with RTS line
            self._reset_mcu()
            
            # Send synchronization bytes
            self.ser.write(bytearray([0x00]))
            time.sleep(0.011)
            self.ser.write(bytearray([0x00]))
            time.sleep(0.011)
            
            self.logger.info("Connection established successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.logger.info("Disconnected from MCU")
    
    def _reset_mcu(self):
        """Reset microcontroller using RTS line"""
        self.ser.setRTS(True)
        time.sleep(0.011)
        self.ser.setRTS(False) 
        time.sleep(0.011)
        self.ser.setRTS(True)
        time.sleep(0.400)
    
    def _add_checksum(self, data: bytearray, size: int) -> int:
        """Calculate checksum for command data"""
        crc = 0x00
        for x in range(size + 1):
            crc = (crc - data[x + 1]) % 256
        return crc
    
    def _receive_response(self) -> int:
        """
        Receive and parse response from MCU
        
        Returns:
            int: Status code from MCU
        """
        try:
            # Read 2 bytes to determine length
            response = self.ser.read(2)
            
            if len(response) < 2:
                raise NEC78K0FlashError("Response too short")
            
            # Read remaining bytes
            response += self.ser.read(response[1] + 2)
            
            status = response[2]
            status_msg = self.STATUS_CODES.get(status, f"Unknown status: 0x{status:02X}")
            
            self.logger.debug(f"MCU Response: {status_msg}")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to receive response: {e}")
            raise NEC78K0FlashError(f"Communication error: {e}")
    
    def reset_mcu(self) -> bool:
        """Send reset command to MCU"""
        try:
            cmd = bytearray([0x01, 0x01, 0x00])  # Start, Length, Command
            cmd.append(self._add_checksum(cmd, cmd[1]))
            cmd.append(0x03)  # Stop byte
            
            self.ser.write(cmd)
            status = self._receive_response()
            
            return status == 0x06  # ACK
            
        except Exception as e:
            self.logger.error(f"Reset command failed: {e}")
            return False
    
    def check_block_empty(self, block: int) -> bool:
        """
        Check if specified flash block is empty
        
        Args:
            block: Block number (0-31)
            
        Returns:
            bool: True if block is empty
        """
        if not (0 <= block < self.N_BLOCKS):
            raise ValueError(f"Block must be 0-{self.N_BLOCKS-1}")
        
        start_addr = block * self.BLOCK_SIZE
        end_addr = ((block + 1) * self.BLOCK_SIZE) - 1
        
        cmd = bytearray([0x01, 0x07, 0x32])  # Start, Length, Blank check command
        
        # Add address range
        cmd.extend([
            (start_addr >> 16) & 0xFF,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (end_addr >> 16) & 0xFF,
            (end_addr >> 8) & 0xFF,
            end_addr & 0xFF
        ])
        
        cmd.append(self._add_checksum(cmd, cmd[1]))
        cmd.append(0x03)  # Stop byte
        
        self.ser.write(cmd)
        status = self._receive_response()
        
        is_empty = status == 0x06
        self.logger.info(f"Block {block}: {'Empty' if is_empty else 'Not empty'}")
        
        return is_empty
    
    def erase_block(self, block: int) -> bool:
        """
        Erase specified flash block
        
        Args:
            block: Block number to erase
            
        Returns:
            bool: True if erase successful
        """
        if not (0 <= block < self.N_BLOCKS):
            raise ValueError(f"Block must be 0-{self.N_BLOCKS-1}")
        
        start_addr = block * self.BLOCK_SIZE
        end_addr = ((block + 1) * self.BLOCK_SIZE) - 1
        
        cmd = bytearray([0x01, 0x07, 0x22])  # Start, Length, Block erase command
        
        cmd.extend([
            (start_addr >> 16) & 0xFF,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (end_addr >> 16) & 0xFF,
            (end_addr >> 8) & 0xFF,
            end_addr & 0xFF
        ])
        
        cmd.append(self._add_checksum(cmd, cmd[1]))
        cmd.append(0x03)
        
        self.logger.info(f"Erasing block {block}...")
        self.ser.write(cmd)
        status = self._receive_response()
        
        success = status == 0x06
        if success:
            self.logger.info(f"Block {block} erased successfully")
        else:
            self.logger.error(f"Block {block} erase failed")
            
        return success
    
    def erase_chip(self) -> bool:
        """
        Erase entire chip
        
        Returns:
            bool: True if erase successful
        """
        cmd = bytearray([0x01, 0x01, 0x20])  # Start, Length, Chip erase command
        cmd.append(self._add_checksum(cmd, cmd[1]))
        cmd.append(0x03)
        
        self.logger.info("Erasing entire chip...")
        self.ser.write(cmd)
        status = self._receive_response()
        
        success = status == 0x06
        if success:
            self.logger.info("Chip erased successfully")
        else:
            self.logger.error("Chip erase failed")
            
        return success
    
    def program_block(self, block: int, firmware_data: bytes) -> bool:
        """
        Program firmware data to specified block
        
        Args:
            block: Target block number
            firmware_data: Binary firmware data (max 256 bytes)
            
        Returns:
            bool: True if programming successful
        """
        if len(firmware_data) > 256:
            raise ValueError("Firmware data too large (max 256 bytes)")
        
        start_addr = block * self.BLOCK_SIZE
        end_addr = ((block + 1) * self.BLOCK_SIZE) - 1
        
        # Send programming command
        cmd = bytearray([0x01, 0x07, 0x40])  # Start, Length, Program command
        
        cmd.extend([
            (start_addr >> 16) & 0xFF,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (end_addr >> 16) & 0xFF,
            (end_addr >> 8) & 0xFF,
            end_addr & 0xFF
        ])
        
        cmd.append(self._add_checksum(cmd, cmd[1]))
        cmd.append(0x03)
        
        self.logger.info(f"Programming block {block}...")
        self.ser.write(cmd)
        status = self._receive_response()
        
        if status != 0x06:
            self.logger.error("Programming command rejected")
            return False
        
        # Send firmware data
        data_cmd = bytearray([0x02, 0x00])  # Start, Length (256 bytes)
        data_cmd.extend(firmware_data)
        
        # Pad to 256 bytes if needed
        while len(data_cmd) < 258:  # 2 header + 256 data
            data_cmd.append(0xFF)
        
        data_cmd.append(self._add_checksum(data_cmd, 256))
        data_cmd.append(0x03)
        
        self.ser.write(data_cmd)
        status = self._receive_response()
        
        success = status == 0x06
        if success:
            self.logger.info(f"Block {block} programmed successfully")
        else:
            self.logger.error(f"Block {block} programming failed")
            
        return success
    
    def verify_block(self, block: int, firmware_data: bytes) -> bool:
        """
        Verify programmed firmware matches expected data
        
        Args:
            block: Block number to verify
            firmware_data: Expected firmware data
            
        Returns:
            bool: True if verification successful
        """
        start_addr = block * self.BLOCK_SIZE
        end_addr = ((block + 1) * self.BLOCK_SIZE) - 1
        
        # Send verify command
        cmd = bytearray([0x01, 0x07, 0x13])  # Start, Length, Verify command
        
        cmd.extend([
            (start_addr >> 16) & 0xFF,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (end_addr >> 16) & 0xFF,
            (end_addr >> 8) & 0xFF,
            end_addr & 0xFF
        ])
        
        cmd.append(self._add_checksum(cmd, cmd[1]))
        cmd.append(0x03)
        
        self.logger.info(f"Verifying block {block}...")
        self.ser.write(cmd)
        status = self._receive_response()
        
        if status != 0x06:
            return False
        
        # Send verification data
        data_cmd = bytearray([0x02, 0x00])  # Start, Length
        data_cmd.extend(firmware_data)
        
        # Pad to 256 bytes
        while len(data_cmd) < 258:
            data_cmd.append(0xFF)
        
        data_cmd.append(self._add_checksum(data_cmd, 256))
        data_cmd.append(0x03)
        
        self.ser.write(data_cmd)
        status = self._receive_response()
        
        success = status == 0x06
        if success:
            self.logger.info(f"Block {block} verification successful")
        else:
            self.logger.error(f"Block {block} verification failed")
            
        return success
    
    def scan_empty_blocks(self) -> List[int]:
        """
        Scan all blocks and return list of empty ones
        
        Returns:
            List[int]: List of empty block numbers
        """
        empty_blocks = []
        
        self.logger.info("Scanning for empty blocks...")
        for block in range(self.N_BLOCKS):
            if self.check_block_empty(block):
                empty_blocks.append(block)
        
        self.logger.info(f"Found {len(empty_blocks)} empty blocks: {empty_blocks}")
        return empty_blocks
    
    def program_firmware_file(self, block: int, firmware_path: str) -> bool:
        """
        Program firmware from file to specified block
        
        Args:
            block: Target block number
            firmware_path: Path to firmware file
            
        Returns:
            bool: True if programming successful
        """
        if not os.path.exists(firmware_path):
            raise FileNotFoundError(f"Firmware file not found: {firmware_path}")
        
        with open(firmware_path, 'rb') as f:
            firmware_data = f.read()
        
        return self.program_block(block, firmware_data)
    
    def __enter__(self):
        """Context manager entry"""
        if not self.connect():
            raise NEC78K0FlashError("Failed to connect to MCU")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def main():
    """CLI interface for NEC 78K0 flasher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEC 78K0 Flash Utility for Makita Batteries")
    parser.add_argument("-p", "--port", default="COM1", help="Serial port")
    parser.add_argument("-b", "--block", type=int, help="Specify block number")
    parser.add_argument("-f", "--flash", help="Flash firmware file")
    parser.add_argument("-v", "--verify", help="Verify firmware file")
    parser.add_argument("-e", "--erase", action="store_true", help="Erase block/chip")
    parser.add_argument("-c", "--check", action="store_true", help="Check empty blocks")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        with NEC78K0Flasher(port=args.port) as flasher:
            flasher.reset_mcu()
            
            if args.check:
                flasher.scan_empty_blocks()
            
            if args.erase:
                if args.block is not None:
                    flasher.erase_block(args.block)
                else:
                    flasher.erase_chip()
            
            if args.flash:
                if args.block is None:
                    print("Block number required for flashing")
                    sys.exit(1)
                flasher.program_firmware_file(args.block, args.flash)
            
            if args.verify:
                if args.block is None:
                    print("Block number required for verification") 
                    sys.exit(1)
                with open(args.verify, 'rb') as f:
                    firmware_data = f.read()
                flasher.verify_block(args.block, firmware_data)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
