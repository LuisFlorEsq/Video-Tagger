from dataclasses import dataclass
from typing import Optional


@dataclass
class Label:
    """Represents a label that can be assigned to fragments."""

    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color for future UI use

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Label name cannot be empty")
        self.name = self.name.strip()
