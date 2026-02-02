# 📡 IoT Blockchain Dashboard - API DOCUMENTATION

## Base URL
```
http://localhost:5000
```

---

## 🔗 Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard HTML |
| GET | `/api/ganache-status` | Ganache connection status |
| POST | `/api/create-device` | Create simulated device |
| POST | `/api/register-blockchain` | Register device to blockchain & MongoDB |
| GET | `/api/encryption-details/<device_id>` | Get device encryption details |
| GET | `/api/stored-devices` | Get all registered devices |
| GET | `/api/audit-events` | Get authentication audit events |
| GET | `/api/metrics` | Get system metrics |

---

## 📋 Endpoint Details

### 1. Dashboard
```http
GET /
```

**Description:** Returns the main dashboard HTML

**Response:** HTML page

**Example:**
```bash
curl http://localhost:5000/
```

---

### 2. Ganache Status
```http
GET /api/ganache-status
```

**Description:** Check Ganache blockchain connection status

**Response:**
```json
{
  "connected": true,
  "chain_id": 1337,
  "message": "Connected"
}
```

**Example:**
```bash
curl http://localhost:5000/api/ganache-status
```

---

### 3. Create Device
```http
POST /api/create-device
Content-Type: application/json
```

**Description:** Create a simulated IoT device

**Request Body:**
```json
{
  "device_id": "BP_MON_001",
  "device_type": "Blood Pressure Monitor",
  "manufacturer": "Medical Corp"
}
```

**Response:**
```json
{
  "success": true,
  "device": {
    "device_id": "BP_MON_001",
    "device_type": "Blood Pressure Monitor",
    "manufacturer": "Medical Corp",
    "status": "SIMULATED",
    "created_at": "2024-01-15T10:30:00.000Z",
    "is_registered_db": false,
    "is_registered_blockchain": false
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/create-device \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "BP_MON_001",
    "device_type": "Blood Pressure Monitor",
    "manufacturer": "Medical Corp"
  }'
```

**Possible Device Types:**
- Blood Pressure Monitor
- Glucose Meter
- Pulse Oximeter
- Temperature Sensor
- ECG Monitor

---

### 4. Register to Blockchain
```http
POST /api/register-blockchain
Content-Type: application/json
```

**Description:** Register device to Ganache blockchain AND MongoDB

**Request Body:**
```json
{
  "device_id": "BP_MON_001",
  "gateway_id": "GATEWAY_HUB_001"
}
```

**Response (Success):**
```json
{
  "success": true,
  "device_id": "BP_MON_001",
  "blockchain_tx": "0x123abc456def789...",
  "block_number": 100,
  "mongodb_stored": true,
  "encryption": {
    "protocol": "Kyber-inspired PQ-KEM",
    "algorithm": "HMAC-SHA256",
    "public_key": "0xaa...ff",
    "key_size": 256,
    "shared_secret": "0xbb...gg"
  },
  "message": "Device registered to BOTH Ganache and MongoDB!"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Device not found",
  "note": "Make sure Ganache is running and contract is deployed"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/register-blockchain \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "BP_MON_001",
    "gateway_id": "GATEWAY_HUB_001"
  }'
```

**Note:** 
- First create device with `/api/create-device`
- Then register to blockchain with this endpoint
- Wait 2-15 seconds for blockchain confirmation
- All data is stored in both Ganache and MongoDB

---

### 5. Get Encryption Details
```http
GET /api/encryption-details/<device_id>
```

**Description:** Get complete encryption and blockchain details for a device

**Response:**
```json
{
  "device_id": "BP_MON_001",
  "public_key_full": "0xaa11bb22cc33dd44ee55ff66...",
  "shared_secret_full": "0xbb11cc22dd33ee44ff55aa66...",
  "encryption_algorithm": "HMAC-SHA256",
  "key_exchange_protocol": "Kyber-inspired Post-Quantum KEM",
  "is_active": true,
  "authenticated_at": "2024-01-15T10:30:00.000Z",
  "gateway_id": "GATEWAY_HUB_001",
  "blockchain_tx": "0x123abc456def789...",
  "blockchain_block": 100
}
```

