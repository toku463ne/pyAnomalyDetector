"""
Super class for all views
"""

from abc import ABC, abstractmethod
from typing import Dict


class View(ABC):
    @abstractmethod
    def show(self, config: Dict) -> None:
        pass

    def check_conn(self) -> bool:
        pass