#!/usr/bin/env python3
"""
Device Simulator - Phase 6
==========================

Simulates IoMT devices sending authentication requests and generating events.
Used to populate the dashboard with realistic data for visualization.

Features:
- Simulates multiple medical devices
- Generates authentication events
- Creates audit trail entries
- Tracks device status changes
- Compatible with storage layer
"""

import time
import random
from datetime import datetime
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import StorageManager, StorageConfig
from auth_protocol import PostQuantumAuth, PostQuantumKeypair


class DeviceSimulator:
    """Simulates an IoMT device with authentication capabilities."""
    
    def __init__(self, device_id: str, device_type: str, storage: StorageManager):
        """
        Initialize device simulator.
        
        Args:
            device_id (str): Unique device identifier
            device_type (str): Type of device (e.g., "BP_MONITOR", "GLUCOSE_METER")
            storage (StorageManager): Storage manager for persistence
        """
        self.device_id = device_id
        self.device_type = device_type
        self.storage = storage
        self.gateway_id = "GATEWAY_001"
        
        # Device state
        self.is_registered = False
        self.is_authenticated = False
        self.keypair: PostQuantumKeypair = None
        self.auth_count = 0
        self.failure_count = 0
        self.last_auth_time = None
        
        # Initialize post-quantum cryptography
        self.pq_auth = PostQuantumAuth()
    
    def register(self) -> bool:
        """
        Register device (generate keys and store in MongoDB).
        
        Returns:
            bool: True if successful
        """
        try:
            print(f"  [*] Registering device {self.device_id}...")
            
            # Generate post-quantum keypair
            self.keypair = self.pq_auth.generate_keypair()
            
            # Prepare key data
            key_data = {
                "public_key": self.keypair.public_key.hex(),
                "shared_secret": "0x" + "0" * 128,  # Placeholder
                "gateway_id": self.gateway_id,
                "authenticated_at": datetime.now().isoformat(),
                "device_type": self.device_type,
                "blockchain_address": None
            }
            
            # Save to MongoDB
            if self.storage.save_device_key(self.device_id, key_data):
                self.is_registered = True
                
                # Log registration event
                self.storage.save_audit_log({
                    "event_type": "DEVICE_REGISTERED",
                    "device_id": self.device_id,
                    "gateway_id": self.gateway_id,
                    "message": f"Device {self.device_id} registered successfully",
                    "metadata": {"device_type": self.device_type}
                })
                
                print(f"  [+] Device {self.device_id} registered successfully")
                return True
            else:
                print(f"  [-] Failed to register device {self.device_id}")
                return False
                
        except Exception as e:
            print(f"  [-] Error registering device: {e}")
            return False
    
    def authenticate(self, success_rate: float = 0.95) -> bool:
        """
        Perform authentication and generate audit log entry.
        
        Args:
            success_rate (float): Probability of successful authentication (0-1)
        
        Returns:
            bool: True if authentication succeeded
        """
        if not self.is_registered:
            return False
        
        try:
            # Determine if auth succeeds based on success_rate
            is_successful = random.random() < success_rate
            
            if is_successful:
                # Simulate successful authentication
                shared_secret = self.pq_auth.encapsulate(self.keypair.public_key)
                
                # Update device in MongoDB
                key_data = self.storage.get_device_key(self.device_id)
                key_data["shared_secret"] = shared_secret.hex()
                key_data["last_authenticated"] = datetime.now().isoformat()
                key_data["authentication_count"] = self.auth_count + 1
                
                # Log successful authentication
                self.storage.save_audit_log({
                    "event_type": "AUTHENTICATED",
                    "device_id": self.device_id,
                    "gateway_id": self.gateway_id,
                    "message": f"Device {self.device_id} authenticated successfully",
                    "metadata": {
                        "device_type": self.device_type,
                        "auth_method": "post_quantum_kem",
                        "key_size": 256
                    }
                })
                
                self.is_authenticated = True
                self.auth_count += 1
                self.last_auth_time = datetime.now()
                
                return True
            else:
                # Simulate failed authentication
                self.storage.save_audit_log({
                    "event_type": "AUTH_FAILED",
                    "device_id": self.device_id,
                    "gateway_id": self.gateway_id,
                    "message": f"Authentication failed for device {self.device_id}",
                    "metadata": {
                        "device_type": self.device_type,
                        "failure_reason": "Invalid credentials or timeout"
                    }
                })
                
                self.is_authenticated = False
                self.failure_count += 1
                
                return False
                
        except Exception as e:
            print(f"  [-] Error during authentication: {e}")
            return False
    
    def revoke(self, reason: str = "Device compromised") -> bool:
        """
        Revoke device access.
        
        Args:
            reason (str): Reason for revocation
        
        Returns:
            bool: True if successful
        """
        try:
            if self.storage.deactivate_device_key(self.device_id):
                self.storage.save_audit_log({
                    "event_type": "DEVICE_REVOKED",
                    "device_id": self.device_id,
                    "gateway_id": self.gateway_id,
                    "message": f"Device {self.device_id} revoked: {reason}",
                    "metadata": {"revocation_reason": reason}
                })
                
                self.is_authenticated = False
                print(f"  [+] Device {self.device_id} revoked")
                return True
            return False
        except Exception as e:
            print(f"  [-] Error revoking device: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "is_registered": self.is_registered,
            "is_authenticated": self.is_authenticated,
            "auth_count": self.auth_count,
            "failure_count": self.failure_count,
            "last_auth_time": self.last_auth_time
        }


