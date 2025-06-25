# Panel-Chatbot communication module

"""Simple socket-based communication between the panel and chatbot."""

from __future__ import annotations

import socket
import threading
from typing import Callable


HOST = "127.0.0.1"
PORT = 5555


def start_server(on_message: Callable[[str], None]) -> None:
    """Start a background server that triggers ``on_message`` for each message."""

    def run() -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        while True:
            conn, _ = server.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    on_message(data.decode("utf-8"))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def send_message(message: str) -> None:
    """Send ``message`` to the server, ignoring connection errors."""

    try:
        with socket.create_connection((HOST, PORT), timeout=1) as sock:
            sock.sendall(message.encode("utf-8"))
    except OSError:
        # Server might not be running
        pass