**Example:**
```bash
curl http://localhost:5000/api/encryption-details/BP_MON_001
```

---

### 6. Get Stored Devices
```http
GET /api/stored-devices
```

**Description:** Get all registered devices from MongoDB and blockchain

**Response:**
```json
[
  {
    "device_id": "BP_MON_001",
    "is_active": true,
    "gateway_id": "GATEWAY_HUB_001",
    "authenticated_at": "2024-01-15T10:30:00.000Z",
    "total_events": 5,
    "successful_auths": 5,
    "public_key_preview": "0xaa11bb22cc33dd44...",
    "blockchain_tx": "0x123abc456def789...",
    "blockchain_block": 100
  },
  {
    "device_id": "SENSOR_002",
    "is_active": true,
    "gateway_id": "GATEWAY_HUB_001",
    "authenticated_at": "2024-01-15T10:35:00.000Z",
    "total_events": 3,
    "successful_auths": 3,
    "public_key_preview": "0xbb11cc22dd33ee44...",
    "blockchain_tx": "0x456def789abc123...",
    "blockchain_block": 101
  }
]
```

**Example:**
```bash
curl http://localhost:5000/api/stored-devices
```

---

### 7. Get Audit Events
```http
GET /api/audit-events
```

**Description:** Get authentication audit events

**Response:**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "event_type": "AUTHENTICATED",
    "device_id": "BP_MON_001",
    "gateway_id": "GATEWAY_HUB_001",
    "message": "Device registered to blockchain and MongoDB",
    "metadata": {
      "device_type": "Blood Pressure Monitor",
      "auth_protocol": "PQ-KEM",
      "blockchain_tx": "0x123abc456def789...",
      "block_number": 100
    },
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
]
```

**Example:**
```bash
curl http://localhost:5000/api/audit-events
```

---

### 8. Get Metrics
```http
GET /api/metrics
```

**Description:** Get system-wide metrics

**Response:**
```json
{
  "registered_count": 2,
  "event_count": 8
}
```

**Example:**
```bash
curl http://localhost:5000/api/metrics
```

---

## 🔐 Request/Response Details

### Authentication
Currently **NO authentication required** (development mode)

For production, add:
```json
{
  "Authorization": "Bearer <token>"
}
```

### Content-Type
All POST requests should use:
```
Content-Type: application/json
```

### CORS
CORS is **enabled** for all origins (*)

For production, restrict to:
```
Access-Control-Allow-Origin: https://yourdomain.com
```

---

## 🧪 Testing with cURL

### Test 1: Check System Status
```bash
curl http://localhost:5000/api/ganache-status
curl http://localhost:5000/api/metrics
```

### Test 2: Create and Register Device
```bash
# Create device
curl -X POST http://localhost:5000/api/create-device \
  -H "Content-Type: application/json" \
  -d '{"device_id":"TEST_001","device_type":"Temperature Sensor"}'

# Register to blockchain
curl -X POST http://localhost:5000/api/register-blockchain \
  -H "Content-Type: application/json" \
  -d '{"device_id":"TEST_001"}'

# Get devices
curl http://localhost:5000/api/stored-devices

# Get details
curl http://localhost:5000/api/encryption-details/TEST_001
```

### Test 3: View Audit Events
```bash
curl http://localhost:5000/api/audit-events
```

---

## 💻 JavaScript/Fetch Examples

### Get Ganache Status
```javascript
fetch('http://localhost:5000/api/ganache-status')
  .then(r => r.json())
  .then(data => console.log(data));
```

### Create Device
```javascript
fetch('http://localhost:5000/api/create-device', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    device_id: 'BP_MON_001',
    device_type: 'Blood Pressure Monitor',
    manufacturer: 'Medical Corp'
  })
})
.then(r => r.json())
.then(data => console.log(data));
```

### Register to Blockchain
```javascript
fetch('http://localhost:5000/api/register-blockchain', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    device_id: 'BP_MON_001',
    gateway_id: 'GATEWAY_HUB_001'
  })
})
.then(r => r.json())
.then(data => console.log(data));
```

### Get All Devices
```javascript
fetch('http://localhost:5000/api/stored-devices')
  .then(r => r.json())
  .then(devices => console.table(devices));
