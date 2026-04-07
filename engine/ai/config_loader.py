import json
import os

class ConfigLoader:
    """Loads configuration variables from JSON to prevent magic numbers."""
    
    _configs = {}
    _BASE_DIR = "config"

    @classmethod
    def load(cls, config_name):
        path = os.path.join(cls._BASE_DIR, f"{config_name}.json")
        try:
            with open(path, 'r') as f:
                cls._configs[config_name] = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config {config_name}: {e}")
            cls._configs[config_name] = {}
        return cls._configs[config_name]

    @classmethod
    def get(cls, config_name, path=None, default=None):
        if config_name not in cls._configs:
            cls.load(config_name)
            
        data = cls._configs.get(config_name, {})
        
        if not path:
            return data
            
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, None)
            else:
                return default
            if data is None:
                return default
                
        return data
