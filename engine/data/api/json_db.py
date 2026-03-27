"""
FILE: data/api/json_db.py
ROLE: The "Basement" (JSONDatabase).

DESCRIPTION:
This is the lowest level of our data storage. While other parts of the app 
talk about "Units" and "Maps", this file only cares about "Files" and "Folders".

It handles the 'dirty work' of:
1. Converting a name (like "Rifleman") into a real file path (like "content/presets/agents/Rifleman.json").
2. Opening that file and reading the raw text.
3. Converting that text into a Python Dictionary that the rest of the app can understand.
"""

import json
import os
import glob
from typing import Any, Dict, List, Optional
from .base_db import BaseDB

class JSONDatabase(BaseDB):
    """
    A simple database that stores every 'Key' as a separate '.json' file on your hard drive.
    """
    def __init__(self, root_dir: str):
        # The 'root_dir' is the top-level folder where all these files are kept (usually 'content/').
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        """
        CONVERTER: Turns a database key into a windows/linux file path.
        If the key is already an absolute path, it respects it.
        """
        safe_key = key.replace("\\", "/")
        
        # If the key is already absolute, don't join with root_dir
        if os.path.isabs(safe_key):
            path = safe_key
        else:
            path = os.path.join(self.root_dir, safe_key)
            
        if not path.endswith(".json"):
            path += ".json"
        return path

    def get(self, key: str) -> Optional[Any]:
        """READ: Opens a file and returns its content as a Python object."""
        path = self._get_path(key)
        # print(f"DEBUG: JSONDatabase.get path='{path}'")
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"JSONDatabase Error: Failed to read {key} - {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """WRITE: Takes a Python object and saves it as a text file on the disk."""
        path = self._get_path(key)
        print(f"DEBUG: JSONDatabase.set key='{key}' -> path='{path}'")
        # Ensure the folders exist before we try to save the file.
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, 'w') as f:
                # Use compact serialization (no indents/spaces) for efficiency
                json.dump(value, f, indent=None, separators=(',', ':'))
            return True
        except IOError as e:
            print(f"JSONDatabase Error: Failed to write {key} - {e}")
            return False

    def delete(self, key: str) -> bool:
        """ERASE: Permanently deletes a JSON file from the disk."""
        path = self._get_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except IOError:
                return False
        return False

    def exists(self, key: str) -> bool:
        """CHECK: Returns True if the specified file actually exists on the disk."""
        return os.path.exists(self._get_path(key))

    def keys(self, pattern: str = "**/*") -> List[str]:
        """
        SEARCH: Finds all files that match a certain pattern (like "Agents/*.json").
        It returns them as 'Keys' (names without the .json at the end).
        """
        search_path = os.path.join(self.root_dir, pattern)
        if not search_path.endswith(".json") and not search_path.endswith("*"):
           search_path += ".json"
        
        # Look through all sub-folders recursively.
        matched_files = glob.glob(search_path, recursive=True)
        keys = []
        
        for file_path in matched_files:
            if not os.path.isfile(file_path): continue
            
            # Figure out the path relative to the root folder.
            rel_path = os.path.relpath(file_path, self.root_dir)
            
            # Remove the ".json" extension.
            if rel_path.endswith(".json"):
                rel_path = rel_path[:-5]
                
            keys.append(rel_path.replace("\\", "/"))
            
        return keys

    def get_all(self, pattern: str = "**/*") -> Dict[str, Any]:
        """BATCH READ: Finds many files at once and returns them all in one big dictionary."""
        result = {}
        for key in self.keys(pattern):
            val = self.get(key)
            if val is not None:
                result[key] = val
        return result

    def clear(self) -> bool:
        """
        DANGEROUS: This would delete everything in the database.
        It is currently disabled to prevent accidental data loss.
        """
        print("JSONDatabase Warning: Clear operation is restricted.")
        return False
