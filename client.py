import socket
import threading
import crypto_utils
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
import ssl
import time

# Initialize Rich console
console = Console()

# PRODUCTION SETTINGS
DEFAULT_PORT = 443 
DEFAULT_HOST = "nexus-main.fly.dev"

# Global encryption key (derived from password)
encryption_key = None

def receive_messages(client_socket):
    """Continuously receives messages from the server."""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data: break
            
            message = data.decode('utf-8', errors='ignore')
            if message:
                timestamp = datetime.now().strftime("%H:%M:%S")
                if message.startswith("[SERVER]"):
                    console.print(f"[bold yellow][{timestamp}] {message}[/bold yellow]")
                else:
                    try:
                        decrypted = crypto_utils.decrypt_message(message, encryption_key)
                        if ":" in decrypted:
                            user, content = decrypted.split(":", 1)
                            console.print(f"[bold green][{timestamp}] {user.strip()}:[/bold green] [bright_green]{content.strip()}[/bright_green]")
                        else:
                            console.print(f"[bold red][{timestamp}] [DECRYPTED ERROR] {decrypted}[/bold red]")
                    except:
                        console.print(f"[bold red][{timestamp}] [ENCRYPTED MSG RECEIVED][/bold red]")
        except: break

def start_client():
    """Connects to the server using SSL Tunneling."""
    global encryption_key
    
    console.clear()
    
    banner = r"""
  _______ _____ __  __      _   _ ______  __  __ _    _  _____ 
 |__   __|_   _|  \/  |    | \ | |  ____| \ \/ /| |  | |/ ____|
    | |    | | | \  / |    |  \| | |__     \  /  | |  | | (___  
    | |    | | | |\/| |    | . ` |  __|     > <  | |  | |\___ \ 
    | |   _| |_| |  | |    | |\  | |____   /  \  | |__| |____) |
    |_|  |_____|_|  |_|    |_| \_|______| /_/\_\ \____/|_____/ 
    """
    
    console.print(Panel.fit(
        Text(banner, style="bold green", justify="center") + 
        Text("\n🚀 SECURE CLIENT GATEWAY 🚀", style="italic green", justify="center"),
        border_style="green"
    ))
    
    console.print("[italic white]Note: For global hosting, use 'nexus-main.fly.dev'[/italic white]")
    server_ip = Prompt.ask("[bold green]Enter Server Hostname[/bold green]", default=DEFAULT_HOST)
    server_port = Prompt.ask("[bold green]Enter Port[/bold green]", default=str(DEFAULT_PORT))
    
    try:
        server_port = int(server_port)
    except:
        server_port = DEFAULT_PORT

    console.print(f"[italic yellow]📡 Initiating SSL Handshake with {server_ip}...[/italic yellow]")
    
    try:
        # Create a standard TCP socket
        raw_socket = socket.create_connection((server_ip, server_port), timeout=15)
        
        # WRAP IT IN SSL (This is the magic part)
        context = ssl.create_default_context()
        # On Fly.io, we use the hostname for the SSL certificate
        client = context.wrap_socket(raw_socket, server_hostname=server_ip)
        
        console.print("[bold green][✔] Secure Tunnel Established[/bold green]")
    except Exception as e:
        console.print(f"[bold red][ERROR] Secure Connection Failed: {e}[/bold red]")
        return

    username = Prompt.ask("[bold green]Enter your username[/bold green]")
    password = Prompt.ask("[bold green]Enter channel password[/bold green]", password=True)
    encryption_key = crypto_utils.derive_key(password)
    
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.daemon = True
    receive_thread.start()

    console.print(f"\n[bold green][SUCCESS][/bold green] Welcome, [bold green]{username}[/bold green]!")
    console.print("[italic green]Commands: /join <name>, /list, /exit[/italic green]\n")
    
    while True:
        try:
            msg = Prompt.ask("", console=console)
            if not msg: continue
            if msg.lower() == '/exit': break
            
            if msg.startswith('/'):
                if msg.startswith('/join'):
                    console.print(f"[italic yellow][⏳] Requesting access to '{msg[6:].strip()}'...[/italic yellow]")
                client.sendall(msg.encode('utf-8'))
            else:
                full_msg = f"{username}: {msg}"
                encrypted_msg = crypto_utils.encrypt_message(full_msg, encryption_key)
                client.sendall(encrypted_msg.encode('utf-8'))
        except: break

    client.close()
    console.print("[bold green]Tunnel closed. Goodbye![/bold green]")

if __name__ == "__main__":
    start_client()
