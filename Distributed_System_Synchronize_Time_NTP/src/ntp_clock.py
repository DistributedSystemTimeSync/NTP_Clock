"""
Custom NTP Clock Simulation
Simulates real clock with offset and drift
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional


class NTPClock:
    """
    Simulated NTP Clock with offset and drift compensation.
    
    Parameters:
    - initial_offset_ms: Initial offset in milliseconds
    - drift_rate_ppm: Drift rate in parts per million (positive = runs fast)
    - clock_adj: Phase adjustment interval in seconds
    - clock_phase: Phase adjustment divisor (2^clock_phase)
    - clock_max: Maximum acceptable offset in milliseconds
    """
    
    def __init__(
        self,
        node_name: str,
        initial_offset_ms: float = 0,
        drift_rate_ppm: float = 0,
        clock_adj: float = 1.0,
        clock_phase: int = 6,
        clock_max: float = 128.0
    ):
        self.node_name = node_name
        self.initial_offset_ms = initial_offset_ms
        self.drift_rate_ppm = drift_rate_ppm
        
        # Clock adjustment parameters
        self.clock_adj = clock_adj
        self.clock_phase = clock_phase
        self.clock_max = clock_max
        self.phase_divisor = 2 ** clock_phase
        
        # State variables
        self.start_system_time = time.time()
        self.clock_adjust_ms = initial_offset_ms  # Offset to apply
        self.drift_compensation_ppm = 0  # Compensation for drift
        self.last_update_time = self.start_system_time
        
        # Slewing state
        self.is_slewing = False
        self.adjustment_count = 0
        
        # Statistics
        self.stats = {
            "total_adjustments": 0,
            "slewing_completed": False,
            "final_offset_ms": initial_offset_ms,
            "convergence_time": 0
        }
    
    def get_current_time(self) -> float:
        """
        Get current simulated time as Unix timestamp.
        Applies offset and drift compensation.
        
        Returns:
            float: Current time in seconds (Unix timestamp)
        """
        elapsed_real = time.time() - self.start_system_time
        
        # Apply drift: adds (drift_rate_ppm * elapsed_time / 1e6) seconds
        drift_correction = (self.drift_compensation_ppm * elapsed_real) / 1e6
        
        # Current offset in seconds
        offset_sec = self.clock_adjust_ms / 1000.0
        
        # Simulated time = reference time + elapsed + offset + drift
        simulated_time = self.start_system_time + elapsed_real + offset_sec + drift_correction
        
        return simulated_time
    
    def get_current_time_ms(self) -> int:
        """Get current time in milliseconds since epoch."""
        return int(self.get_current_time() * 1000)
    
    def get_current_time_readable(self) -> str:
        """Get current time in readable format."""
        dt = datetime.fromtimestamp(self.get_current_time())
        return dt.strftime("%H:%M:%S.%f")[:-3]
    
    def process_ntp_response(
        self,
        offset_ms: float,
        delay_ms: float,
        verify: bool = True
    ) -> Dict[str, any]:
        """
        Process NTP response and update clock.
        
        Args:
            offset_ms: Calculated offset in milliseconds
            delay_ms: Round-trip delay in milliseconds
            verify: Check if offset within acceptable range
            
        Returns:
            dict: Adjustment result
        """
        result = {
            "accepted": False,
            "adjustment_type": None,
            "phase_adjustment_ms": 0,
            "remaining_adjustment_ms": self.clock_adjust_ms,
            "drift_compensation_ppm": self.drift_compensation_ppm
        }
        
        # Check if offset is acceptable
        if verify and abs(offset_ms) > self.clock_max:
            result["adjustment_type"] = "STEP"
            # Step adjustment - jump directly
            self.clock_adjust_ms = offset_ms
            self.is_slewing = False
            result["accepted"] = True
        else:
            result["adjustment_type"] = "SLEWING"
            self.clock_adjust_ms = offset_ms
            self.drift_compensation_ppm = -self.drift_rate_ppm  # Counteract drift
            self.is_slewing = True
            result["accepted"] = True
        
        self.stats["total_adjustments"] += 1
        return result
    
    def slewing_tick(self) -> Dict[str, any]:
        """
        Execute one slewing adjustment cycle (called every clock_adj seconds).
        
        Returns:
            dict: Adjustment details
        """
        result = {
            "phase_adjustment_ms": 0,
            "remaining_adjustment_ms": self.clock_adjust_ms,
            "is_slewing": self.is_slewing,
            "adjustment_count": self.adjustment_count
        }
        
        if not self.is_slewing or self.clock_adjust_ms == 0:
            self.is_slewing = False
            self.stats["slewing_completed"] = True
            return result
        
        # Calculate phase adjustment
        phase_adj_ms = self.clock_adjust_ms / self.phase_divisor
        
        # Apply adjustment
        self.clock_adjust_ms -= phase_adj_ms
        
        # Stop slewing if adjustment is negligible
        if abs(self.clock_adjust_ms) < 0.001:
            self.clock_adjust_ms = 0
            self.is_slewing = False
            self.stats["slewing_completed"] = True
        
        self.adjustment_count += 1
        result["phase_adjustment_ms"] = phase_adj_ms
        result["remaining_adjustment_ms"] = self.clock_adjust_ms
        
        return result
    
    def get_status(self) -> Dict[str, any]:
        """Get current clock status."""
        return {
            "node": self.node_name,
            "current_time": self.get_current_time_readable(),
            "offset_ms": self.clock_adjust_ms,
            "drift_ppm": self.drift_rate_ppm,
            "drift_compensation_ppm": self.drift_compensation_ppm,
            "is_slewing": self.is_slewing,
            "adjustment_count": self.adjustment_count,
            "stats": self.stats.copy()
        }