```

---

## 🐍 Python/Requests Examples

### Get Ganache Status
```python
import requests

response = requests.get('http://localhost:5000/api/ganache-status')
print(response.json())
```

### Create Device
```python
import requests

data = {
    'device_id': 'BP_MON_001',
    'device_type': 'Blood Pressure Monitor',
    'manufacturer': 'Medical Corp'
}

response = requests.post('http://localhost:5000/api/create-device', json=data)
print(response.json())
```

### Register to Blockchain
```python
import requests

data = {
    'device_id': 'BP_MON_001',
    'gateway_id': 'GATEWAY_HUB_001'
}

response = requests.post('http://localhost:5000/api/register-blockchain', json=data)
print(response.json())
```

### Get Audit Events
```python
import requests

response = requests.get('http://localhost:5000/api/audit-events')
events = response.json()
for event in events:
    print(f"{event['timestamp']}: {event['event_type']}")
```

---

## ❌ Error Responses

### 500 - Internal Server Error
```json
{
  "success": false,
  "error": "Device not found"
}
```

### 404 - Not Found
```
Device not found in MongoDB
```

### 400 - Bad Request
```json
{
  "success": false,
  "error": "Invalid device ID format"
}
```

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |

---

## ⏱️ Response Times

| Endpoint | Time |
|----------|------|
| `/api/ganache-status` | < 100ms |
| `/api/create-device` | < 50ms |
| `/api/register-blockchain` | 2-15s (blockchain mining) |
| `/api/stored-devices` | < 100ms |
| `/api/encryption-details/<id>` | < 50ms |
| `/api/audit-events` | < 100ms |
| `/api/metrics` | < 50ms |

---

## 🔄 Workflow Example

```
1. Create Device
   POST /api/create-device
   → Returns: device object

2. Register to Blockchain
   POST /api/register-blockchain
   → Returns: blockchain TX hash + MongoDB stored confirmation

3. Get All Devices
   GET /api/stored-devices
   → Returns: list of all registered devices

4. View Device Details
   GET /api/encryption-details/<device_id>
   → Returns: full encryption keys + blockchain details

5. Monitor Events
   GET /api/audit-events
   → Returns: all authentication events in MongoDB
```

---

## 🚀 Integration Examples

### Complete Flow with Python
```python
import requests
import json

BASE_URL = 'http://localhost:5000'

# 1. Create device
print("[*] Creating device...")
device_resp = requests.post(f'{BASE_URL}/api/create-device', json={
    'device_id': 'SENSOR_001',
    'device_type': 'Temperature Sensor'
})
print(f"[+] Device created: {device_resp.json()}")

# 2. Register to blockchain
print("[*] Registering to blockchain...")
reg_resp = requests.post(f'{BASE_URL}/api/register-blockchain', json={
    'device_id': 'SENSOR_001'
})
result = reg_resp.json()
print(f"[+] Registered!")
print(f"    TX Hash: {result['blockchain_tx']}")
print(f"    Block: {result['block_number']}")

# 3. Get details
print("[*] Getting device details...")
details_resp = requests.get(f'{BASE_URL}/api/encryption-details/SENSOR_001')
details = details_resp.json()
print(f"[+] Device Details:")
print(f"    Public Key: {details['public_key_full'][:32]}...")
print(f"    Gateway: {details['gateway_id']}")

# 4. View all devices
print("[*] Viewing all devices...")
devices_resp = requests.get(f'{BASE_URL}/api/stored-devices')
devices = devices_resp.json()
print(f"[+] Total devices: {len(devices)}")
for device in devices:
    print(f"    - {device['device_id']} (Block: {device['blockchain_block']})")
```

---

## 📖 More Information

- [README_INTEGRATED.md](README_INTEGRATED.md) - Feature overview
- [QUICK_START.md](QUICK_START.md) - 5-minute setup
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed installation

---

**API Version:** 1.0
**Status:** ✅ Production Ready
**Last Updated:** January 2024
