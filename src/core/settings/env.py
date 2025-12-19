from enum import Enum

class Environment(str, Enum):
    """
    Available deployment environments.
    """
    PROD = "PROD"
    DEV = "DEV"
    LOCAL = "LOCAL"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """
        Helper to convert a string (case-insensitive) to the enum.
        Useful when reading from .env or config.
        """
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid environment: {value}. Must be one of {', '.join([e.value for e in cls])}")