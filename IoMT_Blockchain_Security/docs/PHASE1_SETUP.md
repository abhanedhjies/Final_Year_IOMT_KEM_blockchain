# IoMT Blockchain Security - Phase 1 Setup Guide

## Project Overview

**Title:** Low-Cost Quantum-Resistant Secure Key Establishment for IoMT Devices Using Blockchain

**Phase 1 Goal:** Establish a development environment supporting:
- IoMT device simulation
- Post-quantum cryptography (Hash-based signatures in Phase 1, Kyber/Dilithium in Phase 2)
- Private blockchain (Ethereum via Hardhat/Ganache)
- Off-chain storage (MongoDB)

---

## What Has Been Created

### Folder Structure

```
IoMT_Blockchain_Security/
├── device/                          # IoMT Device Simulation
│   └── __init__.py                  # Device class and factory functions
├── gateway/                         # Gateway Aggregation
│   └── __init__.py                  # Gateway class for device management
├── blockchain/                      # Smart Contracts & Hardhat Config
│   ├── contracts/
│   │   └── PostQuantumKeyRegistry.sol   # Smart contract for key management
│   ├── scripts/                     # Deployment scripts (Phase 2)
│   ├── test/                        # Contract tests (Phase 2)
│   ├── hardhat.config.js           # Hardhat configuration
│   ├── package.json                # NPM dependencies
│   └── node_modules/               # Installed packages
├── storage/                         # Off-Chain Storage
│   └── __init__.py                  # MongoDB configuration and manager
├── docs/                            # Documentation
│   └── PHASE1_SETUP.md             # This file
├── venv/                            # Python Virtual Environment
├── test_env.py                      # Environment verification script
├── requirements.txt                 # Python dependencies
└── .gitignore                       # Git ignore file
```

---

## Environment Components

### 1. Python Virtual Environment (venv)
- **Python Version:** 3.11.2
- **Location:** `./venv/`
- **Activation:** `.\venv\Scripts\Activate.ps1` (Windows PowerShell)

### 2. Python Packages Installed

| Package | Version | Purpose |
|---------|---------|---------|
| pycryptodome | 3.23.0 | Cryptographic primitives (AES, SHA, etc.) |
| pymongo | 4.16.0 | MongoDB database driver |
| python-dotenv | 1.0.0 | Environment variable management |
| requests | 2.31.0 | HTTP client library |
| pytest | 7.4.3 | Unit testing framework |

### 3. Node.js/JavaScript Stack

| Package | Version | Purpose |
|---------|---------|---------|
| Hardhat | 2.28.3 | Smart contract development framework |
| @nomicfoundation/hardhat-toolbox | 6.1.0 | Essential Hardhat plugins |
| Solidity | 0.8.20 | Smart contract language |

### 4. External Systems

| System | Purpose | Required for Phase 1? |
|--------|---------|----------------------|
| MongoDB | Off-chain data storage | Optional (tested & working) |
| Ganache/Hardhat Network | Local blockchain | Phase 2+ |

---

## Phase 1 Verification Results

✅ **All Tests Passed:**

1. **Folder Structure** - All 5 required folders created
2. **Post-Quantum Cryptography** - Hash-based signatures working
3. **Symmetric Encryption (AES-256)** - Working correctly
4. **Python Dependencies** - All packages installed
5. **MongoDB Connectivity** - Successfully tested

---

## How to Use

### 1. Activate the Virtual Environment

```powershell
cd c:\Users\ajabh\OneDrive\Desktop\journal_IOT_Blockchain\IoMT_Blockchain_Security
.\venv\Scripts\Activate.ps1
```

### 2. Run Environment Tests

```powershell
python test_env.py
```

Expected output: All 5 tests should pass ✓

### 3. Test Individual Modules

```powershell
# Test IoMT Device module
python -m device

# Test Gateway module
python -m gateway

# Test Storage module
python -m storage
```

### 4. Check Solidity Smart Contract

```powershell
# View the smart contract
cat blockchain/contracts/PostQuantumKeyRegistry.sol

# Compile the contract (Phase 2)
cd blockchain
npm run compile
```

---

## What's Next? (Phase 2 Roadmap)

### Phase 2: Smart Contract Implementation
- [ ] Deploy PostQuantumKeyRegistry contract to Ganache
- [ ] Test key registration on-chain
- [ ] Implement key retrieval functions
- [ ] Add unit tests for smart contracts

