from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> dict:
        """Parse the given document file and return a dictionary of extracted data."""
        pass