class SimulationScenario:
    """Defines and runs simulation scenarios."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.devices: List[DeviceSimulator] = []
    
    def add_device(self, device_id: str, device_type: str) -> DeviceSimulator:
        """Add device to simulation."""
        device = DeviceSimulator(device_id, device_type, self.storage)
        self.devices.append(device)
        return device
    
    def register_all_devices(self) -> bool:
        """Register all devices."""
        print("\n[*] Registering all devices...")
        success_count = 0
        
        for device in self.devices:
            if device.register():
                success_count += 1
        
        print(f"[+] Registered {success_count}/{len(self.devices)} devices\n")
        return success_count == len(self.devices)
    
    def run_authentication_scenario(self, duration: int = 60, interval: int = 5):
        """
        Run continuous authentication scenario.
        
        Args:
            duration (int): Duration in seconds
            interval (int): Interval between authentications in seconds
        """
        print(f"\n[*] Running authentication scenario ({duration}s)...")
        print(f"[*] Interval: {interval}s, Total iterations: {duration // interval}\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while time.time() - start_time < duration:
                iteration += 1
                elapsed = int(time.time() - start_time)
                
                print(f"[*] Iteration {iteration} (elapsed: {elapsed}s)")
                
                # Random device authentication
                for device in self.devices:
                    if random.random() < 0.7:  # 70% chance to auth
                        result = device.authenticate(success_rate=0.95)
                        status = "✓" if result else "✗"
                        print(f"    {status} {device.device_id}: {device.auth_count} auths, {device.failure_count} failures")
                
                # Wait for next iteration
                time.sleep(interval)
            
            print(f"\n[+] Authentication scenario completed\n")
            
        except KeyboardInterrupt:
            print("\n[*] Simulation interrupted by user\n")
    
    def run_revocation_scenario(self):
        """Run device revocation scenario."""
        print("\n[*] Running revocation scenario...")
        
        if len(self.devices) >= 2:
            # Revoke first device
            device_to_revoke = self.devices[0]
            print(f"[*] Revoking {device_to_revoke.device_id}...")
            device_to_revoke.revoke("Unauthorized access attempt detected")
            print(f"[+] Device revoked\n")
        
        return True
    
    def print_summary(self):
        """Print simulation summary."""
        print("\n" + "="*70)
        print("SIMULATION SUMMARY")
        print("="*70 + "\n")
        
        total_auths = sum(d.auth_count for d in self.devices)
        total_failures = sum(d.failure_count for d in self.devices)
        registered = sum(1 for d in self.devices if d.is_registered)
        
        print(f"Devices Registered: {registered}/{len(self.devices)}")
        print(f"Total Authentications: {total_auths}")
        print(f"Total Failures: {total_failures}")
        print(f"Success Rate: {(total_auths / (total_auths + total_failures) * 100) if (total_auths + total_failures) > 0 else 0:.1f}%\n")
        
        print("Device Status:")
        for device in self.devices:
            status = device.get_status()
            state = "ACTIVE" if status["is_authenticated"] else "INACTIVE"
            print(f"  {status['device_id']:20} {state:8} - Auths: {status['auth_count']:3}, Failures: {status['failure_count']:2}")
        
        # Get system statistics
        print("\n[*] Fetching system statistics...")
        stats = self.storage.get_statistics()
        
        print(f"\nSystem Statistics:")
        print(f"  Total Devices: {stats.get('total_devices', 0)}")
        print(f"  Active Devices: {stats.get('active_devices', 0)}")
        print(f"  Total Audit Events: {stats.get('total_audit_events', 0)}")
        print(f"  Unique Gateways: {stats.get('unique_gateways', 0)}\n")


def main():
    """Main simulation runner."""
    
    print("\n" + "="*70)
    print("PHASE 6 - DEVICE SIMULATOR FOR DASHBOARD")
    print("="*70 + "\n")
    
    # Initialize storage
    print("[*] Connecting to MongoDB...")
    storage = StorageManager(StorageConfig())
    
    if not storage.connect():
        print("[-] MongoDB connection failed")
        return False
    
    print("[+] MongoDB connected\n")
    
    # Create simulation
    sim = SimulationScenario(storage)
    
    # Add medical devices
    print("[*] Adding medical devices to simulation...\n")
    sim.add_device("BP_MONITOR_002", "Blood Pressure Monitor")
    sim.add_device("GLUCOSE_METER_002", "Glucose Meter")
    sim.add_device("PULSE_OXI_002", "Pulse Oximeter")
    sim.add_device("TEMP_SENSOR_001", "Temperature Sensor")
    
    # Register devices
    if not sim.register_all_devices():
        print("[-] Failed to register all devices")
        return False
    
    # Run scenarios
    try:
        # Run authentication scenario for 60 seconds
        sim.run_authentication_scenario(duration=60, interval=5)
        
        # Run revocation scenario
        sim.run_revocation_scenario()
        
        # Run more authentications after revocation
        sim.run_authentication_scenario(duration=30, interval=5)
        
        # Print summary
        sim.print_summary()
        
    except Exception as e:
        print(f"[-] Error during simulation: {e}")
        return False
    finally:
        storage.disconnect()
        print("[+] Disconnected from MongoDB")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
