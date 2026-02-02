"""
Device Authentication Protocol - Phase 2
========================================

This module implements the post-quantum cryptographic authentication protocol
between IoMT devices and the gateway.

Protocol Flow:
1. Device Registration: Device connects to gateway
2. Key Generation: Both device and gateway generate PQ keypairs
3. Key Exchange: Device sends public key to gateway
4. Encapsulation: Gateway performs KEM encapsulation
5. Shared Secret: Both parties establish identical shared secret
6. Blockchain Registration: Gateway registers key on-chain

Reference: Kyber KEM (NIST PQC standard)
"""

from typing import Tuple, Dict, Optional
from datetime import datetime
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256, HMAC
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AuthenticationProtocol:
    """
    Post-Quantum Cryptographic Authentication Protocol.
    
    Implements a simplified version of the Kyber KEM for demonstration.
    In production, use actual Kyber library from liboqs-python.
    """
    
    # Protocol configuration
    KEY_SIZE = 32  # 256-bit keys
    EPHEMERAL_SIZE = 32  # 256-bit ephemeral seed
    COMMITMENT_SIZE = 16  # 128-bit commitment proof
    
    def __init__(self):
        """Initialize the authentication protocol."""
        self.session_log = []
    
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum keypair (Kyber-like).
        
        Returns:
            tuple: (private_key, public_key) both as bytes
        """
        # In Phase 2: Use hash-based approach
        # In Phase 3: Use actual Kyber from liboqs
        
        private_key = get_random_bytes(AuthenticationProtocol.KEY_SIZE)
        
        # Derive public key from private key using secure hash
        h = SHA256.new(private_key)
        public_key_part1 = h.digest()
        
        # Add randomness for additional security
        public_key_part2 = get_random_bytes(32)
        public_key = public_key_part1 + public_key_part2
        
        return private_key, public_key
    
    @staticmethod
    def encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Perform key encapsulation (KEM.Encaps in Kyber).
        
        Takes a public key and returns:
        - ciphertext: To be sent to device for decapsulation
        - shared_secret: Symmetric key for encryption
        
        Args:
            public_key (bytes): Device's public key
        
        Returns:
            tuple: (ciphertext, shared_secret)
        """
        # Generate ephemeral key
        ephemeral_seed = get_random_bytes(AuthenticationProtocol.EPHEMERAL_SIZE)
        
        # Derive ephemeral key using hash
        h_eph = SHA256.new(ephemeral_seed)
        ephemeral_key = h_eph.digest()
        
        # Encapsulate: Combine ephemeral key with public key
        encapsulation_input = ephemeral_key + public_key
        h_encap = SHA256.new(encapsulation_input)
        shared_secret = h_encap.digest()
        
        # Ciphertext is the ephemeral seed (receiver will hash it with their private key)
        ciphertext = ephemeral_seed
        
        return ciphertext, shared_secret
    
    @staticmethod
    def decapsulate(private_key: bytes, ciphertext: bytes, public_key: bytes) -> Optional[bytes]:
        """
        Perform key decapsulation (KEM.Decaps in Kyber).
        
        Recovers the shared secret from ciphertext using private key.
        
        Args:
            private_key (bytes): Device's private key
            ciphertext (bytes): Received from gateway
            public_key (bytes): Device's own public key
        
        Returns:
            bytes: Shared secret (should match gateway's shared secret)
        """
        try:
            # Recover ephemeral key from ciphertext
            ephemeral_seed = ciphertext
            h_eph = SHA256.new(ephemeral_seed)
            ephemeral_key = h_eph.digest()
            
            # Decapsulate: Combine ephemeral key with public key
            # Note: This is simplified; real Kyber uses private key for decryption
            decapsulation_input = ephemeral_key + public_key
            h_decap = SHA256.new(decapsulation_input)
            shared_secret = h_decap.digest()
            
            return shared_secret
        except Exception as e:
            print(f"[-] Decapsulation failed: {e}")
            return None
    
    @staticmethod
    def create_session_key(shared_secret: bytes, session_id: str) -> Tuple[bytes, bytes]:
        """
        Derive session key and authentication tag from shared secret.
        
        Args:
            shared_secret (bytes): Shared secret from KEM
            session_id (str): Unique session identifier
        
        Returns:
            tuple: (session_key, authentication_tag)
        """
        # Derive session key using HMAC-based KDF
        h_session = HMAC.new(shared_secret, digestmod=SHA256)
        h_session.update(session_id.encode())
        session_key = h_session.digest()
        
        # Derive authentication tag
        h_auth = HMAC.new(shared_secret, digestmod=SHA256)
        h_auth.update(b"AUTH_TAG" + session_id.encode())
        authentication_tag = h_auth.digest()
        
        return session_key, authentication_tag


