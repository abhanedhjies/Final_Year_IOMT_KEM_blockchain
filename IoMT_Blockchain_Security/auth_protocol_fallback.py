"""
Fallback Auth Protocol - For Decryption Demo
This provides the classes needed for the /decryption page demo
"""
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256, HMAC
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

class AuthenticationProtocol:
    """Simplified Post-Quantum KEM for demonstration"""
    
    KEY_SIZE = 32
    COMMITMENT_SIZE = 16
    
    @staticmethod
    def create_session_key(shared_secret: bytes, session_id: str) -> Tuple[bytes, bytes]:
        """Derive session key and authentication tag from shared secret."""
        h_session = HMAC.new(shared_secret, digestmod=SHA256)
        h_session.update(session_id.encode())
        session_key = h_session.digest()
        
        h_auth = HMAC.new(shared_secret, digestmod=SHA256)
        h_auth.update(b"AUTH_TAG" + session_id.encode())
        authentication_tag = h_auth.digest()
        
        return session_key, authentication_tag


class DeviceAuthenticationSession:
    """Authentication session between device and gateway"""
    
    def __init__(self, device_id: str, gateway_id: str):
        self.device_id = device_id
        self.gateway_id = gateway_id
        self.session_id = f"{device_id}_{gateway_id}_{datetime.now().timestamp()}"
        self.created_at = datetime.now().isoformat()
        
        self.state = "INITIALIZED"
        self.device_public_key: Optional[bytes] = None
        self.shared_secret: Optional[bytes] = None
        self.session_key: Optional[bytes] = None
        self.authentication_tag: Optional[bytes] = None
        self.events = []
    
    def encrypt_message(self, plaintext: bytes) -> Dict:
        """Encrypt a message with session key."""
        if self.state != "AUTHENTICATED" or self.session_key is None:
            return {"status": "ERROR", "message": "Session not authenticated"}
        
        try:
            # Generate IV
            iv = get_random_bytes(16)
            
            # Encrypt using AES-256-CBC
            cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
            padded_plaintext = pad(plaintext, AES.block_size)
            ciphertext = cipher.encrypt(padded_plaintext)
            
            # Create HMAC for integrity
            h = HMAC.new(self.session_key, digestmod=SHA256)
            h.update(ciphertext)
            hmac_tag = h.digest()
            
            return {
                "iv": iv.hex(),
                "ciphertext": ciphertext.hex(),
                "hmac": hmac_tag.hex(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def decrypt_message(self, iv_hex: str, ciphertext_hex: str, hmac_hex: str) -> Optional[bytes]:
        """Decrypt a message with session key."""
        if self.state != "AUTHENTICATED" or self.session_key is None:
            return None
        
        try:
            # Convert from hex
            iv = bytes.fromhex(iv_hex)
            ciphertext = bytes.fromhex(ciphertext_hex)
            hmac_received = bytes.fromhex(hmac_hex)
            
            # Verify HMAC
            h = HMAC.new(self.session_key, digestmod=SHA256)
            h.update(ciphertext)
            hmac_expected = h.digest()
            
            if hmac_received != hmac_expected:
                return None
            
            # Decrypt
            cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            plaintext = unpad(padded_plaintext, AES.block_size)
            
            return plaintext
            
        except Exception as e:
            return None
