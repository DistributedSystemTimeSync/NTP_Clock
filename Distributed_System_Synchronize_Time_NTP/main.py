"""
NTP Synchronization System - Main Entry Point
Simulates distributed time synchronization using NTP protocol
"""

import sys
import time
import signal
import os
from src.server import NTPServer
from src.client import NTPClient


def run_server(config_file: str, duration: int = None):
    """Run NTP Server."""
    print(f"Starting NTP Server with config: {config_file}")
    
    server = NTPServer(config_file=config_file)
    sync_thread, slewing_thread = server.start()
    
    try:
        start_time = time.time()
        while True:
            if duration and (time.time() - start_time) > duration:
                break
            time.sleep(1)
            
            # Print status every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                stats = server.get_stats()
                print(f"\n[{stats['node']}] Time: {stats['clock_status']['current_time']}, "
                      f"Requests: {stats['request_count']}")
    
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    finally:
        server.stop()
        print("Server stopped")


def run_client(config_file: str, server_host: str = "server", duration: int = 180):
    """Run NTP Client."""
    print(f"Starting NTP Client with config: {config_file}")
    print(f"Connecting to server at {server_host}")
    
    client = NTPClient(config_file=config_file, server_host=server_host)
    sync_thread, slewing_thread = client.start()
    
    try:
        start_time = time.time()
        last_print = 0
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > duration:
                break
            
            # Print status every 30 seconds
            if elapsed - last_print >= 30:
                stats = client.get_stats()
                status = stats['clock_status']
                print(f"\n[{status['node']}] "
                      f"Time: {status['current_time']}, "
                      f"Offset: {status['offset_ms']:+.4f}ms, "
                      f"Syncs: {stats['sync_success']}/{stats['sync_attempt']}, "
                      f"Slewing: {status['is_slewing']}")
                last_print = elapsed
            
            time.sleep(1)
        
        print(f"\n[Client] Simulation completed ({duration}s)")
    
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    finally:
        client.stop()
        print("Client stopped")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <server|client> [node_name]")
        print("  Examples:")
        print("    python main.py server")
        print("    python main.py client node_b")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    # Get configuration from environment or arguments
    config_file = os.getenv('CONFIG_FILE', f'configs/{mode}_config.json')
    duration = int(os.getenv('DURATION', '180'))
    
    if mode == "server":
        run_server(config_file, duration=duration)
    elif mode == "client":
        node_name = sys.argv[2] if len(sys.argv) > 2 else "node_b"
        config_file = f"configs/{node_name}_config.json"
        server_host = os.getenv('SERVER_HOST', 'server_a')
        run_client(config_file, server_host=server_host, duration=duration)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
