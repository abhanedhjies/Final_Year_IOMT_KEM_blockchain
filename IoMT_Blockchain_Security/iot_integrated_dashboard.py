"""
IoT Device & Blockchain Management Dashboard - INTEGRATED
==========================================================

Full integration with:
- Real Ganache Blockchain (localhost:8545)
- Real MongoDB (localhost:27017)
- Smart Contract Registration
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, List
from storage import StorageManager
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256, HMAC

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

try:
    from flask import Flask, jsonify, render_template_string, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

class GanacheBlockchainIntegration:
    """Integrate with Ganache blockchain on localhost:8545"""
    
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.account = None
        self.connected = False
        self.connect_to_ganache()
    
    def connect_to_ganache(self) -> bool:
        """Connect to Ganache blockchain"""
        try:
            # Connect to Ganache (port 7545 for GUI, 8545 for CLI)
            self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
            
            if not self.w3.is_connected():
                print("[-] Cannot connect to Ganache at http://127.0.0.1:7545")
                print("    Make sure Ganache GUI or CLI is running")
                return False
            
            print("[+] Connected to Ganache blockchain")
            print(f"    Chain ID: {self.w3.eth.chain_id}")
            print(f"    Current Block: {self.w3.eth.block_number}")
            
            # Get first account
            accounts = self.w3.eth.accounts
            if not accounts:
                print("[-] No accounts available in Ganache")
                return False
            
            self.account = accounts[0]
            print(f"[+] Using account: {self.account}")
            
            # Try to load deployed contract
            self.load_contract()
            self.connected = True
            return True
            
        except Exception as e:
            print(f"[-] Ganache connection error: {e}")
            print("    Make sure Ganache is running: npx ganache --host 0.0.0.0 --port 8545")
            return False
    
    def load_contract(self):
        """Load smart contract from deployment"""
        try:
            import os
            # Try multiple possible paths
            artifact_paths = [
                'blockchain/artifacts/PostQuantumKeyRegistry.json',
                'artifacts/PostQuantumKeyRegistry.json',
                './blockchain/artifacts/PostQuantumKeyRegistry.json',
            ]
            
            artifact_path = None
            for path in artifact_paths:
                if os.path.exists(path):
                    artifact_path = path
                    break
            
            if not artifact_path:
                print("[-] Contract artifact not found")
                return False
                
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
                contract_abi = artifact['abi']
                
                # Try to get deployed address from file
                try:
                    addr_paths = ['blockchain/deployment_address.txt', 'deployment_address.txt', './blockchain/deployment_address.txt']
                    contract_address = None
                    for addr_path in addr_paths:
                        if os.path.exists(addr_path):
                            with open(addr_path, 'r') as addr_file:
                                contract_address = addr_file.read().strip()
                                break
                    
                    if contract_address:
                        self.contract = self.w3.eth.contract(
                            address=Web3.to_checksum_address(contract_address),
                            abi=contract_abi
                        )
                        print(f"[+] Contract loaded at: {contract_address}")
                        return True
                    else:
                        print("[-] Contract deployment address file not found")
                        return False
                except Exception as e:
                    print(f"[-] Error reading contract address: {e}")
                    return False
                    
        except Exception as e:
            print(f"[-] Error loading contract: {e}")
            return False
    
    def register_device_on_blockchain(self, device_id: str, public_key: str, shared_secret: str) -> Dict[str, Any]:
        """Register device on blockchain"""
        if not self.contract:
            return {"success": False, "error": "Contract not deployed"}
        
        try:
            # Convert keys to bytes
            kyber_key = bytes.fromhex(public_key[2:] if public_key.startswith('0x') else public_key)
            dilithium_key = bytes.fromhex(shared_secret[2:] if shared_secret.startswith('0x') else shared_secret)
            
            # First try to send the transaction via the provider (RPC signing) using an unlocked Ganache account
            try:
                # Let the node estimate gas and sign the tx; some Ganache builds prefer not setting gasPrice explicitly
                try:
                    est_gas = self.contract.functions.registerDeviceKey(device_id, kyber_key, dilithium_key).estimate_gas({'from': self.account})
                except Exception:
                    est_gas = 300000

                tx_params = {
                    'from': self.account,
                    'gas': est_gas
                }

                tx_hash = self.contract.functions.registerDeviceKey(
                    device_id,
                    kyber_key,
                    dilithium_key
                ).transact(tx_params)

                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                return {
                    "success": True,
                    "tx_hash": tx_hash.hex() if isinstance(tx_hash, (bytes, bytearray)) else str(tx_hash),
                    "block_number": receipt['blockNumber'],
                    "gas_used": receipt['gasUsed']
                }
            except Exception as rpc_exc:
                # If RPC signing failed (e.g., node refuses signing), fall back to local signing
                print(f"[!] RPC transact failed, attempting local signing fallback: {rpc_exc}")

            # Fallback: Sign and send transaction locally using a private key
            import os
            private_key = os.getenv('GANACHE_PRIVATE_KEY')
            if not private_key:
                # Fallback to the default (legacy) key for local testing, but warn the user
                private_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb476caded732d6d3946a7ec88c60'
                print("[!] GANACHE_PRIVATE_KEY not set - using default fallback key. Set GANACHE_PRIVATE_KEY env var to match your Ganache account to avoid mismatch errors.")

            # Build a raw transaction and sign with provided private key
            tx = self.contract.functions.registerDeviceKey(
                device_id,
                kyber_key,
                dilithium_key
            ).build_transaction({
                'from': self.account,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account),
            })

            try:
                signer_address = self.w3.eth.account.from_key(private_key).address
            except Exception as e:
                return {"success": False, "error": f"Invalid private key provided: {e}"}

            # Use signer-derived address and correct nonce
            tx['from'] = signer_address
            tx['nonce'] = self.w3.eth.get_transaction_count(signer_address)
            tx['chainId'] = getattr(self.w3.eth, 'chain_id', None) or self.w3.net.chainId

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)

            # web3/eth-account versions differ in attribute names for signed tx raw bytes
            raw_tx = None
            for attr in ('rawTransaction', 'raw_transaction', 'raw_signed_transaction', 'raw_tx'):
                raw_tx = getattr(signed_tx, attr, None)
                if raw_tx:
                    break

            if raw_tx is None and isinstance(signed_tx, (bytes, bytearray)):
                raw_tx = signed_tx

            if raw_tx is None:
                return {"success": False, "error": "Signing returned no raw transaction bytes"}

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "success": True,
                "tx_hash": tx_hash.hex() if isinstance(tx_hash, (bytes, bytearray)) else str(tx_hash),
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed']
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_device_from_blockchain(self, device_id: str) -> Dict[str, Any]:
        """Retrieve device from blockchain"""
        if not self.contract:
            return {"error": "Contract not deployed"}
        
        try:
            device_key = self.contract.functions.getDeviceKey(device_id).call()
            return {
                "device_id": device_id,
                "owner": device_key[0],
                "kyber_key": device_key[1].hex(),
                "dilithium_key": device_key[2].hex(),
                "registration_time": datetime.fromtimestamp(device_key[3]).isoformat(),
                "is_active": device_key[4]
            }
        except Exception as e:
            return {"error": str(e)}

    def get_registration_event(self, device_id: str) -> Dict[str, Any]:
        """Find KeyRegistered event for a device and return tx details"""
        if not self.contract:
            return {"error": "Contract not deployed"}

        try:
            # Create a filter for KeyRegistered events matching the deviceId
            try:
                event_filter = self.contract.events.KeyRegistered.createFilter(
                    fromBlock=0, toBlock='latest', argument_filters={'deviceId': device_id}
                )
                entries = event_filter.get_all_entries()
            except Exception:
                # Fallback: fetch all events and filter manually
                entries = []
                logs = self.w3.eth.get_logs({'fromBlock': 0, 'toBlock': 'latest', 'address': self.contract.address})
                for lg in logs:
                    try:
                        ev = self.contract.events.KeyRegistered().processLog(lg)
                        if ev['args'].get('deviceId') == device_id:
                            entries.append(ev)
                    except Exception:
                        continue

            if not entries:
                return {"error": "Registration event not found"}

            ev = entries[-1]
            return {
                "tx_hash": ev['transactionHash'].hex() if isinstance(ev['transactionHash'], (bytes, bytearray)) else str(ev['transactionHash']),
                "block_number": ev['blockNumber'],
                "owner": ev['args'].get('owner'),
                "timestamp": ev['args'].get('timestamp')
            }
        except Exception as e:
            return {"error": str(e)}

class SimpleAuthGateway:
    """Simple authentication gateway for PQ-KEM"""
    
    def authenticate(self, device_id: str, gateway_id: str) -> Dict[str, Any]:
        """Perform device authentication and generate keys"""
        try:
            # Generate device keypair (simulate Kyber)
            device_private_key = get_random_bytes(64)
            h = SHA256.new(device_private_key)
            public_key = h.digest() + get_random_bytes(32)
            
            # Gateway performs KEM encapsulation
            ephemeral_key = get_random_bytes(32)
            shared_secret = SHA256.new(ephemeral_key + public_key).digest()
            
            return {
                "success": True,
                "data": {
                    "public_key": public_key.hex(),
                    "shared_secret": shared_secret.hex(),
                    "device_id": device_id,
                    "gateway_id": gateway_id
                },
                "message": "Authentication successful"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

class DeviceManager:
    """Manage IoT devices with blockchain and MongoDB integration"""
    
    def __init__(self, storage: StorageManager, blockchain: GanacheBlockchainIntegration):
        self.storage = storage
        self.blockchain = blockchain
        self.gateway = SimpleAuthGateway()
        self.simulated_devices = {}
    
    def create_simulated_device(self, device_info: Dict) -> Dict[str, Any]:
        """Create a simulated device"""
        device_id = device_info.get("device_id")
        device_type = device_info.get("device_type")
        
        device = {
            "device_id": device_id,
            "device_type": device_type,
            "manufacturer": device_info.get("manufacturer", "Unknown"),
            "status": "SIMULATED",
            "created_at": datetime.now().isoformat(),
            "is_registered_db": False,
            "is_registered_blockchain": False,
            "blockchain_tx": None,
            "encryption": None
        }
        
        self.simulated_devices[device_id] = device
        return device
    
    def register_to_blockchain(self, device_id: str, gateway_id: str = "GATEWAY_HUB_001") -> Dict[str, Any]:
        """Register device to blockchain AND MongoDB"""
        
        if device_id not in self.simulated_devices:
            return {"success": False, "error": "Device not found"}
        
        # Authenticate device (generates PQ keys)
        auth_result = self.gateway.authenticate(device_id, gateway_id)
        
        if not auth_result["success"]:
            return {"success": False, "error": auth_result["message"]}
        
        public_key = auth_result["data"]["public_key"]
        shared_secret = auth_result["data"]["shared_secret"]
        
        # 1. Register on Ganache blockchain
        blockchain_result = self.blockchain.register_device_on_blockchain(
            device_id, public_key, shared_secret
        )
        
        if not blockchain_result["success"]:
            return {
                "success": False,
                "error": f"Blockchain registration failed: {blockchain_result.get('error')}",
                "note": "Make sure Ganache is running and contract is deployed"
            }
        
        # 2. Save to MongoDB
        key_data = {
            "public_key": public_key,
            "shared_secret": shared_secret,
            "gateway_id": gateway_id,
            "authenticated_at": datetime.now().isoformat(),
            "blockchain_tx": blockchain_result.get("tx_hash"),
            "blockchain_block": blockchain_result.get("block_number")
        }
        
        if not self.storage.save_device_key(device_id, key_data):
            return {"success": False, "error": "Failed to save to MongoDB"}
        
        # 3. Create audit log
        log_entry = {
            "event_type": "AUTHENTICATED",
            "device_id": device_id,
            "gateway_id": gateway_id,
            "message": f"Device registered to blockchain and MongoDB",
            "metadata": {
                "device_type": self.simulated_devices[device_id]["device_type"],
                "auth_protocol": "PQ-KEM",
                "blockchain_tx": blockchain_result.get("tx_hash"),
                "block_number": blockchain_result.get("block_number")
            }
        }
        
        self.storage.save_audit_log(log_entry)
        
        # 4. Update device
        self.simulated_devices[device_id]["is_registered_db"] = True
        self.simulated_devices[device_id]["is_registered_blockchain"] = True
        self.simulated_devices[device_id]["blockchain_tx"] = blockchain_result.get("tx_hash")
        self.simulated_devices[device_id]["encryption"] = {
            "protocol": "Kyber-inspired PQ-KEM",
            "algorithm": "HMAC-SHA256",
            "public_key": public_key[:32] + "...",
            "key_size": 256,
            "shared_secret": shared_secret[:32] + "..."
        }
        
        return {
            "success": True,
            "device_id": device_id,
            "blockchain_tx": blockchain_result.get("tx_hash"),
            "block_number": blockchain_result.get("block_number"),
            "mongodb_stored": True,
            "encryption": self.simulated_devices[device_id]["encryption"],
            "message": "Device registered to BOTH Ganache and MongoDB!"
        }
    
    def get_device_encryption_details(self, device_id: str) -> Dict[str, Any]:
        """Get detailed encryption information"""
        device_key = self.storage.get_device_key(device_id)
        
        if not device_key:
            return {"error": "Device not found"}
        # If blockchain details are missing in DB, attempt to read event logs on-chain
        blockchain_tx = device_key.get("blockchain_tx")
        blockchain_block = device_key.get("blockchain_block")

        if not blockchain_tx or blockchain_tx == 'N/A':
            try:
                ev = self.blockchain.get_registration_event(device_id)
                if ev and 'error' not in ev:
                    blockchain_tx = ev.get('tx_hash')
                    blockchain_block = ev.get('block_number')
                    # Persist the backfilled values to MongoDB
                    device_key['blockchain_tx'] = blockchain_tx
                    device_key['blockchain_block'] = blockchain_block
                    try:
                        self.storage.save_device_key(device_id, device_key)
                    except Exception:
                        pass
            except Exception:
                pass

        return {
            "device_id": device_id,
            "public_key_full": device_key.get("public_key"),
            "shared_secret_full": device_key.get("shared_secret"),
            "encryption_algorithm": "HMAC-SHA256",
            "key_exchange_protocol": "Kyber-inspired Post-Quantum KEM",
            "is_active": device_key.get("is_active"),
            "authenticated_at": device_key.get("authenticated_at"),
            "gateway_id": device_key.get("gateway_id"),
            "blockchain_tx": blockchain_tx,
            "blockchain_block": blockchain_block
        }
    
    def get_all_stored_devices(self) -> List[Dict]:
        """Get all devices from MongoDB"""
        devices = self.storage.get_all_device_keys()
        
        result = []
        for device in devices:
            status = self.storage.get_device_status(device["device_id"])
            result.append({
                "device_id": device["device_id"],
                "is_active": device.get("is_active"),
                "gateway_id": device.get("gateway_id"),
                "authenticated_at": device.get("authenticated_at"),
                "total_events": status["total_events"] if status else 0,
                "successful_auths": status["successful_auths"] if status else 0,
                "public_key_preview": device.get("public_key", "")[:24] + "...",
                "blockchain_tx": device.get("blockchain_tx", "N/A"),
                "blockchain_block": device.get("blockchain_block", "N/A")
            })
        
        return result

def create_dashboard_app(storage: StorageManager, blockchain: GanacheBlockchainIntegration) -> 'Flask':
    """Create the main dashboard application"""
    
    if not FLASK_AVAILABLE:
        print("[-] Flask not available")
        return None
    
    app = Flask(__name__)
    CORS(app)
    
    device_manager = DeviceManager(storage, blockchain)
    
    # ========== HTML INTERFACE ==========
    DASHBOARD_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IoT Device & Blockchain Management - INTEGRATED</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
            }
            
            header {
                background: white;
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            h1 {
                color: #667eea;
                font-size: 32px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .status-badges {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            
            .badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }
            
            .badge-success { background: #d4edda; color: #155724; }
            .badge-error { background: #f8d7da; color: #721c24; }
            
            .grid-2 {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 25px;
                margin-bottom: 25px;
            }
            
            .grid-3 {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 25px;
            }
            
            .panel {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .panel-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
            }
            
            input, select, textarea {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                width: 100%;
            }
            
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            
            .info-box {
                background: #f0f7ff;
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 15px;
                font-size: 13px;
            }
            
            .info-box strong {
                color: #667eea;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 28px;
                font-weight: bold;
                margin: 10px 0;
            }
            
            .metric-label {
                font-size: 12px;
                opacity: 0.9;
            }
            
            .device-list {
                max-height: 400px;
                overflow-y: auto;
            }
            
            .device-item {
                background: #f9f9f9;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 10px;
                border-left: 4px solid #667eea;
            }
            
            .device-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .device-name {
                font-weight: bold;
                color: #333;
            }
            
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            }
            
            .status-registered { background: #d4edda; color: #155724; }
            
            .device-meta {
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }
            
            .blockchain-info {
                background: #e8f4f8;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
                word-break: break-all;
                margin-top: 8px;
            }
            
            .message {
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 10px;
            }
            
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .encryption-display {
                background: #f0f7ff;
                padding: 12px;
                border-radius: 6px;
                font-family: monospace;
                font-size: 11px;
                word-break: break-all;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔗⛓️ IoT Device & Blockchain Management (INTEGRATED)</h1>
                <p style="color: #666;">Ganache Blockchain + MongoDB + PQ-KEM Encryption</p>
                <div class="status-badges">
                    <div class="badge badge-success" id="mongoStatus">✓ MongoDB: Connected</div>
                    <div class="badge" id="ganacheStatus">Loading...</div>
                </div>
            </header>
            
            <!-- Main Grid -->
            <div class="grid-2">
                <!-- LEFT: Device Simulation & Registration -->
                <div>
                    <!-- Device Simulator -->
                    <div class="panel" style="margin-bottom: 20px;">
                        <div class="panel-title">📱 Device Simulator</div>
                        <div id="simulatorMessage"></div>
                        
                        <div class="form-group">
                            <label>Device ID</label>
                            <input type="text" id="deviceId" placeholder="e.g., BP_MON_001" value="BP_MON_001">
                        </div>
                        
                        <div class="form-group">
                            <label>Device Type</label>
                            <select id="deviceType">
                                <option value="Blood Pressure Monitor">Blood Pressure Monitor</option>
                                <option value="Glucose Meter">Glucose Meter</option>
                                <option value="Pulse Oximeter">Pulse Oximeter</option>
                                <option value="Temperature Sensor">Temperature Sensor</option>
                                <option value="ECG Monitor">ECG Monitor</option>
                            </select>
                        </div>
                        
                        <button onclick="createDevice()">Create Simulated Device</button>
                    </div>
                    
                    <!-- Blockchain Registration -->
                    <div class="panel">
                        <div class="panel-title">⛓️ Blockchain + MongoDB Registration</div>
                        <div id="registrationMessage"></div>
                        
                        <div class="info-box">
                            <strong>ℹ️</strong> This will register to BOTH Ganache blockchain AND MongoDB
                        </div>
                        
                        <div class="form-group">
                            <label>Select Device</label>
                            <select id="deviceSelect">
                                <option value="">-- Select a device --</option>
                            </select>
                        </div>
                        
                        <button onclick="registerToBlockchain()">Register to Blockchain & MongoDB</button>
                    </div>
                </div>
                
                <!-- RIGHT: Encryption Display -->
                <div>
                    <div class="panel">
                        <div class="panel-title">🔐 Encryption & Blockchain Details</div>
                        <div id="encryptionDisplay">
                            <div class="info-box">
                                <strong>ℹ️</strong> Select a device to view complete encryption and blockchain details
                            </div>
                        </div>
                        
                        <div class="form-group" style="margin-top: 20px;">
                            <label>View Device Details</label>
                            <select id="encryptionDeviceSelect" onchange="viewEncryption()">
                                <option value="">-- Select a device --</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Metrics Row -->
            <div class="grid-3">
                <div class="metric-card">
                    <div class="metric-label">Simulated Devices</div>
                    <div class="metric-value" id="simulatedCount">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Registered (DB + Blockchain)</div>
                    <div class="metric-value" id="registeredCount">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Audit Events</div>
                    <div class="metric-value" id="eventCount">0</div>
                </div>
            </div>
            
            <!-- Bottom Grid -->
            <div class="grid-2">
                <!-- Stored Devices -->
                <div class="panel">
                    <div class="panel-title">📊 Devices (MongoDB + Blockchain)</div>
                    <div class="device-list" id="storedDevicesList"></div>
                </div>
                
                <!-- Audit Events -->
                <div class="panel">
                    <div class="panel-title">📝 Authentication Events</div>
                    <div class="device-list" id="auditEventsList"></div>
                </div>
            </div>
            
            <!-- Device Details Panel -->
            <div class="panel" style="margin-top: 25px;">
                <div class="panel-title">🔍 Device Details & Encryption Keys</div>
                <div id="deviceDetailsPanel" style="color: #999; padding: 20px; text-align: center;">
                    Click on a device to view full encryption and blockchain details
                </div>
            </div>
        </div>
        
        <script>
            let simulatedDevices = {};
            
            function checkGanacheStatus() {
                fetch('/api/ganache-status')
                    .then(r => r.json())
                    .then(data => {
                        const badge = document.getElementById('ganacheStatus');
                        if (data.connected) {
                            badge.className = 'badge badge-success';
                            badge.textContent = '✓ Ganache: Connected (' + data.chain_id + ')';
                        } else {
                            badge.className = 'badge badge-error';
                            badge.textContent = '✗ Ganache: ' + data.message;
                        }
                    });
            }
            
            function createDevice() {
                const deviceId = document.getElementById('deviceId').value;
                const deviceType = document.getElementById('deviceType').value;
                
                if (!deviceId) {
                    showMessage('simulatorMessage', 'Device ID is required', 'error');
                    return;
                }
                
                fetch('/api/create-device', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({device_id: deviceId, device_type: deviceType, manufacturer: 'Medical Corp'})
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        simulatedDevices[deviceId] = data.device;
                        showMessage('simulatorMessage', `✓ Device "${deviceId}" simulated!`, 'success');
                        updateDeviceSelects();
                        updateMetrics();
                        document.getElementById('deviceId').value = '';
                    } else {
                        showMessage('simulatorMessage', data.error, 'error');
                    }
                });
            }
            
            function registerToBlockchain() {
                const deviceId = document.getElementById('deviceSelect').value;
                
                if (!deviceId) {
                    showMessage('registrationMessage', 'Please select a device', 'error');
                    return;
                }
                
                showMessage('registrationMessage', '⏳ Registering to Ganache and MongoDB...', 'success');
                
                fetch('/api/register-blockchain', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({device_id: deviceId, gateway_id: 'GATEWAY_HUB_001'})
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showMessage('registrationMessage', 
                            `✓ Registered to Ganache!\n TX: ${data.blockchain_tx.substring(0, 20)}...\n Block: ${data.block_number}`, 
                            'success');
                        updateStoredDevices();
                        updateMetrics();
                        viewEncryptionDetails(deviceId);
                    } else {
                        showMessage('registrationMessage', `✗ ${data.error}`, 'error');
                    }
                });
            }
            
            function viewEncryption() {
                const deviceId = document.getElementById('encryptionDeviceSelect').value;
                if (deviceId) {
                    viewEncryptionDetails(deviceId);
                }
            }
            
            function viewEncryptionDetails(deviceId) {
                fetch(`/api/encryption-details/${deviceId}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) {
                            document.getElementById('encryptionDisplay').innerHTML = 
                                '<div class="info-box"><strong>❌ Device not found</strong></div>';
                            return;
                        }
                        
                        const html = `
                            <div style="background: #f0f7ff; padding: 15px; border-radius: 6px;">
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">Device ID:</strong> ${data.device_id}
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">Status:</strong>
                                    <span style="background: #d4edda; color: #155724; padding: 4px 12px; border-radius: 20px; font-size: 12px;">${data.is_active ? '✓ ACTIVE' : '✗ INACTIVE'}</span>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">🔑 Public Key (Kyber):</strong>
                                    <div class="encryption-display">${data.public_key_full}</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">🔒 Shared Secret (KEM):</strong>
                                    <div class="encryption-display">${data.shared_secret_full}</div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">🔐 Encryption:</strong>
                                    <div style="font-size: 12px; margin-top: 5px;">
                                        Protocol: ${data.key_exchange_protocol}<br>
                                        Algorithm: ${data.encryption_algorithm}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <strong style="color: #667eea;">⛓️ Blockchain Details:</strong>
                                    <div class="blockchain-info">
                                        TX: ${data.blockchain_tx || 'N/A'}<br>
                                        Block: ${data.blockchain_block || 'N/A'}
                                    </div>
                                </div>
                            </div>
                        `;
                        document.getElementById('encryptionDisplay').innerHTML = html;
                    });
            }
            
            function updateDeviceSelects() {
                const select1 = document.getElementById('deviceSelect');
                const select2 = document.getElementById('encryptionDeviceSelect');
                
                const options = Object.keys(simulatedDevices).map(id => 
                    `<option value="${id}">${id}</option>`
                ).join('');
                
                select1.innerHTML = '<option value="">-- Select a device --</option>' + options;
                select2.innerHTML = '<option value="">-- Select a device --</option>' + options;
            }
            
            function showDeviceDetails(deviceId) {
                fetch(`/api/encryption-details/${deviceId}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) {
                            alert('Error: ' + data.error);
                            return;
                        }
                        
                        let detailsHtml = `
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;">
                                <h4 style="color: #667eea; margin-bottom: 10px;">Encryption Details</h4>
                                <div style="font-size: 12px; line-height: 1.8; font-family: monospace;">
                                    <strong>Device ID:</strong> ${data.device_id}<br>
                                    <strong>Algorithm:</strong> ${data.encryption_algorithm}<br>
                                    <strong>Key Exchange:</strong> ${data.key_exchange_protocol}<br>
                                    <strong>Gateway:</strong> ${data.gateway_id}<br>
                                    <strong>Status:</strong> ${data.is_active ? '✓ Active' : '✗ Inactive'}<br>
                                    <strong>Authenticated At:</strong> ${data.authenticated_at}<br>
                                    <br>
                                    <strong>Public Key (Full):</strong><br>
                                    <div style="background: white; padding: 8px; border-radius: 4px; word-break: break-all; color: #333;">
                                        ${data.public_key_full || 'N/A'}
                                    </div>
                                    <br>
                                    <strong>Shared Secret (Full):</strong><br>
                                    <div style="background: white; padding: 8px; border-radius: 4px; word-break: break-all; color: #333;">
                                        ${data.shared_secret_full || 'N/A'}
                                    </div>
                                    <br>
                                    <h4 style="color: #667eea; margin-top: 15px;">Blockchain Details</h4>
                                    <strong>TX Hash:</strong> <span style="color: #0066cc;">${data.blockchain_tx || 'N/A'}</span><br>
                                    <strong>Block Number:</strong> ${data.blockchain_block || 'N/A'}<br>
                                </div>
                            </div>
                        `;
                        
                        const detailsPanel = document.getElementById('deviceDetailsPanel');
                        if (detailsPanel) {
                            detailsPanel.innerHTML = detailsHtml;
                        }
                    });
            }
            
            function updateStoredDevices() {
                fetch('/api/stored-devices')
                    .then(r => r.json())
                    .then(devices => {
                        const html = devices.map(d => `
                            <div class="device-item" style="cursor: pointer;" onclick="showDeviceDetails('${d.device_id}')">
                                <div class="device-header">
                                    <div class="device-name">${d.device_id}</div>
                                    <span class="status-badge status-registered">✓ Registered</span>
                                </div>
                                <div class="device-meta">Gateway: ${d.gateway_id}</div>
                                <div class="device-meta">Key: ${d.public_key_preview}</div>
                                <div class="blockchain-info">
                                    <strong>TX:</strong> ${d.blockchain_tx}<br>
                                    <strong>Block:</strong> ${d.blockchain_block}
                                </div>
                                <div style="font-size: 11px; color: #0066cc; margin-top: 8px;">👁️ Click to view full details</div>
                            </div>
                        `).join('');
                        
                        document.getElementById('storedDevicesList').innerHTML = html || '<p style="color: #999;">No devices registered yet</p>';
                    });
            }
            
            function updateAuditEvents() {
                fetch('/api/audit-events')
                    .then(r => r.json())
                    .then(events => {
                        const html = events.slice(0, 15).map(e => `
                            <div class="device-item" style="padding: 10px;">
                                <div style="font-weight: 600; color: #667eea;">${new Date(e.timestamp).toLocaleTimeString()}</div>
                                <div style="font-size: 12px; margin-top: 3px;"><strong>${e.event_type}</strong></div>
                                <div style="font-size: 11px; color: #666; margin-top: 2px;">${e.device_id}</div>
                            </div>
                        `).join('');
                        
                        document.getElementById('auditEventsList').innerHTML = html || '<p style="color: #999;">No events yet</p>';
                    });
            }
            
            function updateMetrics() {
                document.getElementById('simulatedCount').textContent = Object.keys(simulatedDevices).length;
                
                fetch('/api/metrics')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('registeredCount').textContent = data.registered_count;
                        document.getElementById('eventCount').textContent = data.event_count;
                    });
            }
            
            function showMessage(elementId, message, type) {
                const el = document.getElementById(elementId);
                el.innerHTML = `<div class="message ${type}">${message}</div>`;
                setTimeout(() => el.innerHTML = '', 5000);
            }
            
            // Initial load
            checkGanacheStatus();
            updateStoredDevices();
            updateAuditEvents();
            updateMetrics();
            
            // Refresh every 10 seconds
            setInterval(() => {
                checkGanacheStatus();
                updateStoredDevices();
                updateAuditEvents();
                updateMetrics();
            }, 10000);
        </script>
    </body>
    </html>
    """
    
    # ========== API ENDPOINTS ==========
    
    @app.route('/api/ganache-status', methods=['GET'])
    def ganache_status():
        """Get Ganache connection status"""
        return jsonify({
            "connected": blockchain.connected,
            "chain_id": blockchain.w3.eth.chain_id if blockchain.w3 else None,
            "message": "Connected" if blockchain.connected else "Not connected to Ganache"
        }), 200

    @app.route('/api/ganache-debug', methods=['GET'])
    def ganache_debug():
        """Debug info for Ganache - provider, accounts and balances"""
        try:
            provider = getattr(blockchain.w3.provider, 'endpoint_uri', None)
            accounts = blockchain.w3.eth.accounts if blockchain.w3 else []
            balances = {}
            for a in accounts[:5]:
                try:
                    balances[a] = str(blockchain.w3.from_wei(blockchain.w3.eth.get_balance(a), 'ether'))
                except Exception:
                    balances[a] = 'N/A'
            return jsonify({
                'provider': provider,
                'default_account': blockchain.account,
                'accounts_preview': accounts[:5],
                'balances': balances,
                'gas_price': str(blockchain.w3.eth.gas_price)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/create-device', methods=['POST'])
    def create_device():
        """Create a simulated device"""
        try:
            data = request.json
            device = device_manager.create_simulated_device(data)
            return jsonify({"success": True, "device": device}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/register-blockchain', methods=['POST'])
    def register_blockchain():
        """Register device to blockchain and MongoDB"""
        try:
            data = request.json
            result = device_manager.register_to_blockchain(
                data.get("device_id"),
                data.get("gateway_id", "GATEWAY_HUB_001")
            )
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/sync-blockchain-details', methods=['POST'])
    def sync_blockchain_details():
        """Scan stored devices and backfill blockchain tx/hash for devices missing it"""
        try:
            devices = storage.get_all_device_keys()
            updated = []
            for d in devices:
                device_id = d.get('device_id')
                if not device_id:
                    continue
                current_tx = d.get('blockchain_tx')
                if current_tx and current_tx != 'N/A':
                    continue

                ev = blockchain.get_registration_event(device_id)
                if not ev or 'error' in ev:
                    continue

                # Update DB entry with tx & block
                key = storage.get_device_key(device_id) or {}
                key['blockchain_tx'] = ev.get('tx_hash')
                key['blockchain_block'] = ev.get('block_number')
                storage.save_device_key(device_id, key)
                updated.append({'device_id': device_id, 'tx': ev.get('tx_hash')})

            return jsonify({"success": True, "updated": updated}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/encryption-details/<device_id>', methods=['GET'])
    def encryption_details(device_id):
        """Get encryption details for a device"""
        try:
            details = device_manager.get_device_encryption_details(device_id)
            return jsonify(details), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/stored-devices', methods=['GET'])
    def stored_devices():
        """Get all stored devices"""
        try:
            devices = device_manager.get_all_stored_devices()
            return jsonify(devices), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/audit-events', methods=['GET'])
    def audit_events():
        """Get audit events"""
        try:
            events = storage.get_all_audit_logs(limit=50)
            return jsonify(events), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/metrics', methods=['GET'])
    def metrics():
        """Get system metrics"""
        try:
            stats = storage.get_statistics()
            return jsonify({
                "registered_count": stats.get("total_devices", 0),
                "event_count": stats.get("total_audit_events", 0)
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/', methods=['GET'])
    def dashboard():
        """Main dashboard"""
        return render_template_string(DASHBOARD_HTML)
    
    return app

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("IoT DEVICE & BLOCKCHAIN MANAGEMENT - INTEGRATED")
    print("="*70 + "\n")
    
    # Initialize storage
    storage = StorageManager()
    print("[*] Initializing MongoDB...")
    if not storage.connect():
        print("[!] Failed to connect to MongoDB")
        return
    print("[+] MongoDB connected successfully\n")
    
    # Initialize blockchain
    print("[*] Initializing Ganache blockchain integration...")
    if not WEB3_AVAILABLE:
        print("[-] Web3.py not available. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "web3"])
    
    blockchain = GanacheBlockchainIntegration()
    print()
    
    # Create Flask app
    print("[*] Creating Flask application...")
    app = create_dashboard_app(storage, blockchain)
    
    if not app:
        return
    
    print("[+] Application created")
    
    print("\n" + "="*70)
    print("DASHBOARD READY")
    print("="*70)
    print("[*] Dashboard: http://localhost:5000")
    print("[*] MongoDB: localhost:27017")
    print("[*] Ganache: localhost:8545")
    print("[*] Press CTRL+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        storage.disconnect()

if __name__ == "__main__":
    main()
