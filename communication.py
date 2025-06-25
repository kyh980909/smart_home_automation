"""Socket-based communication utilities for the panel and chatbot."""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Callable, Dict


class Communicator:
    """Simple JSON socket communicator."""

    def __init__(self, port: int = 5555) -> None:
        self.port = port
        self.host = "127.0.0.1"

    # ------------------------------------------------------------------
    def start_server(self, message_handler: Callable[[Dict[str, Any]], None]) -> None:
        """Start a background server that invokes ``message_handler`` for each message."""

        def run() -> None:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            while True:
                conn, _ = server.accept()
                with conn:
                    data = conn.recv(4096)
                    if not data:
                        continue
                    try:
                        msg = json.loads(data.decode("utf-8"))
                    except json.JSONDecodeError:
                        msg = {"type": "text", "data": data.decode("utf-8")}
                    message_handler(msg)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    # ------------------------------------------------------------------
    def send_message(self, host: str, port: int, message: Dict[str, Any]) -> None:
        """Send ``message`` as JSON to ``host``/``port``."""
        try:
            with socket.create_connection((host, port), timeout=1) as sock:
                sock.sendall(json.dumps(message).encode("utf-8"))
        except OSError:
            # Ignore connection errors if the receiver is not available
            pass

    # ------------------------------------------------------------------
    def create_recommendation(self, device: str, time: str, action: str) -> Dict[str, Any]:
        """Return a recommendation message payload."""
        return {
            "type": "recommendation",
            "data": {"device": device, "time": time, "action": action},
        }

    def create_rule_command(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Return a rule creation command payload."""
        return {"type": "create_rule", "data": rule}


# ----------------------------------------------------------------------
# Backwards compatible helpers used by existing modules
_default = Communicator()


def start_server(on_message: Callable[[str], None]) -> None:
    """Start a simple server that forwards only the message text to ``on_message``."""

    def wrapper(msg: Dict[str, Any]) -> None:
        if msg.get("type") == "text":
            on_message(str(msg.get("data")))
        else:
            on_message(json.dumps(msg, ensure_ascii=False))

    _default.start_server(wrapper)


def send_message(message: str) -> None:
    """Send a plain text ``message`` to the default server."""
    _default.send_message(_default.host, _default.port, {"type": "text", "data": message})
