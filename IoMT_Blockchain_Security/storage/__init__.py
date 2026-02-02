"""
Storage Module - Phase 1 & 2
============================

This module handles off-chain data storage using MongoDB.

Phase 1: MongoDB connection and initialization (COMPLETE)
Phase 2: Data persistence layer (COMPLETE)
Phase 3: Query and audit trail (IN PROGRESS)

Phase 2 Features:
- Store authenticated device keys
- Persist authentication audit logs
- Track device authentication history
- Query device status and event history
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class StorageConfig:
    """
    Configuration for off-chain storage.
    
    Attributes:
        mongodb_uri (str): MongoDB connection string
        database_name (str): Name of the MongoDB database
        collections (dict): MongoDB collections used
    """
    
    # Default MongoDB connection
    DEFAULT_URI = "mongodb://localhost:27017/"
    DEFAULT_DB = "iomt_blockchain"
    
    def __init__(self, uri=None, db_name=None):
        """
        Initialize storage configuration.
        
        Args:
            uri (str): MongoDB URI (optional)
            db_name (str): Database name (optional)
        """
        self.mongodb_uri = uri or self.DEFAULT_URI
        self.database_name = db_name or self.DEFAULT_DB
        self.collections = {
            "device_keys": "Stores device post-quantum public keys",
            "device_data": "Stores device sensor data",
            "transactions": "Stores blockchain transaction records",
            "audit_logs": "Stores audit trail and access logs"
        }
    
    def get_config(self):
        """
        Get storage configuration.
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            "mongodb_uri": self.mongodb_uri,
            "database_name": self.database_name,
            "collections": self.collections
        }


