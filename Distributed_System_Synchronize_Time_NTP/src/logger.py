"""
Logging Configuration for NTP Synchronization
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup logger with console and file handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console formatter
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create parent directory if needed
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class CSVLogger:
    """CSV logger for exporting synchronization data."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self.file = open(filepath, 'w')
        self._write_header()
    
    def _write_header(self):
        """Write CSV header."""
        header = (
            "timestamp,node,event_type,current_time_ms,offset_ms,"
            "phase_adjustment_ms,remaining_adjustment_ms,is_slewing,"
            "adjustment_count,drift_ppm,drift_compensation_ppm,status\n"
        )
        self.file.write(header)
        self.file.flush()
    
    def log_event(
        self,
        node: str,
        event_type: str,
        current_time_ms: int,
        offset_ms: float,
        phase_adjustment_ms: float = 0,
        remaining_adjustment_ms: float = 0,
        is_slewing: bool = False,
        adjustment_count: int = 0,
        drift_ppm: float = 0,
        drift_compensation_ppm: float = 0,
        status: str = ""
    ):
        """Log event to CSV."""
        timestamp = datetime.now().isoformat()
        row = (
            f"{timestamp},{node},{event_type},{current_time_ms},"
            f"{offset_ms:.4f},{phase_adjustment_ms:.4f},"
            f"{remaining_adjustment_ms:.4f},{int(is_slewing)},"
            f"{adjustment_count},{drift_ppm},{drift_compensation_ppm},\"{status}\"\n"
        )
        self.file.write(row)
        self.file.flush()
    
    def close(self):
        """Close CSV file."""
        self.file.close()
