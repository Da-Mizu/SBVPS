# src/data/__init__.py
from .storage import Database
from .collector import FakeDataCollector

__all__ = ["Database", "FakeDataCollector"]
