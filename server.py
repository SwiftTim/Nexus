import socket
import threading
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from datetime import datetime

# Server configuration
HOST = '0.0.0.0'
PORT = 5555

# Global console
console = Console()

# State management
channels = {"general": []}
client_channels = {}
last_event = "System started. Waiting for connections..."

def get_dashboard():
    """Generates the Rich dashboard layout."""
    table = Table(title="[bold green]Nexus Server Status[/bold green]", expand=True, border_style="green")
    table.add_column("Property", style="green")
    table.add_column("Value", style="bold green")
    
    table.add_row("Uptime", datetime.now().strftime("%H:%M:%S"))
    table.add_row("Active Connections", str(len(client_channels)))
    table.add_row("Active Channels", ", ".join(channels.keys()))
    
    # Format the last event to be clean
    event_panel = Panel(
        Text(last_event, overflow="ellipsis", justify="center", style="green"),
        title="[bold green]Last Activity[/bold green]",
        border_style="green"
    )
    
    banner = r"""
  _______ _____ __  __      _   _ ______  __  __ _    _  _____ 
 |__   __|_   _|  \/  |    | \ | |  ____| \ \/ /| |  | |/ ____|
    | |    | | | \  / |    |  \| | |__     \  /  | |  | | (___  
    | |    | | | |\/| |    | . ` |  __|     > <  | |  | |\___ \ 
    | |   _| |_| |  | |    | |\  | |____   /  \  | |__| |____) |
    |_|  |_____|_|  |_|    |_| \_|______| /_/\_\ \____/|_____/ 
    """
    
    header = Panel(
        Text(banner, style="bold green", justify="center") + 
        Text("\nSecure Multi-Channel Encryption Gateway", style="italic green", justify="center"),
        border_style="green",
        padding=(1, 2)
    )
    
    return Group(header, table, event_panel)

def update_event(msg):
    """Updates the global last event state."""
    global last_event
    timestamp = datetime.now().strftime("%H:%M:%S")
    last_event = f"[{timestamp}] {msg}"

def broadcast(message, sender_socket, channel_name):
    """Sends a message to all connected clients in a specific channel except the sender."""
    if channel_name in channels:
        for client in channels[channel_name]:
            if client != sender_socket:
                try:
                    client.send(message)
                except:
                    remove(client)

def handle_client(client_socket, addr):
    """Handles communication with a single client."""
    update_event(f"New connection from {addr}")
    
    current_channel = "general"
    channels[current_channel].append(client_socket)
    client_channels[client_socket] = current_channel
    
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break
            
            decoded_msg = message.decode('utf-8')
            
            if decoded_msg.startswith("/join "):
                new_channel = decoded_msg.split(" ")[1]
                channels[current_channel].remove(client_socket)
                
                current_channel = new_channel
                if current_channel not in channels:
                    channels[current_channel] = []
                channels[current_channel].append(client_socket)
                client_channels[client_socket] = current_channel
                
                client_socket.send(f"[SERVER] Joined channel: {current_channel}".encode('utf-8'))
                update_event(f"{addr} switched to channel: {current_channel}")
                continue
            
            elif decoded_msg == "/list":
                channel_list = "[SERVER] Available: " + ", ".join(channels.keys())
                client_socket.send(channel_list.encode('utf-8'))
                continue

            update_event(f"Message in {current_channel} (Encrypted Data Received)")
            broadcast(message, client_socket, current_channel)
        except:
            break
    
    remove(client_socket)
    update_event(f"Client {addr} disconnected.")

def remove(client_socket):
    """Removes a client from all channel tracking."""
    if client_socket in client_channels:
        channel_name = client_channels[client_socket]
        if client_socket in channels[channel_name]:
            channels[channel_name].remove(client_socket)
        del client_channels[client_socket]
        try:
            client_socket.close()
        except:
            pass

def start_server():
    """Initializes and starts the TCP server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    with Live(get_dashboard(), refresh_per_second=4) as live:
        # Monitoring thread to update the UI
        def refresh_ui():
            while True:
                live.update(get_dashboard())
        
        threading.Thread(target=refresh_ui, daemon=True).start()

        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.start()

if __name__ == "__main__":
    start_server()
