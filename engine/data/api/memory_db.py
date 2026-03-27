"""
FILE: data/api/memory_db.py
ROLE: The "Working Memory" (MemoryDatabase).

DESCRIPTION:
This file provides a way to store data only while the program is running. 
Unlike the JSONDatabase which saves to your hard drive, this one keeps everything 
in the computer's RAM (Random Access Memory).

Why use this?
1. It is incredibly fast.
2. It is perfect for temporary data that doesn't need to be kept forever.
3. It acts as a "Mock" (a fake version) of a professional database like Redis.
"""

from typing import Any, Dict, List, Optional
import fnmatch
from .base_db import BaseDB

class MemoryDatabase(BaseDB):
    """
    A simple 'In-Memory' storage system that uses a Python Dictionary.
    Now includes LRU (Least Recently Used) pruning for memory efficiency.
    """
    def __init__(self, max_entries: int = 10000):
        # This is where all the data is actually kept during the session.
        self._data: Dict[str, Any] = {}
        self._max_entries = max_entries
        self._access_history: List[str] = [] # Tracks order of access for LRU

    def get(self, key: str) -> Optional[Any]:
        """READ: Retrieves a value and updates its rank in the LRU history."""
        if key in self._data:
            # Move to the end of history (most recent)
            if key in self._access_history:
                self._access_history.remove(key)
            self._access_history.append(key)
            return self._data[key]
        return None
        
    def set(self, key: str, value: Any) -> bool:
        """WRITE: Stores information and prunes memory if limit exceeded."""
        # 1. Update data
        self._data[key] = value
        
        # 2. Update LRU history
        if key in self._access_history:
            self._access_history.remove(key)
        self._access_history.append(key)
        
        # 3. Prune if over limit
        while len(self._data) > self._max_entries:
            oldest_key = self._access_history.pop(0)
            if oldest_key in self._data:
                del self._data[oldest_key]
                # print(f"LRU: Evicted oldest key '{oldest_key}'")
                
        return True
        
    def delete(self, key: str) -> bool:
        """ERASE: Removes a specific piece of information from the memory."""
        if key in self._data:
            del self._data[key]
            if key in self._access_history:
                self._access_history.remove(key)
            return True
        return False
        
    def exists(self, key: str) -> bool:
        """CHECK: Returns True if the memory contains a specific key."""
        return key in self._data
        
    def keys(self, pattern: str = "*") -> List[str]:
        """
        SEARCH: Finds all 'Names' (keys) currently stored in memory.
        If a 'pattern' like 'Agent:*' is provided, it only returns names starting with Agent.
        """
        if pattern == "*":
            return list(self._data.keys())
        
        # This part filters the list to only show names that match the pattern.
        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
        
    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """BATCH READ: Gets all data that matches a search pattern at once."""
        match_keys = self.keys(pattern)
        return {k: self._data[k] for k in match_keys}

    def clear(self) -> bool:
        """WIPE: Deletes every single piece of data from the working memory."""
        self._data.clear()
        return True
