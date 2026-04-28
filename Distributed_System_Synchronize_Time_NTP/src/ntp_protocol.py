"""
NTP Protocol Implementation (Simplified RFC 5905)
"""

import struct
import time
from typing import Tuple, Dict, Optional
from datetime import datetime


class NTPMessage:
    """
    Simplified NTP Message Format.
    Contains only essential fields for synchronization.
    """
    
    # NTP Format: 64-bit timestamp (seconds + fraction)
    # We'll use Unix timestamp for simplicity
    
    @staticmethod
    def create_request(origin_timestamp: float) -> bytes:
        """
        Create NTP request packet.
        
        Args:
            origin_timestamp: Client's sending time (Unix seconds)
            
        Returns:
            bytes: NTP packet
        """
        # Pack as: version(1byte) + mode(1byte) + origin_time(8bytes)
        packet = struct.pack('>BB', 3, 3)  # Version 3, Mode 3 (client)
        packet += struct.pack('>d', origin_timestamp)  # Origin timestamp
        return packet
    
    @staticmethod
    def parse_request(packet: bytes) -> float:
        """Parse NTP request and extract origin timestamp."""
        if len(packet) < 10:
            raise ValueError("Invalid NTP request packet")
        origin_time = struct.unpack('>d', packet[2:10])[0]
        return origin_time
    
    @staticmethod
    def create_response(
        origin_timestamp: float,
        receive_timestamp: float,
        transmit_timestamp: float
    ) -> bytes:
        """
        Create NTP response packet.
        
        Args:
            origin_timestamp: Client's sending time
            receive_timestamp: Server's receive time
            transmit_timestamp: Server's transmit time
            
        Returns:
            bytes: NTP response packet
        """
        packet = struct.pack('>BB', 3, 4)  # Version 3, Mode 4 (server)
        packet += struct.pack('>d', origin_timestamp)
        packet += struct.pack('>d', receive_timestamp)
        packet += struct.pack('>d', transmit_timestamp)
        return packet
    
    @staticmethod
    def parse_response(packet: bytes) -> Tuple[float, float, float, float]:
        """
        Parse NTP response packet.
        
        Returns:
            Tuple: (origin_time, receive_time, transmit_time, destination_time)
        """
        if len(packet) < 26:
            raise ValueError("Invalid NTP response packet")
        
        origin_time = struct.unpack('>d', packet[2:10])[0]
        receive_time = struct.unpack('>d', packet[10:18])[0]
        transmit_time = struct.unpack('>d', packet[18:26])[0]
        destination_time = time.time()
        
        return origin_time, receive_time, transmit_time, destination_time
    
    @staticmethod
    def calculate_offset_and_delay(
        t1: float, t2: float, t3: float, t4: float
    ) -> Tuple[float, float]:
        """
        Calculate NTP offset and delay from 4-timestamp algorithm.
        
        Parameters:
            t1: Client send time
            t2: Server receive time
            t3: Server transmit time
            t4: Client receive time
            
        Returns:
            Tuple: (offset_seconds, delay_seconds)
            
        Formula:
            delay = (t4 - t1) - (t3 - t2)
            offset = ((t2 - t1) + (t3 - t4)) / 2
        """
        delay = (t4 - t1) - (t3 - t2)
        offset = ((t2 - t1) + (t3 - t4)) / 2
        
        return offset, delay
    
    @staticmethod
    def get_timestamp_ms(unix_seconds: float) -> int:
        """Convert Unix timestamp to milliseconds."""
        return int(unix_seconds * 1000)
    
    @staticmethod
    def format_timestamp_readable(unix_seconds: float) -> str:
        """Format timestamp in readable format."""
        dt = datetime.fromtimestamp(unix_seconds)
        return dt.strftime("%H:%M:%S.%f")[:-3]


class NTPPacketParser:
    """Utility class for packet handling."""
    
    @staticmethod
    def log_ntp_transaction(
        t1: float, t2: float, t3: float, t4: float,
        offset_ms: float, delay_ms: float
    ) -> str:
        """Generate human-readable NTP transaction log."""
        log = (
            f"t1 (Client send):     {NTPMessage.format_timestamp_readable(t1)}\n"
            f"t2 (Server receive):  {NTPMessage.format_timestamp_readable(t2)}\n"
            f"t3 (Server transmit): {NTPMessage.format_timestamp_readable(t3)}\n"
            f"t4 (Client receive):  {NTPMessage.format_timestamp_readable(t4)}\n"
            f"---\n"
            f"Delay (d):  {delay_ms:.4f}ms\n"
            f"Offset (c): {offset_ms:+.4f}ms\n"
        )
        return log
