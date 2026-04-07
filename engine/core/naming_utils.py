import re
import os

class NamingUtils:
    """Central utility for validating, sanitizing, and formatting strings and file paths."""

    _INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
    
    @classmethod
    def sanitize_filename(cls, filename: str, replacement: str = "_") -> str:
        """
        Removes Windows-illegal characters from a filename safely.
        Valid: `my_file.json` -> `my_file.json`
        Invalid: `Test:Project?` -> `Test_Project_`
        """
        if not filename:
            return "unnamed"
        return cls._INVALID_FILENAME_CHARS.sub(replacement, str(filename))

    @classmethod
    def sanitize_path(cls, path_string: str) -> str:
        """
        Sanitizes a path string while preserving directory separators (/ and \).
        """
        if not path_string:
            return ""
        
        # Split by / or \ into parts
        parts = path_string.replace("\\", "/").split("/")
        
        sanitized_parts = []
        for i, part in enumerate(parts):
            # Allow drive letter colon at index 0 (e.g. C:)
            if i == 0 and len(part) == 2 and part[1] == ':':
                sanitized_parts.append(part)
            else:
                sanitized_parts.append(cls.sanitize_filename(part))
                
        return "/".join(sanitized_parts)

    @classmethod
    def generate_id(cls, name: str) -> str:
        """
        Generates a lowercase, underscore-separated ID string.
        e.g., "Main Battle Tank" -> "main_battle_tank"
        """
        if not name:
            return "unnamed_entity"
        return cls.sanitize_filename(name.lower().replace(" ", "_"), replacement="_")
