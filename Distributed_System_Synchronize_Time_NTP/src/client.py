"""
NTP Client Implementation
"""

import socket
import time
import json
import threading
from pathlib import Path
from src.ntp_clock import NTPClock
from src.ntp_protocol import NTPMessage, NTPPacketParser
from src.logger import setup_logger, CSVLogger


class NTPClient:
    """
    NTP Client - Synchronizes with NTP Server.
    Periodically queries server and adjusts local clock.
    """
    
    def __init__(
        self,
        config_file: str,
        server_host: str = "server",
        server_port: int = 123
    ):
        self.config = self._load_config(config_file)
        self.server_host = server_host
        self.server_port = server_port
        self.running = False
        
        # Initialize clock
        self.clock = NTPClock(
            node_name=self.config["node_name"],
            initial_offset_ms=self.config.get("initial_offset_ms", 0),
            drift_rate_ppm=self.config.get("drift_rate_ppm", 0),
            clock_adj=self.config.get("clock_adj", 1.0),
            clock_phase=self.config.get("clock_phase", 6),
            clock_max=self.config.get("clock_max", 128.0)
        )
        
        # Setup logging
        log_dir = Path(self.config.get("log_dir", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger(
            f"NTPClient-{self.config['node_name']}",
            str(log_dir / f"client_{self.config['node_name']}.log"),
            level=20
        )
        
        # CSV logging
        self.csv_logger = CSVLogger(
            str(Path(self.config.get("result_dir", "results")) / 
                f"client_{self.config['node_name']}.csv")
        )
        
        # Statistics
        self.sync_attempt = 0
        self.sync_success = 0
        self.sync_failed = 0
        
        self.logger.info(
            f"NTP Client initialized: {self.config['node_name']} "
            f"(offset={self.config.get('initial_offset_ms', 0)}ms, "
            f"drift={self.config.get('drift_rate_ppm', 0)}ppm)"
        )
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def start(self):
        """Start NTP client."""
        self.running = True
        self.logger.info(f"NTP Client starting, connecting to {self.server_host}:{self.server_port}")
        
        # Start sync thread
        sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        sync_thread.start()
        
        # Start slewing thread
        slewing_thread = threading.Thread(target=self._slewing_loop, daemon=True)
        slewing_thread.start()
        
        self.logger.info("NTP Client started successfully")
        return sync_thread, slewing_thread
    
    def _sync_loop(self):
        """Main sync loop - periodically sync with server."""
        sync_interval = self.config.get("sync_interval", 5)
        
        # Wait for server to be ready
        time.sleep(2)
        
        while self.running:
            try:
                self._synchronize()
            except Exception as e:
                self.logger.error(f"Synchronization error: {e}")
                self.sync_failed += 1
            
            time.sleep(sync_interval)
    
    def _synchronize(self):
        """Perform one NTP synchronization cycle."""
        self.sync_attempt += 1
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            # Get timestamps
            t1 = self.clock.get_current_time()
            
            # Send NTP request
            request = NTPMessage.create_request(t1)
            sock.sendto(request, (self.server_host, self.server_port))
            
            # Receive response
            response, _ = sock.recvfrom(1024)
            t4 = self.clock.get_current_time()
            
            sock.close()
            
            # Parse response
            t1_recv, t2, t3 = NTPMessage.parse_response(response)[:3]
            
            # Calculate offset and delay
            offset_sec, delay_sec = NTPMessage.calculate_offset_and_delay(t1, t2, t3, t4)
            offset_ms = offset_sec * 1000
            delay_ms = delay_sec * 1000
            
            # Process NTP response
            result = self.clock.process_ntp_response(offset_ms, delay_ms)
            
            if result["accepted"]:
                self.sync_success += 1
                
                # Log transaction
                log_msg = NTPPacketParser.log_ntp_transaction(t1, t2, t3, t4, offset_ms, delay_ms)
                self.logger.info(
                    f"Sync #{self.sync_attempt} SUCCESS ({result['adjustment_type']})\n{log_msg}"
                )
                
                # CSV logging
                self.csv_logger.log_event(
                    node=self.config["node_name"],
                    event_type="NTP_RESPONSE",
                    current_time_ms=self.clock.get_current_time_ms(),
                    offset_ms=offset_ms,
                    remaining_adjustment_ms=self.clock.clock_adjust_ms,
                    is_slewing=self.clock.is_slewing,
                    drift_ppm=self.clock.drift_rate_ppm,
                    drift_compensation_ppm=self.clock.drift_compensation_ppm,
                    status=f"{result['adjustment_type']} - Delay: {delay_ms:.4f}ms"
                )
            else:
                self.sync_failed += 1
                self.logger.warning(f"Sync #{self.sync_attempt} FAILED")
        
        except socket.timeout:
            self.sync_failed += 1
            self.logger.error(f"Sync #{self.sync_attempt} - Connection timeout")
        except ConnectionRefusedError:
            self.sync_failed += 1
            self.logger.error(f"Sync #{self.sync_attempt} - Server not responding")
        except Exception as e:
            self.sync_failed += 1
            self.logger.error(f"Sync #{self.sync_attempt} - Error: {e}")
    
    def _slewing_loop(self):
        """Handle periodic slewing adjustments."""
        clock_adj = self.clock.clock_adj
        
        while self.running:
            time.sleep(clock_adj)
            
            # Get adjustment status
            adj_status = self.clock.slewing_tick()
            
            if adj_status["is_slewing"] or adj_status["phase_adjustment_ms"] != 0:
                # Log to CSV
                self.csv_logger.log_event(
                    node=self.config["node_name"],
                    event_type="SLEWING_TICK",
                    current_time_ms=self.clock.get_current_time_ms(),
                    offset_ms=self.clock.clock_adjust_ms,
                    phase_adjustment_ms=adj_status["phase_adjustment_ms"],
                    remaining_adjustment_ms=adj_status["remaining_adjustment_ms"],
                    is_slewing=adj_status["is_slewing"],
                    adjustment_count=adj_status["adjustment_count"],
                    drift_ppm=self.clock.drift_rate_ppm,
                    drift_compensation_ppm=self.clock.drift_compensation_ppm
                )
                
                self.logger.debug(
                    f"Slewing tick #{adj_status['adjustment_count']}: "
                    f"Phase adj={adj_status['phase_adjustment_ms']:.4f}ms, "
                    f"Remaining={adj_status['remaining_adjustment_ms']:.4f}ms"
                )
    
    def stop(self):
        """Stop NTP client."""
        self.logger.info("Stopping NTP Client...")
        self.running = False
        self.csv_logger.close()
        
        status = self.clock.get_status()
        self.logger.info(
            f"Client status: {status}\n"
            f"Sync stats: {self.sync_success}/{self.sync_attempt} successful"
        )
    
    def get_stats(self) -> dict:
        """Get client statistics."""
        return {
            "node": self.config["node_name"],
            "sync_attempt": self.sync_attempt,
            "sync_success": self.sync_success,
            "sync_failed": self.sync_failed,
            "clock_status": self.clock.get_status(),
            "running": self.running
        }