class DeviceAuthenticationSession:
    """
    Represents an authentication session between device and gateway.
    """
    
    def __init__(self, device_id: str, gateway_id: str):
        """
        Initialize authentication session.
        
        Args:
            device_id (str): Device identifier
            gateway_id (str): Gateway identifier
        """
        self.device_id = device_id
        self.gateway_id = gateway_id
        self.session_id = f"{device_id}_{gateway_id}_{datetime.now().timestamp()}"
        self.created_at = datetime.now().isoformat()
        
        # Protocol state
        self.state = "INITIALIZED"  # INITIALIZED -> PUBLIC_KEY_SENT -> ENCAPSULATED -> AUTHENTICATED
        self.device_public_key: Optional[bytes] = None
        self.shared_secret: Optional[bytes] = None
        self.session_key: Optional[bytes] = None
        self.authentication_tag: Optional[bytes] = None
        self.events = []
    
    def start_authentication(self, device_public_key: bytes) -> Dict:
        """
        Start authentication with device public key.
        
        Args:
            device_public_key (bytes): Device's PQ public key
        
        Returns:
            dict: Gateway response with ciphertext
        """
        if self.state != "INITIALIZED":
            return {"status": "ERROR", "message": "Invalid session state"}
        
        self.device_public_key = device_public_key
        self.state = "PUBLIC_KEY_RECEIVED"
        self._log_event("PUBLIC_KEY_RECEIVED")
        
        # Perform encapsulation
        ciphertext, shared_secret = AuthenticationProtocol.encapsulate(device_public_key)
        self.shared_secret = shared_secret
        self.state = "ENCAPSULATED"
        self._log_event("ENCAPSULATED")
        
        # Create response
        response = {
            "session_id": self.session_id,
            "status": "OK",
            "ciphertext": ciphertext.hex(),
            "commitment": shared_secret[:AuthenticationProtocol.COMMITMENT_SIZE].hex(),
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    
    def verify_authentication(self, device_commitment: bytes) -> bool:
        """
        Verify device's authentication (commitment proof).
        
        Args:
            device_commitment (bytes): Device's commitment proof
        
        Returns:
            bool: True if authentication successful
        """
        if self.state != "ENCAPSULATED" or self.shared_secret is None:
            return False
        
        # Verify commitment
        expected_commitment = self.shared_secret[:AuthenticationProtocol.COMMITMENT_SIZE]
        
        if device_commitment != expected_commitment:
            self._log_event("AUTHENTICATION_FAILED")
            return False
        
        # Derive session keys
        session_key, auth_tag = AuthenticationProtocol.create_session_key(
            self.shared_secret, self.session_id
        )
        self.session_key = session_key
        self.authentication_tag = auth_tag
        
        self.state = "AUTHENTICATED"
        self._log_event("AUTHENTICATED")
        
        return True
    
    def encrypt_message(self, plaintext: bytes) -> Dict:
        """
        Encrypt a message with session key.
        
        Args:
            plaintext (bytes): Message to encrypt
        
        Returns:
            dict: Encrypted message with IV and authentication tag
        """
        if self.state != "AUTHENTICATED" or self.session_key is None:
            return {"status": "ERROR", "message": "Session not authenticated"}
        
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
    
    def decrypt_message(self, iv_hex: str, ciphertext_hex: str, hmac_hex: str) -> Optional[bytes]:
        """
        Decrypt a message with session key.
        
        Args:
            iv_hex (str): IV in hex
            ciphertext_hex (str): Ciphertext in hex
            hmac_hex (str): HMAC tag in hex
        
        Returns:
            bytes: Decrypted plaintext, or None if verification fails
        """
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
                self._log_event("DECRYPTION_HMAC_FAILED")
                return None
            
            # Decrypt
            cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            plaintext = unpad(padded_plaintext, AES.block_size)
            
            self._log_event("MESSAGE_DECRYPTED")
            return plaintext
            
        except Exception as e:
            self._log_event(f"DECRYPTION_ERROR: {str(e)}")
            return None
    
    def _log_event(self, event_type: str):
        """Log a session event."""
        self.events.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type
        })
    
    def get_session_info(self) -> Dict:
        """Get session information."""
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "gateway_id": self.gateway_id,
            "state": self.state,
            "created_at": self.created_at,
            "authenticated": self.state == "AUTHENTICATED",
            "event_count": len(self.events)
        }


# Example usage and testing
if __name__ == "__main__":
    print("=== Post-Quantum Authentication Protocol Demo ===\n")
    
    # 1. Generate keypairs
    print("[*] Step 1: Generate device and gateway keypairs")
    device_private_key, device_public_key = AuthenticationProtocol.generate_keypair()
    print(f"[+] Device keys generated (PK size: {len(device_public_key)} bytes)")
    
    # 2. Create authentication session
    print("\n[*] Step 2: Create authentication session")
    session = DeviceAuthenticationSession("DEVICE_001", "GATEWAY_001")
    print(f"[+] Session created: {session.session_id}")
    
    # 3. Device sends public key
    print("\n[*] Step 3: Device sends public key to gateway")
    response = session.start_authentication(device_public_key)
    print(f"[+] Gateway response: {response['status']}")
    print(f"[+] Ciphertext: {response['ciphertext'][:32]}...")
    
    # 4. Device decapsulates
    print("\n[*] Step 4: Device decapsulates ciphertext")
    ciphertext = bytes.fromhex(response['ciphertext'])
    device_shared_secret = AuthenticationProtocol.decapsulate(device_private_key, ciphertext, device_public_key)
    print(f"[+] Device recovered shared secret (size: {len(device_shared_secret)} bytes)")
    
    # 5. Verify authentication
    print("\n[*] Step 5: Verify authentication commitment")
    commitment = device_shared_secret[:16]
    is_authenticated = session.verify_authentication(commitment)
    print(f"[+] Authentication: {' PASS' if is_authenticated else ' FAIL'}")
    
    # 6. Encrypt test message
    print("\n[*] Step 6: Encrypt message with session key")
    plaintext = b"IoMT Device Data - Quantum Secure"
    encrypted = session.encrypt_message(plaintext)
    print(f"[+] Message encrypted")
    print(f"[+] IV: {encrypted['iv'][:16]}...")
    print(f"[+] Ciphertext: {encrypted['ciphertext'][:32]}...")
    
    # 7. Decrypt message
    print("\n[*] Step 7: Decrypt message")
    decrypted = session.decrypt_message(encrypted['iv'], encrypted['ciphertext'], encrypted['hmac'])
    print(f"[+] Message decrypted: {decrypted.decode()}")
    print(f"[+] Match: {decrypted == plaintext}")
    
    print("\n[+] Authentication protocol demo complete!")
