from abc import ABC, abstractmethod

class ProtocolParser(ABC):
    """
    Abstract Base Class for protocol parsers.
    Ensures that any new parser implements a 'parse' method.
    """

    @abstractmethod
    def parse(self, message_str: str) -> dict:
        """
        Parses a raw message string into a structured dictionary.

        Args:
            message_str: The raw message from the source.

        Returns:
            A dictionary representing the structured message, or None if parsing fails.
        """
        pass