"""
Storage Management for IoT Devices - MongoDB Integration
========================================================

Handles:
- Device key storage
- Audit logging
- Statistics tracking
- Blockchain transaction references
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime
from typing import Dict, Any, List, Optional

class StorageManager:
    """Manage all data storage in MongoDB"""
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017"):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client['iot_blockchain_db']
            
            # Initialize collections
            self._initialize_collections()
            
            self.connected = True
            print("[+] Connected to MongoDB at " + self.mongodb_uri)
            return True
            
        except ConnectionFailure as e:
            print(f"[-] MongoDB connection failed: {e}")
            return False
        except Exception as e:
            print(f"[-] Error connecting to MongoDB: {e}")
            return False
    
    def _initialize_collections(self):
        """Initialize database collections"""
        try:
            # Create collections if they don't exist
            if 'device_keys' not in self.db.list_collection_names():
                self.db.create_collection('device_keys')
                self.db['device_keys'].create_index('device_id', unique=True)
                print("   [+] Created collection: device_keys")
            
            if 'audit_logs' not in self.db.list_collection_names():
                self.db.create_collection('audit_logs')
                self.db['audit_logs'].create_index('timestamp', expireAfterSeconds=2592000)  # 30 days
                print("   [+] Created collection: audit_logs")
            
            if 'statistics' not in self.db.list_collection_names():
                self.db.create_collection('statistics')
                print("   [+] Created collection: statistics")
        
        except Exception as e:
            print(f"   [!] Error initializing collections: {e}")
    
    def save_device_key(self, device_id: str, key_data: Dict[str, Any]) -> bool:
        """Save device key to MongoDB"""
        if not self.connected:
            return False
        
        try:
            key_data['device_id'] = device_id
            key_data['created_at'] = datetime.now()
            key_data['is_active'] = True
            
            self.db['device_keys'].update_one(
                {'device_id': device_id},
                {'$set': key_data},
                upsert=True
            )
            
            # Update statistics
            self._update_stats('total_devices', 1)
            
            return True
            
        except Exception as e:
            print(f"[-] Error saving device key: {e}")
            return False
    
    def get_device_key(self, device_id: str) -> Optional[Dict]:
        """Retrieve device key from MongoDB"""
        if not self.connected:
            return None
        
        try:
            key = self.db['device_keys'].find_one({'device_id': device_id})
            return key
        except Exception as e:
            print(f"[-] Error retrieving device key: {e}")
            return None
    
    def get_all_device_keys(self) -> List[Dict]:
        """Get all device keys"""
        if not self.connected:
            return []
        
        try:
            keys = list(self.db['device_keys'].find({}))
            # Convert MongoDB ObjectId to string for JSON serialization
            for key in keys:
                if '_id' in key:
                    key['_id'] = str(key['_id'])
            return keys
        except Exception as e:
            print(f"[-] Error retrieving all device keys: {e}")
            return []
    
    def save_audit_log(self, log_entry: Dict[str, Any]) -> bool:
        """Save audit log entry"""
        if not self.connected:
            return False
        
        try:
            log_entry['timestamp'] = datetime.now()
            
            self.db['audit_logs'].insert_one(log_entry)
            
            # Update statistics
            self._update_stats('total_audit_events', 1)
            
            return True
            
        except Exception as e:
            print(f"[-] Error saving audit log: {e}")
            return False
    
    def get_all_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        if not self.connected:
            return []
        
        try:
            logs = list(self.db['audit_logs'].find().sort('timestamp', -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                if '_id' in log:
                    log['_id'] = str(log['_id'])
            
            return logs
            
        except Exception as e:
            print(f"[-] Error retrieving audit logs: {e}")
            return []
    
    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """Get device status from audit logs"""
        if not self.connected:
            return None
        
        try:
            logs = list(self.db['audit_logs'].find({'device_id': device_id}))
            
            status = {
                "total_events": len(logs),
                "successful_auths": len([l for l in logs if l.get('event_type') == 'AUTHENTICATED']),
                "failed_auths": len([l for l in logs if l.get('event_type') == 'AUTH_FAILED']),
                "last_event": logs[0]['timestamp'] if logs else None
            }
            
            return status
            
        except Exception as e:
            print(f"[-] Error getting device status: {e}")
            return None
    
    def _update_stats(self, stat_name: str, increment: int = 1):
        """Update statistics"""
        try:
            self.db['statistics'].update_one(
                {'name': 'system_stats'},
                {'$inc': {stat_name: increment}},
                upsert=True
            )
        except Exception as e:
            print(f"[!] Error updating stats: {e}")
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        if not self.connected:
            return {}
        
        try:
            stats = self.db['statistics'].find_one({'name': 'system_stats'})
            return stats if stats else {}
        except Exception as e:
            print(f"[-] Error getting statistics: {e}")
            return {}
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            print("[*] Disconnected from MongoDB")

# Test function
def test_storage():
    """Test storage manager"""
    print("\n" + "="*70)
    print("TESTING STORAGE MANAGER")
    print("="*70 + "\n")
    
    storage = StorageManager()
    
    if not storage.connect():
        print("[-] Failed to connect")
        return
    
    # Test saving device key
    print("[*] Testing device key storage...")
    test_key = {
        "public_key": "0x" + "aa" * 32,
        "shared_secret": "0x" + "bb" * 32,
        "gateway_id": "GATEWAY_001",
        "blockchain_tx": "0x123456",
        "blockchain_block": 100
    }
    
    if storage.save_device_key("TEST_DEVICE_001", test_key):
        print("[+] Device key saved successfully")
    else:
        print("[-] Failed to save device key")
    
    # Test retrieving device key
    print("[*] Testing device key retrieval...")
    retrieved_key = storage.get_device_key("TEST_DEVICE_001")
    if retrieved_key:
        print(f"[+] Device key retrieved: {retrieved_key.get('device_id')}")
    else:
        print("[-] Failed to retrieve device key")
    
    # Test saving audit log
    print("[*] Testing audit log storage...")
    test_log = {
        "event_type": "TEST_EVENT",
        "device_id": "TEST_DEVICE_001",
        "message": "Test audit log entry"
    }
    
    if storage.save_audit_log(test_log):
        print("[+] Audit log saved successfully")
    else:
        print("[-] Failed to save audit log")
    
    # Test getting statistics
    print("[*] Testing statistics retrieval...")
    stats = storage.get_statistics()
    print(f"[+] Statistics: {stats}")
    
    storage.disconnect()
    print("\n[*] Tests completed\n")

if __name__ == "__main__":
    test_storage()
