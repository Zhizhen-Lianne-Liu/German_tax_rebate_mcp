"""
Session manager for persistent state across MCP tool calls.
Stores session data to disk to survive server restarts.

V2: Supports incremental data collection with nested keys and categories.
"""

import json
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime


class SessionManager:
    """Manage persistent session state with nested key support"""

    def __init__(self, session_file: str = "data/session.json"):
        self.session_file = Path(session_file)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load session from disk, initialize V2 structure if empty"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self._data = data
            except (json.JSONDecodeError, IOError):
                self._data = self._init_v2_structure()
        else:
            self._data = self._init_v2_structure()

    def _init_v2_structure(self) -> Dict:
        """Initialize V2 categorized session structure"""
        return {
            "personal_info": {},
            "income_info": {},
            "tax_status": {},
            "work_info": {},
            "calculations": {},
            "receipts": {"scanned": False, "summary": None},
            "deductions": None,
            "xml_generated": False,
            "_last_updated": datetime.now().isoformat()
        }

    def _save(self):
        """Save session to disk"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self._data, f, indent=2, default=str)
            print(f"DEBUG SessionManager: Saved session to {self.session_file}")
        except TypeError as e:
            print(f"ERROR SessionManager: JSON serialization failed: {e}")
            print(f"  Data types: {[(k, type(v)) for k, v in self._data.items()]}")
            raise
        except IOError as e:
            print(f"ERROR SessionManager: Could not write to file: {e}")
            raise

    def set(self, key: str, value: Any):
        """Set a session value"""
        print(f"DEBUG SessionManager.set(): key='{key}', value_type={type(value)}")

        # Convert Pydantic models to dict for JSON serialization
        if hasattr(value, 'model_dump'):
            print(f"  Converting Pydantic model to dict")
            value = value.model_dump()
        elif hasattr(value, '__dict__'):
            # Handle other objects
            try:
                print(f"  Converting object with __dict__ to dict")
                value = {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
            except:
                print(f"  Failed to convert, using str()")
                value = str(value)

        self._data[key] = value
        self._data['_last_updated'] = datetime.now().isoformat()
        print(f"  Data added to _data dict, total keys: {list(self._data.keys())}")
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a session value"""
        self._load()  # Reload from disk to get latest
        return self._data.get(key, default)

    def clear(self):
        """Clear all session data"""
        self._data = {}
        self._save()

    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        self._load()
        return key in self._data

    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """
        Get a nested session value using dot notation.

        Example: get_nested('personal_info.first_name')
        """
        self._load()
        keys = key_path.split('.')
        value = self._data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set_nested(self, key_path: str, value: Any):
        """
        Set a nested session value using dot notation.

        Example: set_nested('personal_info.first_name', 'Anna')
        """
        # Convert Pydantic models
        if hasattr(value, 'model_dump'):
            value = value.model_dump()

        keys = key_path.split('.')
        data = self._data

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]

        # Set the final key
        data[keys[-1]] = value
        self._data['_last_updated'] = datetime.now().isoformat()
        self._save()

    def merge(self, category: str, updates: Dict[str, Any]):
        """
        Merge updates into a category, preserving existing values.

        Example: merge('personal_info', {'first_name': 'Anna', 'last_name': 'Schmidt'})
        """
        self._load()

        if category not in self._data:
            self._data[category] = {}

        # Convert Pydantic models in updates
        for key, value in updates.items():
            if hasattr(value, 'model_dump'):
                updates[key] = value.model_dump()

        # Merge (update only provided fields)
        self._data[category].update(updates)
        self._data['_last_updated'] = datetime.now().isoformat()
        self._save()

    def get_all(self) -> Dict:
        """Get the entire session data"""
        self._load()
        return self._data.copy()


# Global session instance
_session = None

def get_session() -> SessionManager:
    """Get or create the global session instance"""
    global _session
    if _session is None:
        _session = SessionManager()
    return _session
