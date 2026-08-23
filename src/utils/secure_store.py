import json
import uuid
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

def get_machine_key() -> bytes:
    """
    Generates a 32-byte url-safe base64 encoded key tied to the machine's hardware ID.
    This ensures that the encrypted files cannot be decrypted if copied to another machine.
    """
    # uuid.getnode() returns the MAC address, providing a hardware-specific ID
    machine_id = str(uuid.getnode())
    pepper = "py-cast-secure-vault-hardware-lock"
    
    # Hash the hardware ID and pepper to generate a consistent 32-byte key
    key_hash = hashlib.sha256((machine_id + pepper).encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key_hash)

def get_cipher() -> Fernet:
    return Fernet(get_machine_key())

def secure_save(path: str | Path, data: dict) -> None:
    """
    Encrypts a dictionary to JSON and saves it securely to the disk.
    """
    path_obj = Path(path)
    cipher = get_cipher()
    
    json_data = json.dumps(data).encode('utf-8')
    encrypted_data = cipher.encrypt(json_data)
    
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_bytes(encrypted_data)

def secure_load(path: str | Path) -> dict:
    """
    Reads an encrypted JSON file from the disk and decrypts it.
    Returns an empty dict if the file is missing or tampering is detected.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {}
        
    try:
        cipher = get_cipher()
        encrypted_data = path_obj.read_bytes()
        
        if not encrypted_data:
            return {}
            
        try:
            # First try to decrypt normally
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as decrypt_err:
            # Fallback for old plaintext files during migration
            # We attempt to read as regular JSON if decryption fails
            try:
                plaintext_data = json.loads(encrypted_data.decode('utf-8'))
                logger.warning(f"File {path_obj} was plaintext. Migrating to secure store...")
                # Automatically re-save securely so it's encrypted next time
                secure_save(path_obj, plaintext_data)
                return plaintext_data
            except json.JSONDecodeError:
                # If it's not plaintext and not verifiable by Fernet, it's tampered/corrupt
                logger.error(f"Integrity error or unauthorized access for {path_obj}: {decrypt_err}")
                return {}
                
    except Exception as e:
        logger.error(f"Failed to securely load {path_obj}: {e}")
        return {}
