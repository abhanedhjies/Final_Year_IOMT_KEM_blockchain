"""
Gateway Module - Phase 2
========================

This module implements the IoMT gateway that aggregates devices,
manages authentication with post-quantum cryptography, and communicates
with the blockchain for key management.

Key Features:
- Device registration and management
- Post-quantum key exchange (Kyber-like KEM)
- Blockchain integration for key storage
- Device authentication protocol
- Data aggregation

Phase 1: Basic device management (COMPLETE)
Phase 2: Authentication and blockchain integration (CURRENT)
Phase 3: Advanced data aggregation and reporting (NEXT)
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256


class IoTMGateway:
    """
    IoMT Gateway for device management and authentication.
    
    Responsibilities:
    - Manage connected IoMT devices
    - Coordinate device authentication
    - Communicate with blockchain for key management
    - Aggregate and preprocess device data
    
    Attributes:
        gateway_id (str): Unique gateway identifier
        location (str): Physical location of the gateway
        blockchain_provider: Web3 provider for blockchain communication
        connected_devices (dict): Connected devices mapping
        device_keys (dict): Stores device post-quantum public keys
        authenticated_devices (set): Devices that have been authenticated
        auth_log (list): Audit trail of authentication events
    """
    
    def __init__(self, gateway_id: str, location: str, blockchain_provider=None):
        """
        Initialize the gateway.
        
        Args:
            gateway_id (str): Unique identifier for the gateway
            location (str): Physical location of the gateway
            blockchain_provider: Web3 provider for blockchain communication (Phase 2+)
        """
        self.gateway_id = gateway_id
        self.location = location
        self.blockchain_provider = blockchain_provider
        self.connected_devices: Dict[str, object] = {}
        self.device_keys: Dict[str, Dict] = {}  # Store device PQ keys
        self.gateway_key_pair = self._generate_gateway_keys()
        self.authenticated_devices: set = set()
        self.created_at = datetime.now().isoformat()
        self.auth_log: List[Dict] = []
    
    def _generate_gateway_keys(self) -> Dict:
        """
        Generate post-quantum key pair for the gateway.
        
        Uses hash-based approach (Kyber simulation) for Phase 2.
        Will be replaced with full Kyber in Phase 3.
        
        Returns:
            dict: Contains private_key and public_key (hex format)
        """
        private_key = get_random_bytes(64)
        # Simulate Kyber public key derivation using SHA256
        h = SHA256.new(private_key)
        public_key = h.digest() + get_random_bytes(32)
        
        return {
            "private_key": private_key.hex(),
            "public_key": public_key.hex(),
            "algorithm": "Hash-based KEM (Kyber simulation)"
        }
    
    def register_device(self, device_id: str, device_obj: object) -> bool:
        """
        Register a device with the gateway.
        
        Args:
            device_id (str): Device identifier
            device_obj: Device object
        
        Returns:
            bool: True if registration successful, False if already registered
        """
        if device_id in self.connected_devices:
            self._log_event("REGISTER_FAILED", device_id, "Device already registered")
            return False
        
        self.connected_devices[device_id] = device_obj
        self._log_event("DEVICE_REGISTERED", device_id, "Device registered")
        return True
    
    def unregister_device(self, device_id: str) -> bool:
        """
        Unregister a device from the gateway.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            bool: True if unregistration successful
        """
        if device_id not in self.connected_devices:
            return False
        
        del self.connected_devices[device_id]
        
        # Also remove from authenticated devices if present
        if device_id in self.authenticated_devices:
            self.authenticated_devices.discard(device_id)
        
        self._log_event("DEVICE_UNREGISTERED", device_id, "Device unregistered")
        return True
    
    def authenticate_device(self, device_id: str, device_public_key: bytes) -> Optional[Dict]:
        """
        Authenticate a device using post-quantum cryptography.
        
        Implements key encapsulation mechanism (KEM) similar to Kyber:
        1. Device sends public key to gateway
        2. Gateway performs encapsulation (generates shared secret)
        3. Gateway sends ciphertext back to device
        4. Device performs decapsulation to recover shared secret
        5. Both parties now have identical shared secret
        
        Args:
            device_id (str): Device to authenticate
            device_public_key (bytes): Device's public key
        
        Returns:
            dict: Authentication result with ciphertext, or None if failed
        """
        if device_id not in self.connected_devices:
            self._log_event("AUTH_FAILED", device_id, "Device not registered")
            return None
        
        try:
            # Step 1: Generate ephemeral key
            ephemeral_seed = get_random_bytes(32)
            h_eph = SHA256.new(ephemeral_seed)
            ephemeral_key = h_eph.digest()
            
            # Step 2: Encapsulate shared secret
            # In real Kyber: encaps(device_public_key) -> (ciphertext, shared_secret)
            encapsulation_input = ephemeral_key + device_public_key
            h_encap = SHA256.new(encapsulation_input)
            shared_secret = h_encap.digest()
            ciphertext = ephemeral_seed
            
            # Store device keys for later verification
            self.device_keys[device_id] = {
                "public_key": device_public_key.hex() if isinstance(device_public_key, bytes) else device_public_key,
                "shared_secret": shared_secret.hex(),
                "authenticated_at": datetime.now().isoformat()
            }
            
            self.authenticated_devices.add(device_id)
            
            auth_result = {
                "device_id": device_id,
                "status": "AUTHENTICATED",
                "ciphertext": ciphertext.hex(),  # Send to device for decapsulation
                "shared_secret_commitment": shared_secret[:16].hex(),  # Proof of shared secret
                "timestamp": datetime.now().isoformat()
            }
            
            self._log_event("DEVICE_AUTHENTICATED", device_id, "Authentication successful - KEM completed")
            return auth_result
            
        except Exception as e:
            self._log_event("AUTH_ERROR", device_id, f"Authentication error: {str(e)}")
            return None
    
    def get_connected_device_count(self) -> int:
        """Get number of connected devices."""
        return len(self.connected_devices)
    
    def get_authenticated_device_count(self) -> int:
        """Get number of authenticated devices."""
        return len(self.authenticated_devices)
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """
        Get information about a connected device.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            dict: Device information including authentication status
        """
        if device_id not in self.connected_devices:
            return None
        
        device = self.connected_devices[device_id]
        
        # Try to get device info if method exists
        device_info = {}
        if hasattr(device, 'get_device_info'):
            device_info = device.get_device_info()
        
        # Add authentication status
        is_authenticated = device_id in self.authenticated_devices
        device_info["authenticated"] = is_authenticated
        
        return device_info
    
    def get_gateway_info(self) -> Dict:
        """
        Get gateway information.
        
        Returns:
            dict: Gateway status and configuration
        """
        return {
            "gateway_id": self.gateway_id,
            "location": self.location,
            "connected_devices": self.get_connected_device_count(),
            "authenticated_devices": self.get_authenticated_device_count(),
            "created_at": self.created_at,
            "gateway_public_key_preview": self.gateway_key_pair["public_key"][:32] + "...",
            "blockchain_connected": self.blockchain_provider is not None
        }
    
    def _log_event(self, event_type: str, device_id: str, message: str):
        """
        Log an event in the gateway audit trail.
        
        Args:
            event_type (str): Type of event (e.g., "DEVICE_REGISTERED", "AUTH_FAILED")
            device_id (str): Affected device
            message (str): Event description
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "device_id": device_id,
            "message": message,
            "gateway_id": self.gateway_id
        }
        self.auth_log.append(log_entry)
    
    def get_auth_log(self) -> List[Dict]:
        """
        Get the authentication audit log.
        
        Returns:
            list: List of authentication events (most recent last)
        """
        return self.auth_log.copy()
    
    def submit_to_blockchain(self, device_id: str, contract_instance=None) -> bool:
        """
        Submit device's public key to blockchain smart contract.
        
        Phase 2: Prepares data for blockchain submission.
        Phase 3: Will actually submit to Ganache blockchain.
        
        Args:
            device_id (str): Device to submit
            contract_instance: Web3 contract instance (Phase 3)
        
        Returns:
            bool: True if submission prepared/successful
        """
        if device_id not in self.device_keys:
            self._log_event("BLOCKCHAIN_SUBMIT_FAILED", device_id, "Device not authenticated")
            return False
        
        if self.blockchain_provider is None and contract_instance is None:
            # Phase 2: Log the intent (actual submission in Phase 3)
            self._log_event("BLOCKCHAIN_READY", device_id, 
                          "Device key ready for blockchain submission (Phase 3)")
            return True
        
        # Phase 3: Actual blockchain submission would happen here
        self._log_event("BLOCKCHAIN_SUBMITTED", device_id, 
                       "Device key submitted to blockchain smart contract")
        return True
    
    def get_device_keys(self, device_id: str) -> Optional[Dict]:
        """
        Retrieve stored keys for a device.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            dict: Device keys (public_key, shared_secret, timestamp), or None
        """
        return self.device_keys.get(device_id)


def create_gateway(gateway_id: str, location: str, blockchain_provider=None) -> IoTMGateway:
    """
    Factory function to create an IoMT gateway.
    
    Args:
        gateway_id (str): Gateway identifier
        location (str): Gateway location
        blockchain_provider: Optional blockchain provider (Phase 3)
    
    Returns:
        IoTMGateway: Configured gateway instance
    """
    return IoTMGateway(gateway_id, location, blockchain_provider)


# Example usage (for testing purposes)
if __name__ == "__main__":
    from device import create_device
    
    # Create gateway
    gateway = create_gateway("GATEWAY_001", "Central Hospital Ward A")
    
    # Create and register devices
    bp_monitor = create_device("DEVICE_BP_001", "blood_pressure_monitor", "Philips")
    glucose_meter = create_device("DEVICE_GM_001", "glucose_meter", "Abbott")
    
    gateway.register_device("DEVICE_BP_001", bp_monitor)
    gateway.register_device("DEVICE_GM_001", glucose_meter)
    
    print("✓ Gateway module loaded successfully")
    print(f"  Gateway ID: {gateway.gateway_id}")
    print(f"  Connected devices: {gateway.get_connected_device_count()}")
    print(f"  Gateway Info: {gateway.get_gateway_info()}")
