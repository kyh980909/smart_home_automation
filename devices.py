# Device class definitions
from dataclasses import dataclass


@dataclass
class Device:
    """Simple representation of a controllable device."""

    name: str
    state: bool = False

    def toggle(self) -> None:
        """Toggle the device state."""
        self.state = not self.state


# Pre-defined device list used by the main panel
DEVICE_NAMES = [
    "거실조명",
    "주방조명",
    "가스밸브",
    "보일러",
    "CCTV",
    "에어컨",
]

# Instantiate devices with the default OFF state
DEVICES = [Device(name) for name in DEVICE_NAMES]

