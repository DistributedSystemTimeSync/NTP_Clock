"""
NTP Server Implementation (Stratum 1)
"""

import socket
import threading
import time
import json
from pathlib import Path
from src.ntp_clock import NTPClock
from src.ntp_protocol import NTPMessage, NTPPacketParser
from src.logger import setup_logger, CSVLogger


class NTPServer:
    """
    NTP Server (Stratum 1) - Reference time source.
    Listens for NTP requests and responds with accurate timestamps.
    """
    
    def __init__(
        self,
        config_file: str,
        host: str = "0.0.0.0",
        port: int = 123
    ):
        self.config = self._load_config(config_file)
        self.host = host
        self.port = port
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
            f"NTPServer-{self.config['node_name']}",
            str(log_dir / f"server_{self.config['node_name']}.log"),
            level=20
        )
        
        # CSV logging
        self.csv_logger = CSVLogger(
            str(Path(self.config.get("result_dir", "results")) / 
                f"server_{self.config['node_name']}.csv")
        )
        
        self.request_count = 0
        self.socket = None
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def start(self):
        """Start NTP server."""
        self.running = True
        self.logger.info(f"NTP Server starting on {self.host}:{self.port}")
        
        # Start server thread
        server_thread = threading.Thread(target=self._server_loop, daemon=True)
        server_thread.start()
        
        # Start slewing thread
        slewing_thread = threading.Thread(target=self._slewing_loop, daemon=True)
        slewing_thread.start()
        
        self.logger.info("NTP Server started successfully")
        return server_thread, slewing_thread
    
    def _server_loop(self):
        """Main server loop - handle NTP requests."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.logger.info(f"Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    # Receive NTP request
                    data, client_addr = self.socket.recvfrom(1024)
                    self.request_count += 1
                    
                    # Parse request
                    t1 = NTPMessage.parse_request(data)
                    t2 = self.clock.get_current_time()
                    
                    # Prepare response
                    t3 = self.clock.get_current_time()
                    response = NTPMessage.create_response(t1, t2, t3)
                    
                    # Send response
                    self.socket.sendto(response, client_addr)
                    
                    # Log transaction
                    self.logger.debug(
                        f"Request #{self.request_count} from {client_addr}: "
                        f"t1={NTPMessage.format_timestamp_readable(t1)}, "
                        f"t2={NTPMessage.format_timestamp_readable(t2)}, "
                        f"t3={NTPMessage.format_timestamp_readable(t3)}"
                    )
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error handling request: {e}")
        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
    
    def _slewing_loop(self):
        """Handle periodic slewing adjustments."""
        clock_adj = self.clock.clock_adj
        
        while self.running:
            time.sleep(clock_adj)
            
            # Get adjustment status
            adj_status = self.clock.slewing_tick()
            
            # Log to CSV
            status_msg = f"Request count: {self.request_count}"
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
                drift_compensation_ppm=self.clock.drift_compensation_ppm,
                status=status_msg
            )
    
    def stop(self):
        """Stop NTP server."""
        self.logger.info("Stopping NTP Server...")
        self.running = False
        if self.socket:
            self.socket.close()
        self.csv_logger.close()
        
        status = self.clock.get_status()
        self.logger.info(f"Server status: {status}")
    
    def get_stats(self) -> dict:
        """Get server statistics."""
        return {
            "node": self.config["node_name"],
            "request_count": self.request_count,
            "clock_status": self.clock.get_status(),
            "running": self.running
        }