class StorageManager:
    """
    Manages off-chain data storage operations.
    
    Phase 1: Connection verification
    Phase 2: CRUD operations for device keys and audit logs
    Phase 3: Advanced querying and analytics
    """
    
    def __init__(self, config=None):
        """
        Initialize storage manager.
        
        Args:
            config (StorageConfig): Storage configuration
        """
        self.config = config or StorageConfig()
        self.client = None
        self.db = None
        self._connected = False
    
    def connect(self) -> bool:
        """
        Establish MongoDB connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not PYMONGO_AVAILABLE:
            print("[-] PyMongo not available. Install: pip install pymongo")
            return False
        
        try:
            self.client = MongoClient(
                self.config.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.config.database_name]
            self._connected = True
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"[-] MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self._connected
    
    # ========== PHASE 2: DEVICE KEY STORAGE ==========
    
    def save_device_key(self, device_id: str, key_data: Dict[str, Any]) -> bool:
        """
        Save authenticated device key to MongoDB.
        
        Args:
            device_id (str): Unique device identifier
            key_data (dict): Key information
                - public_key (str): Device's PQ public key (hex)
                - shared_secret (str): Shared secret from KEM (hex)
                - authenticated_at (str): ISO timestamp
                - gateway_id (str): Gateway that authenticated device
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            if not self.connect():
                return False
        
        try:
            collection = self.db["device_keys"]
            
            # Prepare document
            document = {
                "device_id": device_id,
                "public_key": key_data.get("public_key"),
                "shared_secret": key_data.get("shared_secret"),
                "gateway_id": key_data.get("gateway_id", "UNKNOWN"),
                "authenticated_at": key_data.get("authenticated_at", datetime.now().isoformat()),
                "blockchain_address": key_data.get("blockchain_address"),
                "is_active": True,
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert (update if exists, insert if not)
            result = collection.update_one(
                {"device_id": device_id},
                {"$set": document},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            print(f"[-] Error saving device key: {e}")
            return False
    
    def get_device_key(self, device_id: str) -> Optional[Dict]:
        """
        Retrieve device key from MongoDB.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            dict: Device key data or None if not found
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            collection = self.db["device_keys"]
            result = collection.find_one({"device_id": device_id})
            
            # Remove MongoDB's _id field for cleaner output
            if result:
                result.pop("_id", None)
            
            return result
            
        except Exception as e:
            print(f"[-] Error retrieving device key: {e}")
            return None
    
    def get_all_device_keys(self) -> List[Dict]:
        """
        Retrieve all registered device keys.
        
        Returns:
            list: List of device key documents
        """
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            collection = self.db["device_keys"]
            results = list(collection.find({}))
            
            # Clean up _id fields
            for doc in results:
                doc.pop("_id", None)
            
            return results
            
        except Exception as e:
            print(f"[-] Error retrieving all device keys: {e}")
            return []
    
    def deactivate_device_key(self, device_id: str) -> bool:
        """
        Deactivate device key in MongoDB.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            if not self.connect():
                return False
        
        try:
            collection = self.db["device_keys"]
            result = collection.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "is_active": False,
                        "deactivated_at": datetime.now().isoformat()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"[-] Error deactivating device key: {e}")
            return False
    
    # ========== PHASE 2: AUDIT LOG STORAGE ==========
    
    def save_audit_log(self, log_entry: Dict[str, Any]) -> bool:
        """
        Save authentication event to audit log.
        
        Args:
            log_entry (dict): Log entry information
                - event_type (str): Type of event (AUTHENTICATED, FAILED, DEACTIVATED, etc.)
                - device_id (str): Device identifier
                - gateway_id (str): Gateway identifier
                - timestamp (str): ISO timestamp
                - message (str): Description
                - metadata (dict): Additional data
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            if not self.connect():
                return False
        
        try:
            collection = self.db["audit_logs"]
            
            # Prepare document
            document = {
                "event_type": log_entry.get("event_type"),
                "device_id": log_entry.get("device_id"),
                "gateway_id": log_entry.get("gateway_id"),
                "timestamp": log_entry.get("timestamp", datetime.now().isoformat()),
                "message": log_entry.get("message"),
                "metadata": log_entry.get("metadata", {}),
                "recorded_at": datetime.now().isoformat()
            }
            
            result = collection.insert_one(document)
            return result.acknowledged
            
        except Exception as e:
            print(f"[-] Error saving audit log: {e}")
            return False
    
    def get_device_audit_log(self, device_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve audit log for specific device.
        
        Args:
            device_id (str): Device identifier
            limit (int): Maximum number of records to retrieve
        
        Returns:
            list: Audit log entries, most recent first
        """
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            collection = self.db["audit_logs"]
            results = list(
                collection.find({"device_id": device_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Clean up _id fields
            for doc in results:
                doc.pop("_id", None)
            
            return results
            
        except Exception as e:
            print(f"[-] Error retrieving audit log: {e}")
            return []
    
    def get_gateway_audit_log(self, gateway_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve audit log for specific gateway.
        
        Args:
            gateway_id (str): Gateway identifier
            limit (int): Maximum number of records
        
        Returns:
            list: Audit log entries for gateway
        """
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            collection = self.db["audit_logs"]
            results = list(
                collection.find({"gateway_id": gateway_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            for doc in results:
                doc.pop("_id", None)
            
            return results
            
        except Exception as e:
            print(f"[-] Error retrieving gateway audit log: {e}")
            return []
    
    def get_all_audit_logs(self, limit: int = 1000) -> List[Dict]:
        """
        Retrieve all audit logs.
        
        Args:
            limit (int): Maximum number of records
        
        Returns:
            list: All audit log entries, most recent first
        """
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            collection = self.db["audit_logs"]
            results = list(
                collection.find({})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            for doc in results:
                doc.pop("_id", None)
            
            return results
            
        except Exception as e:
            print(f"[-] Error retrieving all audit logs: {e}")
            return []
    
    # ========== PHASE 2: DEVICE STATUS & STATISTICS ==========
    
    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """
        Get current status of device.
        
        Args:
            device_id (str): Device identifier
        
        Returns:
            dict: Device status information
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            # Get device key info
            key_info = self.get_device_key(device_id)
            if not key_info:
                return None
            
            # Get recent events
            audit_log = self.get_device_audit_log(device_id, limit=5)
            
            # Count authentications
            collection = self.db["audit_logs"]
            total_events = collection.count_documents({"device_id": device_id})
            auth_events = collection.count_documents({
                "device_id": device_id,
                "event_type": "AUTHENTICATED"
            })
            
            return {
                "device_id": device_id,
                "is_active": key_info.get("is_active", False),
                "gateway_id": key_info.get("gateway_id"),
                "authenticated_at": key_info.get("authenticated_at"),
                "total_events": total_events,
                "successful_auths": auth_events,
                "last_event": audit_log[0] if audit_log else None,
                "recent_events": audit_log
            }
            
        except Exception as e:
            print(f"[-] Error getting device status: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall system statistics.
        
        Returns:
            dict: Statistics about devices, authentications, gateways
        """
        if not self.is_connected():
            if not self.connect():
                return {}
        
        try:
            device_keys_col = self.db["device_keys"]
            audit_logs_col = self.db["audit_logs"]
            
            # Count statistics
            total_devices = device_keys_col.count_documents({})
            active_devices = device_keys_col.count_documents({"is_active": True})
            total_events = audit_logs_col.count_documents({})
            
            # Get unique gateways
            gateways = audit_logs_col.distinct("gateway_id")
            
            return {
                "total_devices": total_devices,
                "active_devices": active_devices,
                "inactive_devices": total_devices - active_devices,
                "total_audit_events": total_events,
                "unique_gateways": len(gateways),
                "gateways": gateways,
                "database": self.config.database_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[-] Error getting statistics: {e}")
            return {}
    
    def get_connection_info(self):
        """
        Get connection information.
        
        Returns:
            dict: Connection details
        """
        status = "Connected" if self.is_connected() else "Disconnected"
        return {
            "uri": self.config.mongodb_uri,
            "database": self.config.database_name,
            "collections": list(self.config.collections.keys()),
            "status": status,
            "phase": "Phase 2 Complete"
        }


def create_storage_manager(uri=None, db_name=None):
    """
    Factory function to create a storage manager.
    
    Args:
        uri (str): MongoDB URI (optional)
        db_name (str): Database name (optional)
    
    Returns:
        StorageManager: Configured storage manager
    """
    config = StorageConfig(uri, db_name)
    manager = StorageManager(config)
    return manager


# Example usage (for testing purposes)
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Storage Module - Phase 2 Test")
    print("="*60 + "\n")
    
    # Create storage manager
    storage = create_storage_manager()
    
    print("[*] Storage Configuration:")
    print(json.dumps(storage.get_connection_info(), indent=2))
    
    print("\n[*] Attempting MongoDB connection...")
    if storage.connect():
        print("[+] MongoDB Connected Successfully")
        
        print("\n[*] Saving test device key...")
        device_key = {
            "public_key": "0x" + "a" * 64,
            "shared_secret": "0x" + "b" * 64,
            "gateway_id": "GATEWAY_TEST_001",
            "authenticated_at": datetime.now().isoformat()
        }
        
        if storage.save_device_key("DEVICE_TEST_001", device_key):
            print("[+] Device key saved successfully")
            
            print("\n[*] Retrieving device key...")
            retrieved = storage.get_device_key("DEVICE_TEST_001")
            if retrieved:
                print(f"[+] Retrieved: Device {retrieved['device_id']}")
                print(f"    Gateway: {retrieved['gateway_id']}")
                print(f"    Active: {retrieved['is_active']}")
        
        print("\n[*] Saving audit log entry...")
        log_entry = {
            "event_type": "AUTHENTICATED",
            "device_id": "DEVICE_TEST_001",
            "gateway_id": "GATEWAY_TEST_001",
            "message": "Device authenticated successfully via KEM",
            "metadata": {"kem_type": "hash_based", "key_size": 256}
        }
        
        if storage.save_audit_log(log_entry):
            print("[+] Audit log saved successfully")
            
            print("\n[*] Retrieving audit log...")
            logs = storage.get_device_audit_log("DEVICE_TEST_001")
            if logs:
                print(f"[+] Retrieved {len(logs)} audit log entries")
                for log in logs:
                    print(f"    - {log['event_type']}: {log['message']}")
        
        print("\n[*] Getting device status...")
        status = storage.get_device_status("DEVICE_TEST_001")
        if status:
            print(f"[+] Device Status:")
            print(f"    Active: {status['is_active']}")
            print(f"    Total Events: {status['total_events']}")
            print(f"    Successful Auths: {status['successful_auths']}")
        
        print("\n[*] Getting system statistics...")
        stats = storage.get_statistics()
        if stats:
            print(f"[+] System Statistics:")
            print(f"    Total Devices: {stats['total_devices']}")
            print(f"    Active Devices: {stats['active_devices']}")
            print(f"    Total Audit Events: {stats['total_audit_events']}")
            print(f"    Unique Gateways: {stats['unique_gateways']}")
        
        storage.disconnect()
        print("\n[+] MongoDB disconnected")
    else:
        print("[-] MongoDB connection failed")
        print("[*] Make sure MongoDB is running:")
        print("    mongod --dbpath /path/to/db")
    
    print("\n" + "="*60 + "\n")