### Phase 3: Device-Gateway Integration
- [ ] Implement Kyber key exchange (full version)
- [ ] Implement Dilithium signatures
- [ ] Device authentication protocol
- [ ] Gateway data aggregation

### Phase 4: MongoDB Integration
- [ ] Device key storage
- [ ] Device data persistence
- [ ] Audit trail logging
- [ ] Query optimization

### Phase 5: Full System Testing
- [ ] End-to-end device authentication
- [ ] Blockchain transaction verification
- [ ] Off-chain storage synchronization
- [ ] Performance benchmarking

---

## File Descriptions

### `test_env.py`
Comprehensive environment verification script that tests:
- Project folder structure
- Post-quantum cryptography
- Symmetric encryption (AES-256)
- Python package availability
- MongoDB connectivity

**Run with:** `python test_env.py`

### `device/__init__.py`
IoMT device simulation module containing:
- `IoTMDevice` class for device representation
- `create_device()` factory function
- Device key management methods

**Usage:**
```python
from device import create_device
device = create_device("DEVICE_001", "blood_pressure_monitor", "Philips")
```

### `gateway/__init__.py`
Gateway aggregation module containing:
- `IoTMGateway` class for data aggregation
- Device registration/management
- `create_gateway()` factory function

**Usage:**
```python
from gateway import create_gateway
gateway = create_gateway("GATEWAY_001", "Hospital A")
gateway.register_device("DEVICE_001", device)
```

### `storage/__init__.py`
Off-chain storage configuration containing:
- `StorageConfig` class for MongoDB configuration
- `StorageManager` class for storage operations
- Connection management

**Usage:**
```python
from storage import create_storage_manager
storage = create_storage_manager()
```

### `blockchain/hardhat.config.js`
Hardhat configuration for smart contract development:
- Solidity compiler settings
- Network configurations (Hardhat, Ganache)
- Test settings

### `blockchain/contracts/PostQuantumKeyRegistry.sol`
Smart contract for storing post-quantum public keys:
- Device key registration
- Key activation/deactivation
- Blockchain-based key management

---

## Important Notes

### Security Considerations
1. **Phase 1 uses hash-based signatures** - Full Kyber/Dilithium will be integrated in Phase 2
2. **Private keys** should never be stored in plaintext in production
3. **MongoDB** is optional for Phase 1 but recommended for testing
4. **Ganache** requires Node.js and will be started in Phase 2

### Low-Cost Implementation
- Uses open-source tools (Hardhat, MongoDB Community, Python)
- Minimal hardware requirements
- No external API dependencies
- Suitable for final-year engineering project

### Best Practices Followed
- Clean, modular code structure
- Clear comments explaining functionality
- Beginner-friendly module organization
- Comprehensive documentation
- Environment verification testing

---

## Troubleshooting

### MongoDB Connection Failed
- Install MongoDB Community Edition
- Start MongoDB: `mongod` (Windows)
- Note: MongoDB is optional for Phase 1

### Virtual Environment Issues
- Ensure Python 3.9+ is installed
- Delete `venv/` and recreate: `py -m venv venv`
- Reactivate: `.\venv\Scripts\Activate.ps1`

### Package Installation Errors
- Upgrade pip: `python -m pip install --upgrade pip`
- Clear cache: `pip cache purge`
- Reinstall: `pip install -r requirements.txt`

### Hardhat/Node Issues
- Check Node.js: `node --version`
- Reinstall node_modules: `npm install`
- Clear cache: `npm cache clean --force`

---

## Project Timeline & Phases

| Phase | Focus | Duration (Estimated) |
|-------|-------|----------------------|
| **Phase 1** (✓ Current) | Environment Setup | 1-2 hours |
| **Phase 2** | Smart Contracts | 2-3 hours |
| **Phase 3** | Device Integration | 3-4 hours |
| **Phase 4** | Storage Layer | 2-3 hours |
| **Phase 5** | Testing & Optimization | 2-3 hours |

**Total Duration:** ~12-15 hours for complete implementation

---

## Contact & Support

For questions or issues:
1. Review this Phase 1 Setup Guide
2. Check blockchain/contracts/PostQuantumKeyRegistry.sol comments
3. Run `python test_env.py` to verify environment
4. Review Phase 2 roadmap for next steps

---

**Created:** 2026-01-16  
**Status:** Phase 1 Complete ✓  
**Ready for Phase 2:** Yes
