"""
IoMT Device Module - Phase 1
=============================

This module simulates IoMT (Internet of Medical Things) devices.

Phase 1: Device initialization and key generation
Phase 2: Data collection and signing
Phase 3: Blockchain interaction
"""

import json
from datetime import datetime


class IoTMDevice:
    """
    Represents a simulated IoMT device.
    
    Attributes:
        device_id (str): Unique device identifier
        device_type (str): Type of device (e.g., 'blood_pressure_monitor', 'glucose_meter')
        manufacturer (str): Device manufacturer
        kyber_public_key (bytes): Post-quantum public key (Kyber)
        dilithium_public_key (bytes): Post-quantum signature key (Dilithium)
    """
    
    def __init__(self, device_id, device_type, manufacturer):
        """
        Initialize an IoMT device.
        
        Args:
            device_id (str): Unique identifier for the device
            device_type (str): Type of medical device
            manufacturer (str): Manufacturer name
        """
        self.device_id = device_id
        self.device_type = device_type
        self.manufacturer = manufacturer
        self.kyber_public_key = None
        self.dilithium_public_key = None
        self.created_at = datetime.now().isoformat()
    
    def set_pq_keys(self, kyber_pk, dilithium_pk):
        """
        Set post-quantum cryptographic keys for the device.
        
        Args:
            kyber_pk (bytes): Kyber public key for key encapsulation
            dilithium_pk (bytes): Dilithium public key for signatures
        """
        self.kyber_public_key = kyber_pk
        self.dilithium_public_key = dilithium_pk
    
    def get_device_info(self):
        """
        Get device information dictionary.
        
        Returns:
            dict: Device information including ID, type, and keys
        """
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "created_at": self.created_at,
            "keys_configured": bool(self.kyber_public_key and self.dilithium_public_key)
        }


def create_device(device_id, device_type, manufacturer):
    """
    Factory function to create an IoMT device.
    
    Args:
        device_id (str): Device identifier
        device_type (str): Device type
        manufacturer (str): Manufacturer name
    
    Returns:
        IoTMDevice: Configured device instance
    """
    device = IoTMDevice(device_id, device_type, manufacturer)
    return device


# Example usage (for testing purposes)
if __name__ == "__main__":
    # Create sample devices
    bp_monitor = create_device("DEVICE_BP_001", "blood_pressure_monitor", "Philips")
    glucose_meter = create_device("DEVICE_GM_001", "glucose_meter", "Abbott")
    
    print("✓ Device module loaded successfully")
    print(f"  Sample device 1: {bp_monitor.get_device_info()}")
    print(f"  Sample device 2: {glucose_meter.get_device_info()}")
