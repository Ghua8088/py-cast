import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from src.utils.secure_store import secure_load, secure_save

class VaultManager:
    """
    Manages secure credential storage using the OS's native keyring service.
    
    This class handles the interface with the `keyring` library to securely store passwords
    in Windows Credential Manager, macOS Keychain, or Linux Secret Service.
    It also maintains a local JSON registry of stored keys (service/username pairs only)
    to allow listing and managing credentials, as the keyring API doesn't always 
    support listing all stored items across backends.
    """
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.vault_file = config_dir / "vault_keys.json"
        
        # Simple locked state
        self.locked = True
        self.pin_hash = None
        self._load_pin()

        # Load known keys registry
        # Format: [{"service": "GitHub", "username": "octocat"}, ...]
        self.keys = self._load_keys()

    def _load_pin(self):
        """Load vault master PIN hash from config if exists."""
        pin_file = self.config_dir / "vault_settings.json"
        
        data = secure_load(pin_file)
        if hasattr(data, 'get'):
            self.pin_hash = data.get("pin_hash")

    def set_pin(self, pin: str):
        """Set a master PIN for vault access."""
        if not pin or len(pin) < 4:
            return False

        hashed = hashlib.sha256(pin.encode()).hexdigest()
        self.pin_hash = hashed
        self.locked = False # Auto-unlock on create

        pin_file = self.config_dir / "vault_settings.json"
        secure_save(pin_file, {"pin_hash": hashed})
        """Unlock the vault for this session."""
        if not self.pin_hash:
            return True # No pin set means unlocked
            
        if hashlib.sha256(pin.encode()).hexdigest() == self.pin_hash:
            self.locked = False
            return True
        return False
        
    def lock(self):
        """Lock the vault."""
        if self.pin_hash:
            self.locked = True

    def is_setup(self) -> bool:
        """Check if vault has been initialized with a PIN."""
        return self.pin_hash is not None

    def _load_keys(self) -> List[Dict[str, str]]:
        """Load the registry of known credentials."""
        data = secure_load(self.vault_file)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'keys' in data: # In case we saved it as a dict
            return data['keys']
        return []

    def _save_keys(self):
        """Save the registry of known credentials."""
        secure_save(self.vault_file, self.keys)

    def save_credential(self, service: str, username: str, password: str) -> bool:
        """
        Securely save a password to the OS keychain.
        """
        import keyring
        try:
            keyring.set_password(service, username, password)
            
            # Add to known keys if not exists
            entry = {"service": service, "username": username}
            
            # check if exists to avoid duplicates
            exists = False
            for k in self.keys:
                if k["service"] == service and k["username"] == username:
                    exists = True
                    break
            
            if not exists:
                self.keys.append(entry)
                self._save_keys()
            return True
        except Exception as e:
            print(f"Error saving credential: {e}")
            return False
    
    def get_credential(self, service: str, username: str) -> Optional[str]:
        """
        Retrieve a password from the OS keychain.
        """
        import keyring
        try:
            return keyring.get_password(service, username)
        except Exception as e:
            print(f"Error retrieving credential: {e}")
            return None

    def delete_credential(self, service: str, username: str) -> bool:
        """
        Remove a password from the OS keychain and the local registry.
        """
        import keyring
        import keyring.errors
        success = False
        try:
            keyring.delete_password(service, username)
            success = True
        except keyring.errors.PasswordDeleteError:
            # Maybe already deleted from backend, but check registry
            success = True # Treat as success if it's gone
        except Exception as e:
            print(f"Error deleting credential: {e}")
            return False
            
        # Update registry
        original_count = len(self.keys)
        self.keys = [k for k in self.keys if not (k["service"] == service and k["username"] == username)]
        
        if len(self.keys) < original_count:
            self._save_keys()
            
        return success

    def list_credentials(self) -> List[Dict[str, str]]:
        """
        List all known credentials (service and username only).
        """
        return self.keys
