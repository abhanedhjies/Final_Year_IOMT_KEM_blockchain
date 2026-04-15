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
import requests
from datetime import datetime
from typing import Dict, Any, List
from storage import StorageManager
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256, HMAC
from blockchain.auth_protocol import DeviceAuthenticationSession, AuthenticationProtocol

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
        """Connect to Ganache blockchain (tries port 7545 GUI then 8545 CLI)"""
        try:
            # Try GUI port first, then CLI port
            for port in [7545, 8545]:
                w3_try = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{port}'))
                if w3_try.is_connected():
                    self.w3 = w3_try
                    print(f"[+] Connected to Ganache at port {port}")
                    break
            else:
                print("[-] Cannot connect to Ganache at ports 7545 or 8545")
                print("    Make sure Ganache GUI or CLI is running")
                return False

            if not self.w3.is_connected():
                print("[-] Cannot connect to Ganache")
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
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try to get deployed address from file
            addr_paths = [
                os.path.join(current_dir, 'blockchain/deployment_address.txt'),
                os.path.join(current_dir, 'deployment_address.txt'),
                'blockchain/deployment_address.txt',
                'deployment_address.txt',
                './blockchain/deployment_address.txt'
            ]
            
            contract_address = None
            for addr_path in addr_paths:
                if os.path.exists(addr_path):
                    try:
                        with open(addr_path, 'r') as f:
                            contract_address = f.read().strip()
                        break
                    except Exception:
                        continue
            
            if not contract_address:
                print("[-] Contract address not found in deployment files")
                return False
            
            # Get ABI from artifact
            artifact_paths = [
                os.path.join(current_dir, 'blockchain/artifacts/PostQuantumKeyRegistry.json'),
                os.path.join(current_dir, 'artifacts/PostQuantumKeyRegistry.json'),
                'blockchain/artifacts/PostQuantumKeyRegistry.json',
            ]
            
            contract_abi = None
            for path in artifact_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            artifact = json.load(f)
                            contract_abi = artifact.get('abi')
                        break
                    except Exception:
                        continue
            
            if not contract_abi:
                print("[-] Contract ABI not found")
                return False
            
            # Verify contract exists at address
            code = self.w3.eth.get_code(Web3.to_checksum_address(contract_address))
            if len(code) == 0:
                print(f"[-] No contract code at address {contract_address}")
                return False
            
            # Load contract
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=contract_abi
            )
            print(f"[+] Contract loaded at: {contract_address}")
            return True
                    
        except Exception as e:
            print(f"[-] Error loading contract: {e}")
            return False
    
    def register_device_on_blockchain(self, device_id: str, public_key: str, shared_secret: str) -> Dict[str, Any]:
        """Register device on blockchain"""
        if not self.contract:
            print(f"[DEBUG] register_device_on_blockchain: self.contract is None!")
            print(f"[DEBUG] self.w3.is_connected: {self.w3.is_connected() if self.w3 else 'w3 is None'}")
            print(f"[DEBUG] self.account: {self.account}")
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

    # Access Control
    def _transact(self, fn, extra_gas: int = 300000) -> Dict[str, Any]:
        """Helper: send a state-changing transaction to Ganache."""
        try:
            try:
                gas_est = fn.estimate_gas({'from': self.account})
            except Exception:
                gas_est = extra_gas
            tx_hash = fn.transact({'from': self.account, 'gas': gas_est})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "success": True,
                "tx_hash": tx_hash.hex() if isinstance(tx_hash, (bytes, bytearray)) else str(tx_hash),
                "block_number": receipt['blockNumber'],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_provider(self, provider_address: str, name: str, role: str) -> Dict[str, Any]:
        """Register a healthcare provider on-chain (admin only)."""
        if not self.contract:
            return {"success": False, "error": "Contract not loaded"}
        try:
            addr = Web3.to_checksum_address(provider_address)
            fn = self.contract.functions.registerProvider(addr, name, role)
            return self._transact(fn)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def revoke_provider(self, provider_address: str) -> Dict[str, Any]:
        """Revoke a healthcare provider's registration (admin only)."""
        if not self.contract:
            return {"success": False, "error": "Contract not loaded"}
        try:
            addr = Web3.to_checksum_address(provider_address)
            fn = self.contract.functions.revokeProvider(addr)
            return self._transact(fn)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def grant_access(self, provider_address: str, patient_id: str) -> Dict[str, Any]:
        """Grant a provider access to a specific patient's device data (admin only)."""
        if not self.contract:
            return {"success": False, "error": "Contract not loaded"}
        try:
            addr = Web3.to_checksum_address(provider_address)
            fn = self.contract.functions.grantAccess(addr, patient_id)
            return self._transact(fn)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def revoke_access(self, provider_address: str, patient_id: str) -> Dict[str, Any]:
        """Revoke a provider's access to a patient (admin only)."""
        if not self.contract:
            return {"success": False, "error": "Contract not loaded"}
        try:
            addr = Web3.to_checksum_address(provider_address)
            fn = self.contract.functions.revokeAccess(addr, patient_id)
            return self._transact(fn)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_access(self, provider_address: str, patient_id: str) -> bool:
        """Return True if provider currently has access to patient."""
        if not self.contract:
            return False
        try:
            addr = Web3.to_checksum_address(provider_address)
            return self.contract.functions.checkAccess(addr, patient_id).call()
        except Exception:
            return False

    def assign_device_to_patient(self, device_id: str, patient_id: str) -> Dict[str, Any]:
        """Assign an IoMT device to a patient (admin only)."""
        if not self.contract:
            return {"success": False, "error": "Contract not loaded"}
        try:
            fn = self.contract.functions.assignDeviceToPatient(device_id, patient_id)
            return self._transact(fn)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_provider(self, provider_address: str) -> Dict[str, Any]:
        """Return on-chain provider record."""
        if not self.contract:
            return {"error": "Contract not loaded"}
        try:
            addr = Web3.to_checksum_address(provider_address)
            p = self.contract.functions.getProvider(addr).call()
            return {
                "address": provider_address,
                "name": p[0],
                "role": p[1],
                "is_registered": p[2],
                "registered_at": datetime.fromtimestamp(p[3]).isoformat() if p[3] else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Return list of all providers ever registered (active + revoked)."""
        if not self.contract:
            return []
        try:
            count = self.contract.functions.getProviderCount().call()
            result = []
            for i in range(count):
                addr = self.contract.functions.getProviderAt(i).call()
                info = self.get_provider(addr)
                result.append(info)
            return result
        except Exception as e:
            return [{"error": str(e)}]

    def get_admin_address(self) -> str:
        """Return the current admin address from the contract."""
        if not self.contract:
            return ""
        try:
            return self.contract.functions.admin().call()
        except Exception:
            return ""

    def get_device_public_info(self, device_id: str) -> Dict[str, Any]:
        """Return non-sensitive public metadata about a device."""
        if not self.contract:
            return {"error": "Contract not loaded"}
        try:
            result = self.contract.functions.getDevicePublicInfo(device_id).call()
            return {
                "device_id": device_id,
                "owner": result[0],
                "registration_time": datetime.fromtimestamp(result[1]).isoformat() if result[1] else None,
                "is_active": result[2],
                "patient_id": result[3],
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
    <!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>IoMT Blockchain Security - Dashboard</title> <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"> <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"> <style> :root {
                --bg-base:      #050d1a;
                --bg-surface:   #0b1628;
                --bg-card:      #0f1e35;
                --bg-hover:     #162540;
                --border:       rgba(6,182,212,0.12);
                --border-glow:  rgba(6,182,212,0.35);
                --teal:         #0d9488;
                --cyan:         #06b6d4;
                --cyan-light:   #67e8f9;
                --indigo:       #6366f1;
                --green:        #10b981;
                --red:          #ef4444;
                --amber:        #f59e0b;
                --text-primary: #f0f9ff;
                --text-secondary:#94a3b8;
                --text-muted:   #475569;
                --font:         'Inter', sans-serif;
                --mono:         'JetBrains Mono', monospace;
                --radius:       12px;
                --radius-sm:    8px;
                --shadow:       0 4px 24px rgba(0,0,0,0.5);
                --shadow-glow:  0 0 20px rgba(6,182,212,0.15);
                --transition:   all 0.22s cubic-bezier(.4,0,.2,1);
            }

            *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

            html { scroll-behavior: smooth; }

            body {
                font-family: var(--font);
                background: var(--bg-base);
                color: var(--text-primary);
                min-height: 100vh;
                line-height: 1.5;
            }

            /* Scrollbar */
            ::-webkit-scrollbar { width: 5px; height: 5px; }
            ::-webkit-scrollbar-track { background: var(--bg-surface); }
            ::-webkit-scrollbar-thumb { background: var(--teal); border-radius: 3px; }

            /* Layout */
            .layout { display: flex; min-height: 100vh; }

            /* Sidebar */
            .sidebar {
                width: 240px;
                min-height: 100vh;
                background: var(--bg-surface);
                border-right: 1px solid var(--border);
                padding: 28px 16px;
                display: flex;
                flex-direction: column;
                gap: 6px;
                flex-shrink: 0;
                position: sticky;
                top: 0;
                height: 100vh;
                overflow-y: auto;
            }

            .sidebar-logo {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 0 8px 28px;
                border-bottom: 1px solid var(--border);
                margin-bottom: 12px;
            }

            .sidebar-logo-icon {
                width: 36px; height: 36px;
                background: linear-gradient(135deg, var(--teal), var(--cyan));
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 18px;
            }

            .sidebar-logo-text {
                font-size: 13px;
                font-weight: 700;
                color: var(--text-primary);
                letter-spacing: 0.02em;
                line-height: 1.2;
            }

            .sidebar-logo-sub {
                font-size: 10px;
                color: var(--text-muted);
                font-weight: 400;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }

            .nav-section-label {
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: var(--text-muted);
                padding: 12px 8px 4px;
            }

            .nav-link {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 12px;
                border-radius: var(--radius-sm);
                text-decoration: none;
                font-size: 13px;
                font-weight: 500;
                color: var(--text-secondary);
                transition: var(--transition);
                cursor: pointer;
                border: none;
                background: transparent;
                width: 100%;
                text-align: left;
            }

            .nav-link:hover, .nav-link.active {
                background: rgba(6,182,212,0.08);
                color: var(--cyan);
            }

            .nav-link.active { border-left: 3px solid var(--cyan); padding-left: 9px; }

            .nav-link-icon { font-size: 16px; width: 20px; text-align: center; }

            .sidebar-status {
                margin-top: auto;
                padding-top: 16px;
                border-top: 1px solid var(--border);
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .status-dot {
                display: inline-block;
                width: 7px; height: 7px;
                border-radius: 50%;
                margin-right: 6px;
            }

            .status-dot.green  { background: var(--green); box-shadow: 0 0 6px var(--green); }
            .status-dot.red    { background: var(--red); }
            .status-dot.amber  { background: var(--amber); }

            .status-line {
                font-size: 11px;
                color: var(--text-secondary);
                display: flex;
                align-items: center;
            }

            /* Main Content */
            .main {
                flex: 1;
                padding: 28px 32px;
                overflow-x: hidden;
                min-width: 0;
            }

            /* Page Header */
            .page-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                margin-bottom: 32px;
                gap: 16px;
                flex-wrap: wrap;
            }

            .page-title { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em; }
            .page-subtitle { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

            .header-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

            .badge {
                display: inline-flex; align-items: center; gap: 5px;
                padding: 5px 12px; border-radius: 20px;
                font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
            }

            .badge-green  { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
            .badge-red    { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
            .badge-cyan   { background: rgba(6,182,212,0.12);  color: var(--cyan); border: 1px solid rgba(6,182,212,0.25); }
            .badge-amber  { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }

            /* Grid */
            .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
            .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin-bottom: 24px; }
            @media(max-width:1100px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

            /* Card */
            .card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 22px;
                transition: var(--transition);
            }

            .card:hover { border-color: var(--border-glow); box-shadow: var(--shadow-glow); }

            .card-title {
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: var(--cyan);
                margin-bottom: 18px;
                display: flex;
                align-items: cen
                gap: 8px;
                padding-bottom: 12px;
                border-bottom: 1px solid var(--border);
            }

            .card-title-icon { font-size: 15px; }

            /* Metric Cards */
            .metric-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 22px 24px;
                display: flex;
                align-items: center;
                gap: 18px;
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }

            .metric-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 2px;
                background: linear-gradient(90deg, var(--teal), var(--cyan));
            }

            .metric-card:hover { border-color: var(--border-glow); box-shadow: var(--shadow-glow); }

            .metric-icon {
                width: 48px; height: 48px;
                border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                font-size: 22px;
                flex-shrink: 0;
            }

            .metric-icon.teal   { background: rgba(13,148,136,0.15); }
            .metric-icon.cyan   { background: rgba(6,182,212,0.15); }
            .metric-icon.indigo { background: rgba(99,102,241,0.15); }

            .metric-value { font-size: 30px; font-weight: 800; color: var(--text-primary); line-height: 1; }
            .metric-label { font-size: 11px; color: var(--text-muted); font-weight: 500; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }

            /* Form Elements */
            .form-group { margin-bottom: 14px; }

            label {
                display: block;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                color: var(--text-secondary);
                margin-bottom: 6px;
            }

            input, select, textarea {
                width: 100%;
                padding: 10px 12px;
                background: var(--bg-surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                color: var(--text-primary);
                font-family: var(--font);
                font-size: 13px;
                transition: var(--transition);
                outline: none;
            }

            input::placeholder { color: var(--text-muted); }
            select option { background: var(--bg-surface); }

            input:focus, select:focus, textarea:focus {
                border-color: var(--cyan);
                box-shadow: 0 0 0 3px rgba(6,182,212,0.1);
            }

            /* Buttons */
            .btn {
                display: inline-flex; align-items: center; justify-content: center; gap: 7px;
                padding: 10px 20px;
                border: none; border-radius: var(--radius-sm);
                font-family: var(--font);
                font-size: 13px; font-weight: 600;
                cursor: pointer; transition: var(--transition);
                width: 100%;
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--teal) 0%, var(--cyan) 100%);
                color: #fff;
                box-shadow: 0 4px 14px rgba(6,182,212,0.25);
            }

            .btn-primary:hover { opacity: 0.88; transform: translateY(-1px); box-shadow: 0 6px 18px rgba(6,182,212,0.35); }

            .btn-secondary {
                background: rgba(6,182,212,0.08);
                color: var(--cyan);
                border: 1px solid var(--border-glow);
            }

            .btn-secondary:hover { background: rgba(6,182,212,0.15); }

            /* Alert / Info Box */
            .alert {
                padding: 12px 16px;
                border-radius: var(--radius-sm);
                font-size: 12px;
                margin-bottom: 14px;
                display: flex; align-items: flex-start; gap: 8px;
            }

            .alert-info    { background: rgba(6,182,212,0.06); border: 1px solid rgba(6,182,212,0.2); color: #a5f3fc; }
            .alert-success { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.25); color: #6ee7b7; }
            .alert-error   { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.25);  color: #fca5a5; }

            .message { padding: 12px 14px; border-radius: var(--radius-sm); margin-bottom: 12px; font-size: 12px; font-weight: 500; }
            .message.success { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: #6ee7b7; }
            .message.error   { background: rgba(239,68,68,0.1);  border: 1px solid rgba(239,68,68,0.3);  color: #fca5a5; }

            /* Device List */
            .device-list { max-height: 420px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }

            .device-item {
                background: var(--bg-surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 14px 16px;
                border-left: 3px solid var(--teal);
                transition: var(--transition);
                cursor: pointer;
            }

            .device-item:hover { border-color: var(--border-glow); border-left-color: var(--cyan); background: var(--bg-hover); }

            .device-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }

            .device-name {
                font-size: 13px; font-weight: 700; color: var(--text-primary);
                display: flex; align-items: center; gap: 6px;
            }

            .tag {
                display: inline-flex; align-items: center;
                padding: 2px 9px; border-radius: 20px;
                font-size: 10px; font-weight: 700; letter-spacing: 0.03em;
            }

            .tag-green  { background: rgba(16,185,129,0.12); color: #34d399; }
            .tag-red    { background: rgba(239,68,68,0.12);  color: #f87171; }
            .tag-cyan   { background: rgba(6,182,212,0.12);  color: var(--cyan); }
            .tag-amber  { background: rgba(245,158,11,0.12); color: #fbbf24; }

            .device-meta { font-size: 11px; color: var(--text-muted); margin-bottom: 2px; }

            .mono-block {
                background: rgba(0,0,0,0.3);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 8px 10px;
                font-family: var(--mono);
                font-size: 10px;
                color: var(--cyan-light);
                word-break: break-all;
                margin-top: 8px;
            }

            /* Encryption Display */
            .enc-block {
                background: rgba(0,0,0,0.3);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 10px 12px;
                font-family: var(--mono);
                font-size: 10px;
                color: #67e8f9;
                word-break: break-all;
                margin-bottom: 10px;
                line-height: 1.6;
            }

            .key-label {
                font-size: 11px; font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase; letter-spacing: 0.05em;
                margin-bottom: 6px;
            }

            /* Divider */
            .divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

            /* Pulse animation for live indicator */
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.4; }
            }
            .pulse { animation: pulse 2s ease-in-out infinite; }

            /* Section heading */
            .section-label {
                font-size: 10px; font-weight: 700;
                letter-spacing: 0.1em; text-transform: uppercase;
                color: var(--text-muted); margin-bottom: 14px;
                display: flex; align-items: center; gap: 8px;
            }
            .section-label::after {
                content: ''; flex: 1; height: 1px;
                background: var(--border);
            }

            /* Tooltip-style meta row */
            .meta-row { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
            .meta-row strong { color: var(--text-secondary); }

            /* Live badge */
            .live-badge {
                display: inline-flex; align-items: center; gap: 5px;
                font-size: 10px; font-weight: 700;
                color: var(--green); letter-spacing: 0.05em;
                text-transform: uppercase;
            }

            /* Footer strip */
            .top-bar {
                background: var(--bg-surface);
                border-bottom: 1px solid var(--border);
                padding: 10px 32px;
                display: flex; align-items: center; gap: 14px;
                font-size: 11px; color: var(--text-muted);
                flex-wrap: wrap;
            }
            .top-bar-item { display: flex; align-items: center; gap: 5px; }

        </style> </head> <body> <div class="layout"> <!--  SIDEBAR  --> <aside class="sidebar"> <div class="sidebar-logo"> <div class="sidebar-logo-icon">"</div> <div> <div class="sidebar-logo-text">IoMT Security</div> <div class="sidebar-logo-sub">Blockchain Platform</div> </div> </div> <div class="nav-section-label">Navigation</div> <div class="nav-link active"><span class="nav-link-icon"><i class="fa-solid fa-gauge-high"></i></span> Dashboard</div> <a class="nav-link" href="/decryption"><span class="nav-link-icon">""</span> Decryption Demo</a> <a class="nav-link" href="/admin"><span class="nav-link-icon"><i class="fa-solid fa-shield-halved"></i></span> Access Control</a> <div class="nav-section-label" style="margin-top:8px;">System Status</div> <div class="sidebar-status"> <div class="status-line"><span class="status-dot green"></span> MongoDB: Connected</div> <div class="status-line" id="sidebarGanache"><span class="status-dot amber pulse"></span> Ganache: Checking...</div> <div class="status-line"><span class="status-dot green"></span> Flask API: Online</div> </div> </aside> <!--  MAIN  --> <div style="flex:1;display:flex;flex-direction:column;min-width:0;"> <!-- Top Bar --> <div class="top-bar"> <div class="top-bar-item"> <span>"-</span> <span>Post-Quantum KEM (Kyber)</span> </div> <div class="top-bar-item" style="margin-left:auto;"> <span id="topBarGanache" class="badge badge-amber"><i class="fa-solid fa-circle-nodes"></i> Ganache</span> <span class="badge badge-green"><i class="fa-solid fa-database"></i> MongoDB</span> </div> </div> <div class="main"> <!-- Page Header --> <div class="page-header"> <div> <div class="page-title">IoMT Blockchain Dashboard</div> <div class="page-subtitle">Real-time IoT device management with post-quantum cryptography &amp; on-chain key registry</div> </div> <div class="live-badge"> <span class="status-dot green pulse"></span>LIVE
                    </div> </div> <!-- "" Metric Cards "" --> <div class="grid-3"> <div class="metric-card"> <div class="metric-icon teal">"</div> <div> <div class="metric-value" id="simulatedCount">0</div> <div class="metric-label">Simulated Devices</div> </div> </div> <div class="metric-card"> <div class="metric-icon cyan">"</div> <div> <div class="metric-value" id="registeredCount">0</div> <div class="metric-label">On-Chain Registered</div> </div> </div> <div class="metric-card"> <div class="metric-icon indigo">"</div> <div> <div class="metric-value" id="eventCount">0</div> <div class="metric-label">Audit Events</div> </div> </div> </div> <!-- "" Row 1 : Simulator + Registration | Encryption Details "" --> <div class="grid-2"> <!-- Left Column --> <div style="display:flex;flex-direction:column;gap:20px;"> <!-- Device Simulator --> <div class="card"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-microchip"></i></span> Device Simulator</div> <div id="simulatorMessage"></div> <div class="form-group"> <label>Device ID</label> <input type="text" id="deviceId" placeholder="e.g. BP_MON_001" value="BP_MON_001"> </div> <div class="form-group"> <label>Device Type</label> <select id="deviceType"> <option value="Blood Pressure Monitor">Blood Pressure Monitor</option> <option value="Glucose Meter">Glucose Meter</option> <option value="Pulse Oximeter">Pulse Oximeter</option> <option value="Temperature Sensor">Temperature Sensor</option> <option value="ECG Monitor">ECG Monitor</option> </select> </div> <button class="btn btn-secondary" onclick="createDevice()">+ Create Simulated Device</button> </div> <!-- Blockchain Registration --> <div class="card"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-cube"></i></span> Blockchain Registration</div> <div id="registrationMessage"></div> <div class="alert alert-info"> <span></span> <span>Registers PQ keys to <strong>Ganache blockchain</strong> AND <strong>MongoDB</strong> simultaneously.</span> </div> <div class="form-group"> <label>Select Device</label> <select id="deviceSelect"><option value="">-- Select a device --</option></select> </div> <button class="btn btn-primary" onclick="registerToBlockchain()"><i class="fa-solid fa-cube"></i> Register to Blockchain & DB</button> </div> </div> <!-- Right: Encryption Details --> <div class="card" style="display:flex;flex-direction:column;"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-lock"></i></span> Encryption &amp; Key Details</div> <div id="encryptionDisplay"> <div class="alert alert-info"> <span></span> <span>Select a registered device below to inspect its post-quantum keys and blockchain record.</span> </div> </div> <div style="margin-top:auto;padding-top:16px;"> <label>Inspect Device Keys</label> <select id="encryptionDeviceSelect" onchange="viewEncryption()"> <option value="">-- Select a device --</option> </select> </div> </div> </div> <!-- "" Row 2 : Stored Devices | Audit Log "" --> <div class="section-label" style="margin-top:8px;">Registered Devices &amp; Events</div> <div class="grid-2"> <div class="card"> <div class="card-title"><span class="card-title-icon"></span> Devices " MongoDB + Blockchain</div> <div class="device-list" id="storedDevicesList"> <div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No devices registered yet</div> </div> </div> <div class="card"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-clipboard-list"></i></span> Authentication Events</div> <div class="device-list" id="auditEventsList"> <div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No events yet</div> </div> </div> </div> <!-- "" Row 3 : ESP Devices | Live Packets "" --> <div class="section-label">Live ESP Device Feed</div> <div class="grid-2"> <div class="card"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-wifi"></i></span> Connected ESP Devices</div> <div class="device-list" id="espDevicesList"> <div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No ESP devices connected yet</div> </div> </div> <div class="card"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-envelope-open-text"></i></span> Latest Packets &amp; Hashes</div> <div class="device-list" id="espPacketsList"> <div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No packets received yet</div> </div> </div> </div> <!-- Device Detail Expand Panel --> <div class="card" style="margin-top:4px;"> <div class="card-title"><span class="card-title-icon"><i class="fa-solid fa-magnifying-glass"></i></span> Device Detail Viewer</div> <div id="deviceDetailsPanel" style="color:var(--text-muted);font-size:13px;text-align:center;padding:24px 0;"> Click any device card above to view full encryption keys and blockchain proof.
                    </div> </div> </div><!-- /main --> </div><!-- /flex-col --> </div><!-- /layout --> <script> let simulatedDevices = {};

        function checkGanacheStatus() {
            fetch('/api/ganache-status')
                .then(r => r.json())
                .then(data => {
                    const topBadge = document.getElementById('topBarGanache');
                    const sideEl   = document.getElementById('sidebarGanache');
                    if (data.connected) {
                        topBadge.className = 'badge badge-green';
                        topBadge.textContent = ' Ganache: Chain ' + data.chain_id;
                        sideEl.innerHTML = '<span class="status-dot green"></span> Ganache: Chain ' + data.chain_id;
                    } else {
                        topBadge.className = 'badge badge-red';
                        topBadge.textContent = ' Ganache: Offline';
                        sideEl.innerHTML = '<span class="status-dot red"></span> Ganache: Offline';
                    }
                });
        }

        function createDevice() {
            const deviceId   = document.getElementById('deviceId').value.trim();
            const deviceType = document.getElementById('deviceType').value;
            if (!deviceId) { showMessage('simulatorMessage','Device ID is required','error'); return; }
            fetch('/api/create-device', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({device_id: deviceId, device_type: deviceType, manufacturer: 'MedCorp'})
            }).then(r=>r.json()).then(data => {
                if (data.success) {
                    simulatedDevices[deviceId] = data.device;
                    showMessage('simulatorMessage', 'Device "' + deviceId + '" simulated!', 'success');
                    updateDeviceSelects();
                    updateMetrics();
                    document.getElementById('deviceId').value = '';
                } else { showMessage('simulatorMessage', data.error, 'error'); }
            });
        }

        function registerToBlockchain() {
            const deviceId = document.getElementById('deviceSelect').value;
            if (!deviceId) { showMessage('registrationMessage','Please select a device','error'); return; }
            showMessage('registrationMessage', ' Registering to Ganache and MongoDB', 'success');
            fetch('/api/register-blockchain', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({device_id: deviceId, gateway_id: 'GATEWAY_HUB_001'})
            }).then(r=>r.json()).then(data => {
                if (data.success) {
                    showMessage('registrationMessage',
                        'On-chain! TX: ' + data.blockchain_tx.substring(0,20) + ' Block #' + data.block_number,
                        'success');
                    updateStoredDevices(); updateMetrics(); viewEncryptionDetails(deviceId);
                } else { showMessage('registrationMessage', '- ' + data.error, 'error'); }
            });
        }

        function viewEncryption() {
            const deviceId = document.getElementById('encryptionDeviceSelect').value;
            if (deviceId) viewEncryptionDetails(deviceId);
        }

        function viewEncryptionDetails(deviceId) {
            fetch('/api/encryption-details/' + deviceId).then(r=>r.json()).then(data => {
                if (data.error) {
                    document.getElementById('encryptionDisplay').innerHTML =
                        '<div class="alert alert-error"><span>-</span><span>Device not found.</span></div>';
                    return;
                }
                const statusTag = data.is_active
                    ? '<span class="tag tag-green"><i class="fa-solid fa-circle-check"></i> ACTIVE</span>'
                    : '<span class="tag tag-red"><i class="fa-solid fa-circle-xmark"></i> INACTIVE</span>';
                document.getElementById('encryptionDisplay').innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:12px;"> <div style="display:flex;justify-content:space-between;align-items:center;"> <span style="font-size:13px;font-weight:700;color:var(--text-primary);">${data.device_id}</span> ${statusTag}
                        </div> <hr class="divider" style="margin:4px 0;"> <div> <div class="key-label">"' Kyber Public Key</div> <div class="enc-block">${data.public_key_full}</div> </div> <div> <div class="key-label">"' KEM Shared Secret</div> <div class="enc-block">${data.shared_secret_full}</div> </div> <div> <div class="key-label"> Protocol</div> <div style="font-size:12px;color:var(--text-secondary);">${data.key_exchange_protocol} . ${data.encryption_algorithm}</div> </div> <div> <div class="key-label"><i class="fa-solid fa-cube"></i> Blockchain Proof</div> <div class="mono-block">TX: ${data.blockchain_tx || 'N/A'}<br>Block: ${data.blockchain_block || 'N/A'}</div> </div> </div>`;
            });
        }

        function updateDeviceSelects() {
            const opts = Object.keys(simulatedDevices).map(id => `<option value="${id}">${id}</option>`).join('');
            document.getElementById('deviceSelect').innerHTML           = '<option value="">-- Select a device --</option>' + opts;
            document.getElementById('encryptionDeviceSelect').innerHTML = '<option value="">-- Select a device --</option>' + opts;
        }

        function showDeviceDetails(deviceId) {
            fetch('/api/encryption-details/' + deviceId).then(r=>r.json()).then(data => {
                if (data.error) { return; }
                document.getElementById('deviceDetailsPanel').innerHTML = `
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;text-align:left;"> <div> <div class="key-label">Device Info</div> <div class="meta-row"><strong>ID:</strong> ${data.device_id}</div> <div class="meta-row"><strong>Status:</strong> ${data.is_active ? '<span class="tag tag-green">Active</span>' : '<span class="tag tag-red">Inactive</span>'}</div> <div class="meta-row"><strong>Gateway:</strong> ${data.gateway_id}</div> <div class="meta-row"><strong>Auth At:</strong> ${data.authenticated_at || 'N/A'}</div> <div class="meta-row"><strong>Protocol:</strong> ${data.key_exchange_protocol}</div> <div class="meta-row"><strong>Algorithm:</strong> ${data.encryption_algorithm}</div> </div> <div> <div class="key-label">Blockchain Proof</div> <div class="mono-block">TX: ${data.blockchain_tx || 'N/A'}<br>Block: ${data.blockchain_block || 'N/A'}</div> <div class="key-label" style="margin-top:12px;">Kyber Public Key</div> <div class="enc-block">${(data.public_key_full||'').substring(0,80)}</div> <div class="key-label">Shared Secret</div> <div class="enc-block">${(data.shared_secret_full||'').substring(0,80)}</div> </div> </div>`;
            });
        }

        function updateStoredDevices() {
            fetch('/api/stored-devices').then(r=>r.json()).then(devices => {
                // Always refresh encryptionDeviceSelect with registered devices
                const encSel = document.getElementById('encryptionDeviceSelect');
                const prevVal = encSel.value;
                if (devices.length) {
                    encSel.innerHTML = '<option value="">-- Select a device --</option>' +
                        devices.map(d => `<option value="${d.device_id}">${d.device_id}</option>`).join('');
                    if (prevVal) encSel.value = prevVal;
                } else {
                    encSel.innerHTML = '<option value="">-- No registered devices --</option>';
                }

                if (!devices.length) {
                    document.getElementById('storedDevicesList').innerHTML =
                        '<div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No devices registered yet</div>';
                    return;
                }
                document.getElementById('storedDevicesList').innerHTML = devices.map(d => `
                    <div class="device-item" onclick="showDeviceDetails('${d.device_id}')"> <div class="device-header"> <div class="device-name"> ${d.device_id}</div> <span class="tag tag-green"><i class="fa-solid fa-circle-check"></i> Registered</span> </div> <div class="meta-row"><strong>Gateway:</strong> ${d.gateway_id}</div> <div class="meta-row"><strong>Key:</strong> <span style="font-family:var(--mono);font-size:10px;">${d.public_key_preview}</span></div> <div class="mono-block">TX: ${d.blockchain_tx}<br>Block: ${d.blockchain_block}</div> <div style="font-size:10px;color:var(--cyan);margin-top:8px;">' Click for full details</div> </div>`).join('');
            });
        }

        function updateAuditEvents() {
            fetch('/api/audit-events').then(r=>r.json()).then(events => {
                if (!events.length) {
                    document.getElementById('auditEventsList').innerHTML =
                        '<div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No events yet</div>';
                    return;
                }
                const typeColors = {
                    'AUTHENTICATED': 'tag-green', 'SENSOR_READING': 'tag-cyan',
                    'ACCESS_GRANTED': 'tag-cyan', 'ACCESS_REVOKED': 'tag-amber',
                    'PROVIDER_REGISTERED': 'tag-green', 'PROVIDER_REVOKED': 'tag-red',
                    'DEVICE_ASSIGNED': 'tag-cyan'
                };
                document.getElementById('auditEventsList').innerHTML = events.slice(0,20).map(e => {
                    const cls = typeColors[e.event_type] || 'tag-amber';
                    return `<div class="device-item" style="cursor:default;"> <div class="device-header"> <span class="tag ${cls}">${e.event_type}</span> <span style="font-size:10px;color:var(--text-muted);">${new Date(e.timestamp).toLocaleTimeString()}</span> </div> <div class="meta-row"><strong>Device:</strong> ${e.device_id}</div> </div>`;
                }).join('');
            });
        }

        function updateESPDevices() {
            fetch('/api/esp-devices').then(r=>r.json()).then(devices => {
                if (!Array.isArray(devices) || !devices.length) {
                    document.getElementById('espDevicesList').innerHTML =
                        '<div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No ESP devices connected yet</div>';
                    return;
                }
                document.getElementById('espDevicesList').innerHTML = devices.map(d => {
                    const nowMs      = Date.now();
                    const lastSeenMs = d.last_seen ? new Date(d.last_seen).getTime() : 0;
                    const isStale    = !lastSeenMs || (nowMs - lastSeenMs) > 30000;
                    const connected  = d.connection_status === 'CONNECTED' && !isStale;
                    const statusTxt  = connected ? 'CONNECTED' : 'DISCONNECTED';
                    const lastSeen   = d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : 'Never';
                    const ageSec     = lastSeenMs ? Math.round((nowMs - lastSeenMs) / 1000) : null;
                    const ageStr     = ageSec !== null ? ` (${ageSec}s ago)` : '';
                    return `<div class="device-item" style="border-left-color:${connected?'var(--green)':'var(--red)'};">
                        <div class="device-header">
                            <div class="device-name">&#x1F4F6; ${d.device_id}</div>
                            <span class="tag ${connected?'tag-green':'tag-red'}">${statusTxt}</span>
                        </div>
                        <div class="meta-row"><strong>Last Seen:</strong> ${lastSeen}${ageStr}</div>
                        ${d.last_packet ? `<div class="mono-block">Sensor: ${d.last_packet.sensor_type}<br>Reading: ${d.last_packet.reading_value}</div>` : ''}
                    </div>`;
                }).join('');
            }).catch(()=>{});
        }

        function updateESPPackets() {
            fetch('/api/esp-devices').then(r=>r.json()).then(devices => {
                const packets = (Array.isArray(devices) ? devices : []).filter(d=>d.last_packet);
                if (!packets.length) {
                    document.getElementById('espPacketsList').innerHTML =
                        '<div style="padding:24px;text-align:center;color:var(--text-muted);font-size:12px;">No packets received yet</div>';
                    return;
                }
                document.getElementById('espPacketsList').innerHTML = packets.slice(0,10).map(d => `
                    <div class="device-item" style="cursor:default;"> <div class="device-name" style="margin-bottom:8px;">" ${d.device_id}</div> <div class="mono-block"> Hash: ${d.last_packet.hash ? d.last_packet.hash.substring(0,40)+'' : 'N/A'}<br> Payload: ${d.last_packet.encrypted_payload || 'N/A'}<br> Time: ${d.last_packet.timestamp || 'N/A'}
                        </div> </div>`).join('');
            }).catch(()=>{});
        }

        function updateMetrics() {
            document.getElementById('simulatedCount').textContent = Object.keys(simulatedDevices).length;
            fetch('/api/metrics').then(r=>r.json()).then(data => {
                document.getElementById('registeredCount').textContent = data.registered_count;
                document.getElementById('eventCount').textContent      = data.event_count;
            });
        }

        function showMessage(elementId, message, type) {
            const el = document.getElementById(elementId);
            el.innerHTML = `<div class="message ${type}">${message}</div>`;
            setTimeout(() => el.innerHTML = '', 6000);
        }

        // Init
        checkGanacheStatus();
        updateStoredDevices();
        updateAuditEvents();
        updateESPDevices();
        updateESPPackets();
        updateMetrics();
        setInterval(() => {
            checkGanacheStatus();
            updateStoredDevices();
            updateAuditEvents();
            updateESPDevices();
            updateESPPackets();
            updateMetrics();
        }, 10000);
    </script> </body> </html> """

    ADMIN_HTML = """
    <!DOCTYPE html> <html> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Admin " Access Control</title> <style> * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: #e0e0e0;
                min-height: 100vh;
                padding: 24px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            header {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 24px;
                border-radius: 12px;
                margin-bottom: 24px;
            }
            h1 { color: #e94560; font-size: 28px; margin-bottom: 8px; }
            .badge {
                display: inline-block; padding: 6px 14px; border-radius: 20px;
                font-size: 12px; font-weight: 600; margin: 4px;
            }
            .badge-admin  { background: #e94560; color: #fff; }
            .badge-ok     { background: #28a745; color: #fff; }
            .badge-warn   { background: #ffc107; color: #000; }
            .badge-info   { background: #17a2b8; color: #fff; }
            .nav { margin-top: 12px; }
            .nav a { color: #e94560; text-decoration: none; font-weight: 600; margin-right: 18px; }

            .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
            .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin-bottom: 24px; }
            @media(max-width:900px){ .grid-2,.grid-3 { grid-template-columns: 1fr; } }

            .panel {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 22px;
            }
            .panel-title {
                font-size: 16px; font-weight: 700; color: #e94560;
                border-bottom: 2px solid #e94560; padding-bottom: 10px; margin-bottom: 16px;
            }
            label { display: block; margin-bottom: 5px; font-size: 13px; color: #aaa; }
            input, select {
                width: 100%; padding: 10px; border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.15);
                background: rgba(255,255,255,0.07);
                color: #e0e0e0; font-size: 13px; margin-bottom: 12px;
            }
            input::placeholder { color: #666; }
            .btn {
                width: 100%; padding: 11px; border: none; border-radius: 6px;
                font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .2s;
            }
            .btn:hover { opacity: .85; }
            .btn-red    { background: #e94560; color: #fff; }
            .btn-green  { background: #28a745; color: #fff; }
            .btn-blue   { background: #0066cc; color: #fff; }
            .btn-orange { background: #fd7e14; color: #fff; }
            .btn-sm {
                padding: 5px 14px; font-size: 11px; font-weight: 600;
                border: none; border-radius: 4px; cursor: pointer;
            }
            .msg { padding: 10px; border-radius: 6px; font-size: 13px; margin-bottom: 10px; display: none; }
            .msg.show { display: block; }
            .msg.ok   { background: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32; }
            .msg.err  { background: #7f0000; color: #ffcdd2; border: 1px solid #b71c1c; }
            .provider-item {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; padding: 14px; margin-bottom: 10px;
            }
            .provider-addr { font-family: monospace; font-size: 11px; color: #aaa; word-break: break-all; }
            .provider-name { font-weight: 700; font-size: 14px; color: #e0e0e0; }
            .provider-role { font-size: 12px; color: #e94560; font-weight: 600; }
            .access-log { max-height: 320px; overflow-y: auto; }
            .log-item { padding: 10px; border-radius: 6px; margin-bottom: 8px; background: rgba(255,255,255,0.04); font-size: 12px; }
            .log-time { color: #aaa; margin-bottom: 3px; }
            .log-type { font-weight: 700; }
            .log-PROVIDER_REGISTERED { color: #28a745; }
            .log-PROVIDER_REVOKED    { color: #e94560; }
            .log-ACCESS_GRANTED      { color: #17a2b8; }
            .log-ACCESS_REVOKED      { color: #fd7e14; }
            .log-DEVICE_ASSIGNED     { color: #a855f7; }
            .admin-addr { font-family: monospace; font-size: 12px; color: #e94560; word-break: break-all; }
            .access-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
            .access-row input { margin-bottom: 0; flex: 1; min-width: 120px; }
        </style> </head> <body> <div class="container"> <header> <h1> Admin " Healthcare Access Control</h1> <p style="color:#aaa; margin-bottom:10px;"> Manage which doctors and healthcare providers can access patient IoMT device data.
                Every action is recorded as an immutable transaction on the blockchain.
            </p> <span class="badge badge-admin">ADMIN PANEL</span> <span class="badge badge-info" id="adminAddr">Loading...</span> <span class="badge badge-ok" id="blockchainBadge">Blockchain...</span> <div class="nav"> <a href="/"> Main Dashboard</a> <a href="/decryption">Decryption Demo</a> </div> </header> <!-- Stats row --> <div class="grid-3"> <div class="panel" style="text-align:center;"> <div style="font-size:28px;font-weight:700;color:#e94560;" id="statProviders">"</div> <div style="font-size:12px;color:#aaa;">Registered Providers</div> </div> <div class="panel" style="text-align:center;"> <div style="font-size:28px;font-weight:700;color:#28a745;" id="statActive">"</div> <div style="font-size:12px;color:#aaa;">Active Providers</div> </div> <div class="panel" style="text-align:center;"> <div style="font-size:28px;font-weight:700;color:#17a2b8;" id="statRevoked">"</div> <div style="font-size:12px;color:#aaa;">Revoked Providers</div> </div> </div> <div class="grid-2"> <!-- Register Provider --> <div class="panel"> <div class="panel-title"><i class="fa-solid fa-user-doctor"></i> Register Healthcare Provider</div> <div class="msg" id="regMsg"></div> <label>Wallet Address (0x...)</label> <input id="regAddr" placeholder="0xProviderEthereumAddress"> <label>Full Name</label> <input id="regName" placeholder="Dr. Jane Smith"> <label>Role</label> <select id="regRole"> <option value="DOCTOR">Doctor</option> <option value="NURSE">Nurse</option> <option value="RADIOLOGIST">Radiologist</option> <option value="PHARMACIST">Pharmacist</option> <option value="ADMIN_STAFF">Admin Staff</option> <option value="RESEARCHER">Researcher</option> </select> <button class="btn btn-green" onclick="registerProvider()"><i class="fa-solid fa-plus"></i> Register Provider</button> </div> <!-- Assign Device to Patient --> <div class="panel"> <div class="panel-title"><i class="fa-solid fa-link"></i> Assign Device to Patient</div> <div class="msg" id="assignMsg"></div> <label>Device ID</label> <select id="assignDevice"> <option value="">-- Select device --</option> </select> <label>Patient ID</label> <input id="assignPatient" placeholder="e.g. PATIENT_001"> <button class="btn btn-blue" onclick="assignDevice()"><i class="fa-solid fa-link"></i> Assign Device</button> <div style="margin-top:14px; font-size:12px; color:#aaa;"> A device must be assigned to a patient before any provider can be granted access to it.
                </div> </div> </div> <!-- Sync MongoDB Devices to Blockchain --> <div class="panel" style="margin-bottom:24px;border-left:4px solid #f39c12;"> <div class="panel-title"><i class="fa-solid fa-rotate"></i> Sync MongoDB Devices -> Blockchain</div> <div style="font-size:12px;color:#aaa;margin-bottom:14px;"> Registers every active device stored in MongoDB onto the blockchain contract.
                Devices already on-chain are skipped automatically.
            </div> <div class="msg" id="syncMsg"></div> <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;"> <button class="btn btn-orange" style="width:auto;padding:10px 24px;" onclick="syncDevices()"> <i class="fa-solid fa-rotate"></i> Sync All Devices to Blockchain
                </button> <span id="syncStatus" style="font-size:13px;color:#aaa;"></span> </div> <div id="syncResults" style="margin-top:16px;max-height:260px;overflow-y:auto;display:none;"></div> </div> <!-- Grant / Revoke Access --> <div class="panel" style="margin-bottom:24px;"> <div class="panel-title"><i class="fa-solid fa-key"></i> Grant / Revoke Patient Access</div> <div class="msg" id="accessMsg"></div> <div style="display:grid;grid-template-columns:1fr 1fr auto auto;gap:12px;align-items:end;"> <div> <label>Provider Wallet Address</label> <input id="accessAddr" placeholder="0xProviderAddress" style="margin-bottom:0"> </div> <div> <label>Patient ID</label> <input id="accessPatient" placeholder="PATIENT_001" style="margin-bottom:0"> </div> <div> <button class="btn btn-green" style="width:auto;padding:10px 20px;" onclick="grantAccess()"><i class="fa-solid fa-check"></i> Grant Access</button> </div> <div> <button class="btn btn-red" style="width:auto;padding:10px 20px;" onclick="revokeAccess()"><i class="fa-solid fa-ban"></i> Revoke Access</button> </div> </div> <div style="margin-top:14px;"> <label style="margin-bottom:6px;">Quick Access Check</label> <div style="display:flex;gap:10px;align-items:center;"> <input id="checkAddr"    placeholder="Provider address" style="margin-bottom:0;flex:1"> <input id="checkPatient" placeholder="Patient ID"       style="margin-bottom:0;flex:1"> <button class="btn btn-orange" style="width:auto;padding:10px 20px;" onclick="checkAccess()"><i class="fa-solid fa-magnifying-glass"></i> Check</button> </div> <div id="checkResult" style="margin-top:10px;font-size:13px;display:none;padding:10px;border-radius:6px;"></div> </div> </div> <div class="grid-2"> <!-- Provider List --> <div class="panel"> <div class="panel-title"><i class="fa-solid fa-users-gear"></i> Registered Providers
                    <button class="btn-sm btn-blue" style="float:right;" onclick="loadProviders()"><i class="fa-solid fa-arrows-rotate"></i> Refresh</button> </div> <div id="providerList" style="max-height:460px;overflow-y:auto;"> <p style="color:#555;text-align:center;padding:20px;">Loading...</p> </div> </div> <!-- Audit Log --> <div class="panel"> <div class="panel-title"><i class="fa-solid fa-scroll"></i> Access Control Audit Log
                    <button class="btn-sm btn-blue" style="float:right;" onclick="loadAudit()"><i class="fa-solid fa-arrows-rotate"></i> Refresh</button> </div> <div class="access-log" id="auditLog"> <p style="color:#555;text-align:center;padding:20px;">Loading...</p> </div> </div> </div> </div> <script> const ACCESS_EVENTS = ['PROVIDER_REGISTERED','PROVIDER_REVOKED','ACCESS_GRANTED','ACCESS_REVOKED','DEVICE_ASSIGNED'];

    function showMsg(id, text, ok) {
        const el = document.getElementById(id);
        el.textContent = text;
        el.className = 'msg show ' + (ok ? 'ok' : 'err');
        setTimeout(() => { el.className = 'msg'; }, 6000);
    }

    async function post(url, body) {
        const r = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        return r.json();
    }

    async function loadAdminInfo() {
        try {
            const r = await fetch('/api/admin/providers');
            const d = await r.json();
            if (d.admin) {
                document.getElementById('adminAddr').textContent = 'Admin: ' + d.admin.substring(0,16) + '...';
            }
            document.getElementById('blockchainBadge').textContent = 'Blockchain Connected';
        } catch(e) {
            document.getElementById('blockchainBadge').textContent = 'Blockchain Error';
            document.getElementById('blockchainBadge').style.background = '#e94560';
        }
    }

    async function loadProviders() {
        const r = await fetch('/api/admin/providers');
        const d = await r.json();
        const list = d.providers || [];
        const total   = list.length;
        const active  = list.filter(p => p.is_registered).length;
        const revoked = total - active;
        document.getElementById('statProviders').textContent = total;
        document.getElementById('statActive').textContent   = active;
        document.getElementById('statRevoked').textContent  = revoked;

        if (!list.length) {
            document.getElementById('providerList').innerHTML =
                '<p style="color:#555;text-align:center;padding:20px;">No providers registered yet.</p>';
            return;
        }
        document.getElementById('providerList').innerHTML = list.map(p => `
            <div class="provider-item" style="border-left: 4px solid ${p.is_registered ? '#28a745' : '#e94560'};"> <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"> <span class="provider-name">${p.name || 'Unknown'}</span> <span class="badge ${p.is_registered ? 'badge-ok' : 'badge-warn'}" style="font-size:10px;"> ${p.is_registered ? 'ACTIVE' : '- REVOKED'}
                    </span> </div> <div class="provider-role">${p.role || ''}</div> <div class="provider-addr" style="margin-top:6px;">${p.address}</div> <div style="font-size:11px;color:#666;margin-top:4px;">Since: ${p.registered_at || 'N/A'}</div> ${p.is_registered ? `
                <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;"> <button class="btn-sm btn-red"
                        onclick="revokeProviderAddr('${p.address}')"> Revoke Provider</button> </div>` : ''}
            </div> `).join('');
    }

    async function loadAudit() {
        const r = await fetch('/api/audit-events');
        const events = await r.json();
        const filtered = events.filter(e => ACCESS_EVENTS.includes(e.event_type));
        if (!filtered.length) {
            document.getElementById('auditLog').innerHTML =
                '<p style="color:#555;text-align:center;padding:20px;">No access control events yet.</p>';
            return;
        }
        document.getElementById('auditLog').innerHTML = filtered.slice(0, 40).map(e => `
            <div class="log-item"> <div class="log-time">${new Date(e.timestamp).toLocaleString()}</div> <div class="log-type log-${e.event_type}">${e.event_type}</div> <div style="color:#ccc;margin-top:3px;">${e.message}</div> ${e.metadata && e.metadata.tx_hash ? `<div style="font-family:monospace;font-size:10px;color:#555;margin-top:3px;">TX: ${e.metadata.tx_hash.substring(0,32)}...</div>` : ''}
            </div> `).join('');
    }

    async function loadDeviceList() {
        try {
            const r = await fetch('/api/stored-devices');
            const devices = await r.json();
            const sel = document.getElementById('assignDevice');
            if (!devices.length) {
                sel.innerHTML = '<option value="">No registered devices</option>';
                return;
            }
            sel.innerHTML = '<option value="">-- Select device --</option>' +
                devices.map(d => `<option value="${d.device_id}">${d.device_id}</option>`).join('');
        } catch(e) {}
    }

    async function registerProvider() {
        const addr = document.getElementById('regAddr').value.trim();
        const name = document.getElementById('regName').value.trim();
        const role = document.getElementById('regRole').value;
        if (!addr || !name) { showMsg('regMsg','Address and name required',false); return; }
        const d = await post('/api/admin/register-provider', {address: addr, name, role});
        if (d.success) {
            showMsg('regMsg', `... Provider "${name}" registered. TX: ${d.tx_hash ? d.tx_hash.substring(0,20)+'...' : 'N/A'}`, true);
            document.getElementById('regAddr').value = '';
            document.getElementById('regName').value = '';
            loadProviders();
        } else {
            showMsg('regMsg', ' ' + (d.error || 'Unknown error'), false);
        }
    }

    async function revokeProviderAddr(addr) {
        if (!confirm('Revoke this provider? Their access to ALL patients will be denied immediately.')) return;
        const d = await post('/api/admin/revoke-provider', {address: addr});
        if (d.success) {
            loadProviders();
            loadAudit();
        } else {
            alert('Error: ' + (d.error || 'Unknown'));
        }
    }

    async function assignDevice() {
        const device_id  = document.getElementById('assignDevice').value.trim();
        const patient_id = document.getElementById('assignPatient').value.trim();
        if (!device_id || !patient_id) { showMsg('assignMsg','Device and patient ID required',false); return; }
        const d = await post('/api/admin/assign-device', {device_id, patient_id});
        if (d.success) {
            showMsg('assignMsg', `... Device "${device_id}" assigned to patient "${patient_id}"`, true);
            loadAudit();
        } else {
            showMsg('assignMsg', ' ' + (d.error || 'Unknown error'), false);
        }
    }

    async function grantAccess() {
        const address    = document.getElementById('accessAddr').value.trim();
        const patient_id = document.getElementById('accessPatient').value.trim();
        if (!address || !patient_id) { showMsg('accessMsg','Address and patient ID required',false); return; }
        const d = await post('/api/admin/grant-access', {address, patient_id});
        if (d.success) {
            showMsg('accessMsg', `... Access GRANTED to ${address.substring(0,16)}... for patient ${patient_id}`, true);
            loadAudit();
        } else {
            showMsg('accessMsg', ' ' + (d.error || 'Unknown error'), false);
        }
    }

    async function revokeAccess() {
        const address    = document.getElementById('accessAddr').value.trim();
        const patient_id = document.getElementById('accessPatient').value.trim();
        if (!address || !patient_id) { showMsg('accessMsg','Address and patient ID required',false); return; }
        if (!confirm(`Revoke access for ${address.substring(0,16)}... to patient ${patient_id}?`)) return;
        const d = await post('/api/admin/revoke-access', {address, patient_id});
        if (d.success) {
            showMsg('accessMsg', ` Access REVOKED for patient ${patient_id}`, true);
            loadAudit();
        } else {
            showMsg('accessMsg', ' ' + (d.error || 'Unknown error'), false);
        }
    }

    async function checkAccess() {
        const address    = document.getElementById('checkAddr').value.trim();
        const patient_id = document.getElementById('checkPatient').value.trim();
        if (!address || !patient_id) return;
        const r = await fetch(`/api/admin/check-access?address=${encodeURIComponent(address)}&patient_id=${encodeURIComponent(patient_id)}`);
        const d = await r.json();
        const box = document.getElementById('checkResult');
        box.style.display = 'block';
        if (d.has_access) {
            box.style.background = '#1b5e20'; box.style.color = '#a5d6a7';
            box.style.border = '1px solid #2e7d32';
            box.innerHTML = `... <strong>ACCESS GRANTED</strong> " ${d.provider.name || address} (${d.provider.role || 'N/A'}) can access patient <strong>${patient_id}</strong> data`;
        } else {
            box.style.background = '#7f0000'; box.style.color = '#ffcdd2';
            box.style.border = '1px solid #b71c1c';
            const reason = !d.provider.is_registered ? ' (provider not registered or revoked)' : ' (access not granted for this patient)';
            box.innerHTML = ` <strong>ACCESS DENIED</strong> " ${d.provider.name || address}${reason}`;
        }
    }

    // Init
    loadAdminInfo();
    loadProviders();
    loadAudit();
    loadDeviceList();
    setInterval(() => { loadProviders(); loadAudit(); }, 15000);

    async function syncDevices() {
        const btn = document.querySelector('[onclick="syncDevices()"]');
        const statusEl = document.getElementById('syncStatus');
        const resultsEl = document.getElementById('syncResults');
        const msgEl = document.getElementById('syncMsg');
        btn.disabled = true;
        btn.textContent = ' Syncing...';
        statusEl.textContent = 'Fetching device list...';
        resultsEl.style.display = 'none';
        try {
            const r = await fetch('/api/admin/sync-blockchain', {method: 'POST'});
            const d = await r.json();
            btn.disabled = false;
            btn.textContent = 'Sync All Devices to Blockchain';
            if (d.success) {
                const total   = d.total || 0;
                const synced  = d.synced || 0;
                const skipped = d.skipped || 0;
                const failed  = d.failed || 0;
                const summary = `Done: ${synced} registered, ${skipped} already on-chain, ${failed} failed (of ${total} total)`;
                statusEl.textContent = summary;
                msgEl.textContent = (failed === 0 ? ' ' : ' ') + summary;
                msgEl.className = 'msg show ' + (failed === 0 ? 'ok' : 'err');
                setTimeout(() => { msgEl.className = 'msg'; }, 8000);
                if (d.results && d.results.length) {
                    resultsEl.style.display = 'block';
                    resultsEl.innerHTML = '<table style="width:100%;border-collapse:collapse;font-size:12px;">'
                        + '<thead><tr style="color:#aaa;border-bottom:1px solid #2a3a4a;">'  
                        + '<th style="text-align:left;padding:6px;">Device ID</th>'
                        + '<th style="padding:6px;">Status</th>'
                        + '<th style="text-align:left;padding:6px;">TX Hash / Note</th></tr></thead><tbody>'
                        + d.results.map(r => `
                            <tr style="border-bottom:1px solid #1e2a38;"> <td style="padding:6px;font-family:monospace;">${r.device_id}</td> <td style="padding:6px;text-align:center;"> <span style="padding:2px 8px;border-radius:4px;
                                        background:${r.status==='registered'?'#1b5e20':r.status==='skipped'?'#1a3a5c':'#5c1a1a'};
                                        color:${r.status==='registered'?'#a5d6a7':r.status==='skipped'?'#90caf9':'#ef9a9a'}"> ${r.status.toUpperCase()}
                                    </span> </td> <td style="padding:6px;font-family:monospace;font-size:11px;color:#aaa;"> ${r.tx_hash ? r.tx_hash.substring(0,26)+'...' : (r.error || '-')}
                                </td> </tr>`).join('')
                        + '</tbody></table>';
                }
                loadDeviceList();
            } else {
                const errMsg = ' Error: ' + (d.error || 'Unknown');
                statusEl.textContent = errMsg;
                msgEl.textContent = errMsg;
                msgEl.className = 'msg show err';
                setTimeout(() => { msgEl.className = 'msg'; }, 8000);
            }
        } catch(e) {
            btn.disabled = false;
            btn.textContent = 'Sync All Devices to Blockchain';
            statusEl.textContent = 'Request failed: ' + e.message;
        }
    }
    </script> </body> </html> """

    # ========== API ENDPOINTS ==========
    
    @app.route('/api/ganache-status', methods=['GET'])
    def ganache_status():
        """Get Ganache connection status — live check with auto-reconnect"""
        # Always do a live check
        if blockchain.w3 and blockchain.w3.is_connected():
            blockchain.connected = True
        else:
            # Try to reconnect
            blockchain.connected = False
            blockchain.connect_to_ganache()
        return jsonify({
            "connected": blockchain.connected,
            "chain_id": blockchain.w3.eth.chain_id if (blockchain.w3 and blockchain.connected) else None,
            "message": "Connected" if blockchain.connected else "Not connected to Ganache — start Ganache on port 7545 or 8545"
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
    
    @app.route('/api/device-sensor-reading/<device_id>', methods=['POST'])
    def device_sensor_reading(device_id):
        """Simulate IoT device generating and encrypting a sensor reading"""
        try:
            data = request.json or {}
            sensor_type = data.get('sensor_type', 'ECG')
            reading_value = data.get('reading_value', 'HR=72,BP=120/80,O2=98')
            
            # Get device's encryption keys from storage
            key_record = storage.get_device_key(device_id)
            if not key_record:
                return jsonify({"success": False, "error": "Device not registered"}), 404
            
            shared_secret_hex = key_record.get('shared_secret')
            gateway_id = key_record.get('gateway_id', 'GATEWAY_HUB_001')
            
            if not shared_secret_hex:
                return jsonify({"success": False, "error": "No shared secret"}), 400
            
            # Normalize hex
            if isinstance(shared_secret_hex, str) and shared_secret_hex.startswith('0x'):
                shared_secret_hex = shared_secret_hex[2:]
            
            shared_secret_bytes = bytes.fromhex(shared_secret_hex)
            session_id = f"{device_id}_{gateway_id}"
            
            # Device derives session key (same as gateway will use)
            session_key, auth_tag = AuthenticationProtocol.create_session_key(shared_secret_bytes, session_id)
            
            # Device encrypts the reading
            plaintext = f"{sensor_type}:{reading_value}".encode()
            sess = DeviceAuthenticationSession(device_id, gateway_id)
            sess.session_key = session_key
            sess.state = 'AUTHENTICATED'
            
            encrypted_payload = sess.encrypt_message(plaintext)
            
            # Return ONLY the encrypted payload (like a real device would send)
            return jsonify({
                "success": True,
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "encrypted_payload": encrypted_payload,
                "message": "Encrypted sensor reading ready to send to gateway"
            }), 200
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/gateway-decrypt-device-data', methods=['POST'])
    def gateway_decrypt_device_data():
        """Gateway receives encrypted data from IoT device and decrypts it"""
        try:
            data = request.json or {}
            device_id = data.get('device_id')
            encrypted_payload = data.get('encrypted_payload')
            
            if not device_id or not encrypted_payload:
                return jsonify({"success": False, "error": "Missing device_id or encrypted_payload"}), 400
            
            # Gateway retrieves device keys from storage
            key_record = storage.get_device_key(device_id)
            if not key_record:
                return jsonify({"success": False, "error": "Device not found"}), 404
            
            shared_secret_hex = key_record.get('shared_secret')
            gateway_id = key_record.get('gateway_id', 'GATEWAY_HUB_001')
            
            if not shared_secret_hex:
                return jsonify({"success": False, "error": "No shared secret for device"}), 400
            
            # Normalize hex
            if isinstance(shared_secret_hex, str) and shared_secret_hex.startswith('0x'):
                shared_secret_hex = shared_secret_hex[2:]
            
            shared_secret_bytes = bytes.fromhex(shared_secret_hex)
            session_id = f"{device_id}_{gateway_id}"
            
            # Gateway derives the SAME session key
            session_key, auth_tag = AuthenticationProtocol.create_session_key(shared_secret_bytes, session_id)
            
            # Gateway decrypts
            sess = DeviceAuthenticationSession(device_id, gateway_id)
            sess.session_key = session_key
            sess.state = 'AUTHENTICATED'
            
            iv_hex = encrypted_payload.get('iv')
            ciphertext_hex = encrypted_payload.get('ciphertext')
            hmac_hex = encrypted_payload.get('hmac')
            
            decrypted = sess.decrypt_message(iv_hex, ciphertext_hex, hmac_hex)
            
            # Verify on blockchain
            blockchain_info = blockchain.get_device_from_blockchain(device_id) if blockchain else {"error": "blockchain not initialized"}
            
            return jsonify({
                "success": True,
                "device_id": device_id,
                "decrypted_sensor_reading": decrypted.decode() if decrypted else None,
                "verified_on_blockchain": True if 'error' not in blockchain_info else False,
                "blockchain_status": blockchain_info,
                "message": "Data decrypted and verified from blockchain"
            }), 200
            
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
    
    @app.route('/api/simulate-encrypted', methods=['POST'])
    def simulate_encrypted():
        """Simulate a device sending an encrypted message and gateway decryption"""
        try:
            data = request.json or {}
            device_id = data.get('device_id')
            plaintext = (data.get('plaintext') or '').encode()

            if not device_id:
                return jsonify({'success': False, 'error': 'device_id required'}), 400

            key_record = storage.get_device_key(device_id)
            if not key_record:
                return jsonify({'success': False, 'error': 'Device not found in DB'}), 404

            # Extract shared secret and gateway id
            shared_secret_hex = key_record.get('shared_secret')
            gateway_id = key_record.get('gateway_id', 'GATEWAY_HUB_001')

            if not shared_secret_hex:
                return jsonify({'success': False, 'error': 'No shared secret for device'}), 400

            # Normalize hex
            if isinstance(shared_secret_hex, str) and shared_secret_hex.startswith('0x'):
                shared_secret_hex = shared_secret_hex[2:]

            shared_secret_bytes = bytes.fromhex(shared_secret_hex)

            # Deterministic session id for demo: device_gateway
            session_id = f"{device_id}_{gateway_id}"

            # Derive session key
            session_key, auth_tag = AuthenticationProtocol.create_session_key(shared_secret_bytes, session_id)

            # Create a session object (used for encrypt/decrypt helpers)
            sess = DeviceAuthenticationSession(device_id, gateway_id)
            sess.session_key = session_key
            sess.state = 'AUTHENTICATED'

            # Device encrypts the message
            encrypted = sess.encrypt_message(plaintext)

            # Gateway decrypts the message (same session key)
            decrypted = sess.decrypt_message(encrypted['iv'], encrypted['ciphertext'], encrypted['hmac'])

            # Fetch on-chain device info
            blockchain_info = blockchain.get_device_from_blockchain(device_id) if blockchain else {'error': 'blockchain not initialized'}

            return jsonify({
                'success': True,
                'device_id': device_id,
                'encrypted': encrypted,
                'decrypted_text': decrypted.decode() if decrypted else None,
                'auth_tag': auth_tag.hex(),
                'blockchain_info': blockchain_info
            }), 200

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/decryption', methods=['GET'])
    def decryption_page():
        """Render the Decryption & Authentication demo page"""
        page_html = '''
        <!doctype html> <html> <head> <meta charset="utf-8"> <title>Decryption & Authentication</title> <style> body{font-family:Segoe UI, Tahoma, Geneva, Verdana, sans-serif;padding:20px;background:#f6f8fb}
            .panel{background:#fff;padding:20px;border-radius:8px;max-width:900px;margin:0 auto;box-shadow:0 6px 18px rgba(0,0,0,0.08)}
            label{display:block;margin-top:10px;font-weight:600}
            textarea,input,select{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px}
            button{margin-top:12px;padding:10px 14px;background:#667eea;color:#fff;border:none;border-radius:6px;cursor:pointer}
            button:hover{background:#5568d3}
            pre{background:#0f1724;color:#dbeafe;padding:12px;border-radius:6px;overflow:auto;min-height:40px}
            .result-box{background:#e8f5e9;border-left:4px solid #4caf50;padding:15px;border-radius:4px;margin:10px 0;display:none}
            .result-box.show{display:block}
            .result-label{font-weight:600;color:#2e7d32;margin-bottom:5px}
            .result-value{font-family:monospace;color:#1b5e20;word-break:break-all}
            .error-box{background:#ffebee;border-left:4px solid #f44336;padding:15px;border-radius:4px;margin:10px 0;display:none;color:#c62828}
            .error-box.show{display:block}
          </style> </head> <body> <div class="panel"> <h2>" Decryption & Authentication Demo</h2> <p>Simulate a connected device sending encrypted data; gateway will decrypt and display result along with blockchain verification.</p> <label>Select Device</label> <select id="deviceSelect"></select> <label>Plaintext Message to Send</label> <textarea id="plaintext" rows="3">Patient blood pressure: 120/80</textarea> <button onclick="simulate()">" Simulate Send & Decrypt</button> <div class="error-box" id="errorBox"></div> <div class="result-box" id="resultBox"> <h3>... Decryption Successful!</h3> <div style="background:#fff;padding:12px;border-radius:4px;margin:10px 0;"> <div class="result-label">"" Decrypted Message:</div> <div class="result-value" id="decryptedMsg" style="font-size:14px;padding:10px;background:#f5f5f5;border-radius:3px;color:#333"></div> </div> <h3>"' Encryption Details</h3> <pre id="encrypted" style="font-size:11px"></pre> <h3><i class="fa-solid fa-cube"></i> Blockchain Verification</h3> <pre id="blockchain" style="font-size:11px"></pre> </div> </div> <script> function loadDevices(){
              fetch('/api/stored-devices').then(r=>r.json()).then(list=>{
                const sel=document.getElementById('deviceSelect');
                if(!list || list.length === 0) {
                  sel.innerHTML='<option value="">No devices registered</option>';
                } else {
                  sel.innerHTML='<option value="">-- Select Device --</option>' + list.map(d=>`<option value="${d.device_id}">${d.device_id}</option>`).join('');
                }
              }).catch(e => console.error('Error loading devices:', e))
            }

            function simulate(){
              const device=document.getElementById('deviceSelect').value;
              const pt=document.getElementById('plaintext').value;
              const errorBox=document.getElementById('errorBox');
              const resultBox=document.getElementById('resultBox');
              
              errorBox.classList.remove('show');
              resultBox.classList.remove('show');
              
              if(!device){ 
                errorBox.textContent = ' Please select a device first';
                errorBox.classList.add('show');
                return; 
              }
              if(!pt.trim()) {
                errorBox.textContent = ' Please enter a message to encrypt';
                errorBox.classList.add('show');
                return;
              }
              
              fetch('/api/simulate-encrypted',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_id:device, plaintext:pt})})
                .then(r=>r.json()).then(resp=>{
                  if(!resp.success){ 
                    errorBox.textContent = ' ' + (resp.error||'Unknown error');
                    errorBox.classList.add('show');
                    return; 
                  }
                  
                  // Display decrypted message prominently
                  document.getElementById('decryptedMsg').textContent = resp.decrypted_text || 'DECRYPTION_FAILED';
                  
                  // Display encrypted details
                  document.getElementById('encrypted').textContent = JSON.stringify(resp.encrypted,null,2);
                  
                  // Display blockchain verification
                  document.getElementById('blockchain').textContent = JSON.stringify(resp.blockchain_info,null,2);
                  
                  resultBox.classList.add('show');
                }).catch(e => {
                  errorBox.textContent = ' Error: ' + e.message;
                  errorBox.classList.add('show');
                })
            }

            loadDevices();
          </script> </body> </html> '''
        return render_template_string(page_html)
    
    @app.route('/api/esp-device-provision', methods=['POST'])
    def esp_device_provision():
        """Provision ESP32 device and register to blockchain"""
        try:
            data = request.json or {}
            device_id = data.get('device_id')
            device_name = data.get('device_name', 'Unknown Device')
            device_type = data.get('device_type', 'IoT_Sensor')
            location = data.get('location', 'Unknown')
            mac_address = data.get('mac_address', 'N/A')
            
            if not device_id:
                return jsonify({"success": False, "error": "device_id required"}), 400
            
            # Create device first
            requests.post(f"http://localhost:5000/api/create-device", json={
                "device_id": device_id,
                "device_name": device_name,
                "device_type": device_type,
                "location": location
            })
            
            # Register to blockchain
            reg_result = device_manager.register_to_blockchain(device_id)
            
            if not reg_result.get('success'):
                return jsonify({
                    "success": False,
                    "error": reg_result.get('error', 'Registration failed')
                }), 400
            
            # Get device keys
            device_key = storage.get_device_key(device_id)
            
            return jsonify({
                "success": True,
                "device_id": device_id,
                "device_key": device_key.get('shared_secret', device_id)[:32] if device_key else device_id,
                "blockchain_tx": reg_result.get('blockchain_tx'),
                "block_number": reg_result.get('block_number'),
                "message": "Device provisioned and registered to blockchain"
            }), 200
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/esp-sensor-upload', methods=['POST'])
    def esp_sensor_upload():
        """Receive encrypted sensor data from ESP device"""
        try:
            data = request.json or {}
            device_id = data.get('device_id')
            sensor_type = data.get('sensor_type', 'Unknown')
            reading_value = data.get('reading_value')
            encrypted_data = data.get('encrypted_data', None)
            
            if not device_id or not reading_value:
                return jsonify({"success": False, "error": "Missing device_id or reading_value"}), 400
            
            # Get device from storage
            device_key = storage.get_device_key(device_id)
            if not device_key:
                return jsonify({"success": False, "error": "Device not registered"}), 404
            
            # Calculate hash of the received data
            from Crypto.Hash import SHA256 as SHA256_HASH
            data_to_hash = f"{sensor_type}:{reading_value}:{data.get('timestamp', '')}".encode()
            hash_obj = SHA256_HASH.new(data_to_hash)
            data_hash = hash_obj.hexdigest()
            
            # Create audit log for this sensor reading
            log_entry = {
                "event_type": "SENSOR_READING",
                "device_id": device_id,
                "message": f"{sensor_type} reading received",
                "metadata": {
                    "sensor_type": sensor_type,
                    "reading_value": reading_value,
                    "timestamp": data.get('timestamp'),
                    "data_hash": data_hash,
                    "encrypted_payload": encrypted_data
                }
            }
            storage.save_audit_log(log_entry)
            
            # Update ESP device connection status directly in MongoDB
            try:
                # Save to esp_devices collection
                esp_device_data = {
                    "device_id": device_id,
                    "connection_status": "CONNECTED",
                    "last_seen": datetime.now().isoformat(),
                    "last_packet": {
                        "sensor_type": sensor_type,
                        "reading_value": reading_value,
                        "hash": data_hash,
                        "encrypted_payload": encrypted_data[:50] + "..." if encrypted_data and len(encrypted_data) > 50 else encrypted_data,
                        "timestamp": data.get('timestamp')
                    }
                }
                
                # Direct MongoDB insert
                esp_devices_col = storage.db['esp_devices']
                esp_devices_col.update_one(
                    {'device_id': device_id},
                    {'$set': {**esp_device_data, 'updated_at': datetime.now()}},
                    upsert=True
                )
                print(f"[+] Saved ESP device status for {device_id}")
            except Exception as e:
                print(f"[!] Warning: Could not save ESP device status: {e}")
            
            # Get blockchain info for device
            blockchain_info = blockchain.get_device_from_blockchain(device_id) if blockchain else {}
            
            return jsonify({
                "success": True,
                "device_id": device_id,
                "sensor_type": sensor_type,
                "reading_stored": True,
                "data_hash": data_hash,
                "blockchain_status": "Active" if blockchain_info.get('is_active') else "Inactive",
                "block_number": blockchain_info.get('block_number') if 'error' not in blockchain_info else None,
                "message": "Sensor reading received and logged"
            }), 200
            
        except Exception as e:
            print(f"[-] Error in esp_sensor_upload: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/stored-devices', methods=['GET'])
    def stored_devices():
        """Get all stored devices"""
        try:
            devices = device_manager.get_all_stored_devices()
            return jsonify(devices), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/esp-devices', methods=['GET'])
    def esp_devices():
        """Get all ESP devices with connection status"""
        try:
            # Query MongoDB directly
            esp_devices_col = storage.db['esp_devices']
            devices = list(esp_devices_col.find().sort('updated_at', -1))

            # Auto-expire: mark DISCONNECTED if no packet received in the last 30 s
            STALE_THRESHOLD_SECONDS = 30
            now = datetime.now()

            for device in devices:
                if '_id' in device:
                    device['_id'] = str(device['_id'])
                last_seen_str = device.get('last_seen')
                if last_seen_str:
                    try:
                        last_seen_dt = datetime.fromisoformat(last_seen_str)
                        elapsed = (now - last_seen_dt).total_seconds()
                        if elapsed > STALE_THRESHOLD_SECONDS:
                            device['connection_status'] = 'DISCONNECTED'
                            esp_devices_col.update_one(
                                {'device_id': device.get('device_id')},
                                {'$set': {'connection_status': 'DISCONNECTED'}}
                            )
                    except Exception:
                        pass

            print(f"[D] Found {len(devices)} ESP devices")
            return jsonify(devices), 200
        except Exception as e:
            print(f"[-] Error getting ESP devices: {e}")
            return jsonify([]), 200  # Return empty array if no devices
    
    @app.route('/api/esp-devices/<device_id>', methods=['GET'])
    def esp_device_status(device_id):
        """Get specific ESP device status"""
        try:
            device = storage.get_esp_device_status(device_id)
            if not device:
                return jsonify({"error": "Device not found"}), 404
            return jsonify(device), 200
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

    # Admin: Access Control API
    @app.route('/api/admin/providers', methods=['GET'])
    def admin_list_providers():
        """List all registered healthcare providers."""
        try:
            providers = blockchain.get_all_providers()
            admin_addr = blockchain.get_admin_address()
            return jsonify({"success": True, "providers": providers, "admin": admin_addr}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/register-provider', methods=['POST'])
    def admin_register_provider():
        """Register a new healthcare provider on-chain."""
        try:
            data = request.json or {}
            address  = data.get('address', '').strip()
            name     = data.get('name', '').strip()
            role     = data.get('role', 'DOCTOR').strip()
            if not address or not name:
                return jsonify({"success": False, "error": "address and name are required"}), 400
            result = blockchain.register_provider(address, name, role)
            if result.get('success'):
                storage.save_audit_log({
                    "event_type": "PROVIDER_REGISTERED",
                    "device_id": "ADMIN",
                    "message": f"Provider {name} ({role}) registered",
                    "metadata": {"address": address, "name": name, "role": role,
                                 "tx_hash": result.get('tx_hash')}
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/revoke-provider', methods=['POST'])
    def admin_revoke_provider():
        """Revoke a healthcare provider."""
        try:
            data = request.json or {}
            address = data.get('address', '').strip()
            if not address:
                return jsonify({"success": False, "error": "address is required"}), 400
            result = blockchain.revoke_provider(address)
            if result.get('success'):
                storage.save_audit_log({
                    "event_type": "PROVIDER_REVOKED",
                    "device_id": "ADMIN",
                    "message": f"Provider {address} REVOKED",
                    "metadata": {"address": address, "tx_hash": result.get('tx_hash')}
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/grant-access', methods=['POST'])
    def admin_grant_access():
        """Grant a provider access to a patient's data.
        Auto-registers the provider on-chain if not yet registered (when name is supplied).
        """
        try:
            data = request.json or {}
            address    = data.get('address', '').strip()
            patient_id = data.get('patient_id', '').strip()
            name       = data.get('name', '').strip()
            role       = data.get('role', 'DOCTOR').strip() or 'DOCTOR'
            if not address or not patient_id:
                return jsonify({"success": False, "error": "address and patient_id are required"}), 400

            auto_registered = None
            # Check if provider is already registered on-chain
            provider_info = blockchain.get_provider(address)
            if not provider_info.get('is_registered'):
                # Auto-register if a name was provided
                if not name:
                    name = f"Provider-{address[:8]}"
                reg_result = blockchain.register_provider(address, name, role)
                if not reg_result.get('success'):
                    return jsonify({
                        "success": False,
                        "error": f"Provider is not registered and auto-registration failed: "
                                 f"{reg_result.get('error')}"
                    }), 500
                auto_registered = f"{name} ({role})"
                storage.save_audit_log({
                    "event_type": "PROVIDER_REGISTERED",
                    "device_id": "ADMIN",
                    "message": f"Provider {name} ({role}) auto-registered during grant-access",
                    "metadata": {"address": address, "name": name, "role": role,
                                 "tx_hash": reg_result.get('tx_hash')}
                })

            result = blockchain.grant_access(address, patient_id)
            if result.get('success') and auto_registered:
                result['auto_registered'] = auto_registered
            if result.get('success'):
                storage.save_audit_log({
                    "event_type": "ACCESS_GRANTED",
                    "device_id": "ADMIN",
                    "message": f"Access GRANTED: {address} ' patient {patient_id}",
                    "metadata": {"address": address, "patient_id": patient_id,
                                 "tx_hash": result.get('tx_hash')}
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/revoke-access', methods=['POST'])
    def admin_revoke_access():
        """Revoke a provider's access to a patient."""
        try:
            data = request.json or {}
            address    = data.get('address', '').strip()
            patient_id = data.get('patient_id', '').strip()
            if not address or not patient_id:
                return jsonify({"success": False, "error": "address and patient_id are required"}), 400
            result = blockchain.revoke_access(address, patient_id)
            if result.get('success'):
                storage.save_audit_log({
                    "event_type": "ACCESS_REVOKED",
                    "device_id": "ADMIN",
                    "message": f"Access REVOKED: {address} ' patient {patient_id}",
                    "metadata": {"address": address, "patient_id": patient_id,
                                 "tx_hash": result.get('tx_hash')}
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/assign-device', methods=['POST'])
    def admin_assign_device():
        """Assign an IoMT device to a patient.
        Auto-registers the device on-chain first if it exists in MongoDB but not yet on the contract.
        """
        try:
            data = request.json or {}
            device_id  = data.get('device_id', '').strip()
            patient_id = data.get('patient_id', '').strip()
            if not device_id or not patient_id:
                return jsonify({"success": False, "error": "device_id and patient_id are required"}), 400

            # Pre-flight: check if device is active on-chain
            is_active = False
            if blockchain.contract:
                try:
                    is_active = blockchain.contract.functions.isKeyActive(device_id).call()
                except Exception:
                    is_active = False

            if not is_active:
                # Device not on-chain yet - fetch its keys from MongoDB and register it first
                mongo_device = storage.get_device_key(device_id)
                if not mongo_device:
                    return jsonify({
                        "success": False,
                        "error": f"Device '{device_id}' is not registered on-chain and was not found "
                                 f"in the database. Authenticate the device first."
                    }), 400
                public_key = mongo_device.get('public_key', '')
                if not public_key:
                    return jsonify({
                        "success": False,
                        "error": f"Device '{device_id}' found in database but has no public key stored."
                    }), 400
                # Use same bytes for both kyber and dilithium keys (single-key devices)
                reg_result = blockchain.register_device_on_blockchain(
                    device_id, public_key, public_key
                )
                if not reg_result.get('success'):
                    return jsonify({
                        "success": False,
                        "error": f"Auto-registration of device '{device_id}' on-chain failed: "
                                 f"{reg_result.get('error')}"
                    }), 500
                storage.save_audit_log({
                    "event_type": "DEVICE_AUTO_REGISTERED",
                    "device_id": device_id,
                    "message": f"Device auto-registered on-chain before patient assignment",
                    "metadata": {"tx_hash": reg_result.get('tx_hash'), "patient_id": patient_id}
                })

            result = blockchain.assign_device_to_patient(device_id, patient_id)
            if result.get('success'):
                storage.save_audit_log({
                    "event_type": "DEVICE_ASSIGNED",
                    "device_id": device_id,
                    "message": f"Device {device_id} assigned to patient {patient_id}",
                    "metadata": {"patient_id": patient_id, "tx_hash": result.get('tx_hash')}
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/sync-blockchain', methods=['POST'])
    def admin_sync_blockchain():
        """Register all active MongoDB devices that are missing from the blockchain."""
        results = []
        total = synced = skipped = failed = 0
        try:
            devices = storage.get_all_device_keys()
            total = len(devices)
            for dev in devices:
                device_id  = dev.get('device_id', '')
                public_key = dev.get('public_key', '')
                is_active  = dev.get('is_active', False)
                if not device_id or not public_key or not is_active:
                    results.append({"device_id": device_id or "(no id)",
                                    "status": "skipped", "error": "inactive or no key"})
                    skipped += 1
                    continue
                # Check on-chain first
                already = False
                if blockchain.contract:
                    try:
                        already = blockchain.contract.functions.isKeyActive(device_id).call()
                    except Exception:
                        already = False
                if already:
                    results.append({"device_id": device_id, "status": "skipped",
                                    "tx_hash": None})
                    skipped += 1
                    continue
                # Register on-chain
                reg = blockchain.register_device_on_blockchain(device_id, public_key, public_key)
                if reg.get('success'):
                    synced += 1
                    results.append({"device_id": device_id, "status": "registered",
                                    "tx_hash": reg.get('tx_hash')})
                    storage.save_audit_log({
                        "event_type": "BLOCKCHAIN_SYNC",
                        "device_id": device_id,
                        "message": f"Device {device_id} synced to blockchain",
                        "metadata": {"tx_hash": reg.get('tx_hash'), "block": reg.get('block_number')}
                    })
                else:
                    failed += 1
                    results.append({"device_id": device_id, "status": "failed",
                                    "error": reg.get('error', 'Unknown error')})
            return jsonify({
                "success": True,
                "total": total, "synced": synced,
                "skipped": skipped, "failed": failed,
                "results": results
            }), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/admin/check-access', methods=['GET'])
    def admin_check_access():
        """Check whether a provider has access to a patient."""
        address    = request.args.get('address', '').strip()
        patient_id = request.args.get('patient_id', '').strip()
        if not address or not patient_id:
            return jsonify({"error": "address and patient_id query params required"}), 400
        has_access = blockchain.check_access(address, patient_id)
        provider   = blockchain.get_provider(address)
        return jsonify({
            "address": address,
            "patient_id": patient_id,
            "has_access": has_access,
            "provider": provider
        }), 200

    @app.route('/api/admin/device-info/<device_id>', methods=['GET'])
    def admin_device_public_info(device_id):
        """Return public on-chain metadata for a device (patient assignment etc.)."""
        info = blockchain.get_device_public_info(device_id)
        return jsonify(info), 200

    @app.route('/admin', methods=['GET'])
    def admin_access_control_page():
        """Admin access-control management page."""
        return render_template_string(ADMIN_HTML)

    # 
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
