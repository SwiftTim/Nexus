import socket
import threading
import sys
import os
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from datetime import datetime
import time
import re

# Use port 10000 to avoid common proxy filters
PORT = 10000

# Global console
console = Console()
is_terminal = sys.stdout.isatty() and not os.path.exists('/.dockerenv')

# State management
state_lock = threading.Lock()
channels = {"general": []}
client_channels = {}
last_event = "System started. Waiting for connections..."

def get_dashboard():
    """Generates the Rich dashboard layout."""
    table = Table(title="[bold green]Nexus Status[/bold green]", expand=True, border_style="green")
    table.add_column("Property", style="green")
    table.add_column("Value", style="bold green")
    with state_lock:
        table.add_row("Uptime", datetime.now().strftime("%H:%M:%S"))
        table.add_row("Connections", str(len(client_channels)))
        table.add_row("Channels", ", ".join(channels.keys()))
    return Group(Panel(Text("TIM NEXUS", style="bold green", justify="center"), border_style="green"), table)

def update_event(msg):
    """Updates the global last event state."""
    global last_event
    timestamp = datetime.now().strftime("%H:%M:%S")
    last_event = f"[{timestamp}] {msg}"
    print(last_event, flush=True)

def broadcast(message, sender_socket, channel_name):
    """Sends a message to all connected clients in a specific channel except the sender."""
    with state_lock:
        if channel_name in channels:
            targets = list(channels[channel_name])
        else:
            return
    for client in targets:
        if client != sender_socket:
            try:
                client.sendall(message)
            except:
                remove(client)

def handle_client(client_socket, addr):
    """Handles communication with a single client."""
    update_event(f"New connection from {addr}")
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    current_channel = "general"
    with state_lock:
        channels[current_channel].append(client_socket)
        client_channels[client_socket] = current_channel
    
    try:
        while True:
            try:
                data = client_socket.recv(4096)
                if not data: break
                
                msg = data.decode('utf-8', errors='ignore')
                
                if msg.startswith("/join "):
                    new_chan = re.sub(r'[<>{}\[\]]', '', msg[6:].strip()) or "general"
                    with state_lock:
                        if client_socket in channels[current_channel]:
                            channels[current_channel].remove(client_socket)
                        if new_chan not in channels: channels[new_chan] = []
                        channels[new_chan].append(client_socket)
                        client_channels[client_socket] = new_chan
                        current_channel = new_chan
                    client_socket.sendall(f"[SERVER] ACCESS GRANTED: Joined '{current_channel}'".encode('utf-8'))
                    update_event(f"{addr} -> {current_channel}")
                elif msg == "/list":
                    with state_lock:
                        resp = "[SERVER] Available: " + ", ".join(channels.keys())
                    client_socket.sendall(resp.encode('utf-8'))
                else:
                    broadcast(data, client_socket, current_channel)
            except: break
    finally:
        remove(client_socket)
        update_event(f"Disconnected: {addr}")

def remove(client_socket):
    """Removes a client from all channel tracking."""
    with state_lock:
        if client_socket in client_channels:
            chan = client_channels[client_socket]
            if chan in channels and client_socket in channels[chan]: channels[chan].remove(client_socket)
            del client_channels[client_socket]
            try: client_socket.close()
            except: pass

def start_server():
    """Starts the TCP server on both IPv4 and IPv6."""
    # Binding to '::' with IPv6_V6ONLY=0 allows both IPv4 and IPv6
    try:
        server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('::', PORT))
        server.listen(50)
        print(f"🚀 NEXUS LIVE ON PORT {PORT} (IPv4/IPv6 Dual-Stack Support)", flush=True)
        
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    start_server()
