from abc import ABC, abstractmethod
import logging


class BaseAnalyzer(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze(self, domain: str) -> dict:
        """Run analysis on the given domain and return results as a dict."""
        pass
