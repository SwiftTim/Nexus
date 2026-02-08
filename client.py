import socket
import threading
import crypto_utils
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

# Initialize Rich console
console = Console()

# Client configuration
DEFAULT_PORT = 5555

# Global encryption key (derived from password)
encryption_key = None

def receive_messages(client_socket):
    """Continuously receives messages from the server."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                timestamp = datetime.now().strftime("%H:%M:%S")
                if message.startswith("[SERVER]"):
                    console.print(f"[bold green][{timestamp}] {message}[/bold green]")
                else:
                    # Attempt to decrypt
                    decrypted = crypto_utils.decrypt_message(message, encryption_key)
                    if ":" in decrypted:
                        user, content = decrypted.split(":", 1)
                        console.print(f"[bold green][{timestamp}] {user.strip()}:[/bold green] [bright_green]{content.strip()}[/bright_green]")
                    else:
                        console.print(f"[bold red][{timestamp}] [DECRYPTED ERROR] {decrypted}[/bold red]")
            else:
                break
        except Exception as e:
            console.print(f"[bold red][ERROR] Connection lost or decryption failed: {e}[/bold red]")
            break

def start_client():
    """Connects to the server and handles user input."""
    global encryption_key
    
    console.clear()
    console.print(Panel.fit("🚀 [bold green]Encrypted Terminal Chat[/bold green] 🚀", border_style="green"))
    
    server_ip = Prompt.ask("[bold green]Enter Server IP[/bold green]", default="127.0.0.1")
    server_port = Prompt.ask("[bold green]Enter Server Port[/bold green]", default=str(DEFAULT_PORT))
    
    try:
        server_port = int(server_port)
    except ValueError:
        console.print("[bold red][ERROR] Invalid port number. Using default 5555.[/bold green]")
        server_port = DEFAULT_PORT

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_ip, server_port))
    except (ConnectionRefusedError, socket.gaierror) as e:
        console.print(f"[bold red][ERROR] Could not connect to {server_ip}:{server_port}. {e}[/bold red]")
        return

    username = Prompt.ask("[bold green]Enter your username[/bold green]")
    password = Prompt.ask("[bold green]Enter channel password (encryption key)[/bold green]", password=True)
    encryption_key = crypto_utils.derive_key(password)
    
    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.daemon = True
    receive_thread.start()

    console.print(f"\n[bold green][CONNECTED][/bold green] Welcome, [bold green]{username}[/bold green]!")
    console.print("[italic green]Commands: /join <channel>, /list, /exit[/italic green]\n")
    
    while True:
        try:
            msg = Prompt.ask("", console=console)
            if msg.lower() == '/exit':
                break
            
            if msg.startswith('/'):
                # Send command directly (unencrypted for server to process)
                client.send(msg.encode('utf-8'))
            else:
                full_msg = f"{username}: {msg}"
                # Encrypt the message before sending
                encrypted_msg = crypto_utils.encrypt_message(full_msg, encryption_key)
                client.send(encrypted_msg.encode('utf-8'))
        except EOFError:
            break
        except KeyboardInterrupt:
            break

    client.close()
    console.print("[bold green]Goodbye![/bold green]")

if __name__ == "__main__":
    start_client()
