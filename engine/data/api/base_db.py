"""
FILE: data/api/base_db.py
ROLE: The "Blueprint" (BaseDB Interface).

DESCRIPTION:
This file defines the 'Rules' for how any database in our system must behave. 
By creating this 'Abstract Base Class' (ABC), we ensure that whether we are 
using JSON files or a Pro-level database like Redis, they all use the same 
commands (get, set, delete).

This makes the rest of the app much easier to write because it doesn't have 
to care HOW the data is stored, only that it CAN be stored.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseDB(ABC):
    """
    The Master Template for all database types.
    Any new database MUST follow these rules.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """READ: Every database must have a 'get' command to retrieve data."""
        pass
        
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """WRITE: Every database must have a 'set' command to save data."""
        pass
        
    @abstractmethod
    def delete(self, key: str) -> bool:
        """ERASE: Every database must have a 'delete' command to remove data."""
        pass
        
    @abstractmethod
    def exists(self, key: str) -> bool:
        """CHECK: Every database must be able to tell if a piece of data exists."""
        pass
        
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """SEARCH: Every database must be able to search for multiple items."""
        pass
        
    @abstractmethod
    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """BATCH READ: Every database must be able to retrieve multiple items at once."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """WIPE: Every database must have a way to clear all its data."""
        pass
