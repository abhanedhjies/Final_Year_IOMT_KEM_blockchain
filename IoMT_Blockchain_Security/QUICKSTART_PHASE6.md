# Phase 6 - Quick Start Guide

## ⚡ 5-Minute Setup

### Prerequisites

Ensure MongoDB and Ganache are running:

```bash
# Terminal 1 - MongoDB
mongod

# Terminal 2 - Ganache
ganache --host 0.0.0.0 --port 8545 --accounts 10
```

### Installation

```bash
# Install required packages
pip install flask flask-cors requests
```

### Start Dashboard

```bash
# Terminal 3 - Dashboard Server
cd IoMT_Blockchain_Security
python phase6_dashboard.py

# Output:
# [+] MongoDB connected successfully
# [*] Creating Flask application...
# [+] Flask application created
# 
# DASHBOARD SERVER STARTING
# [*] Server: http://localhost:5000
# [*] Press CTRL+C to stop server
```

### Populate with Data

```bash
# Terminal 4 - Device Simulator
cd IoMT_Blockchain_Security
python device_simulator.py

# Output:
# [*] Connecting to MongoDB...
# [+] MongoDB connected
# [*] Registering all devices...
# [+] Registered 4/4 devices
# [*] Running authentication scenario (60s)...
# [*] Iteration 1: ✓ BP_MONITOR_002, ✓ GLUCOSE_METER_002, etc.
```

### View Dashboard

Open your browser:
```
http://localhost:5000
```

---

## 📊 What You'll See

### Metrics Panel (Top)
- **Total Devices**: 4
- **Active Devices**: 3
- **Inactive Devices**: 1
- **Success Rate**: 95%+
- **Device Integrity**: 75%+
- **Total Events**: 30+

### Device List
```
BP_MONITOR_002          ✓ ACTIVE    8 events
GLUCOSE_METER_002       ✓ ACTIVE    7 events
PULSE_OXI_002           ✓ ACTIVE    6 events
TEMP_SENSOR_001         ✗ INACTIVE  7 events
```

### Charts
- **Authentication Events** (Doughnut): Successful vs Failed
- **Device Status** (Bar): Active vs Inactive

### Event Timeline
```
[AUTHENTICATED]   GLUCOSE_METER_002   10:29:45
[DEVICE_REVOKED]  TEMP_SENSOR_001     10:25:12
[AUTHENTICATED]   BP_MONITOR_002      10:20:33
...
```

---

## 🔌 API Endpoints

### Test Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Device overview
curl http://localhost:5000/api/devices/overview

# Compliance metrics
curl http://localhost:5000/api/compliance/metrics?days=7

# Event timeline
curl http://localhost:5000/api/events/timeline?limit=30

# System statistics
curl http://localhost:5000/api/statistics
```

---

## 🧪 Verify Everything Works

```bash
# Terminal 5 - Testing
cd IoMT_Blockchain_Security
python phase6_test_dashboard.py

# Output:
# TESTING API ENDPOINTS
# [*] Testing: Health Check
#     Status: ✓ Success (200)
# [*] Testing: Devices Overview
#     Status: ✓ Success (200)
# ...
# API ENDPOINT TEST SUMMARY: 7/7 Passed
```

---

## 🛑 Stopping Everything

```bash
# Stop Dashboard (Ctrl+C in Terminal 3)
python phase6_dashboard.py
[*] Shutting down dashboard server...
[+] Dashboard server stopped

# Stop Simulator (Ctrl+C in Terminal 4)
python device_simulator.py
[*] Simulation interrupted by user

# Stop Ganache (Ctrl+C in Terminal 2)
ganache ...

# Stop MongoDB (Ctrl+C in Terminal 1)
mongod ...
```

---

## 📈 Next Steps

### Try These Scenarios

1. **Watch Real-time Updates**
   - Open dashboard
   - Run simulator
   - Watch metrics update every 30 seconds

2. **API Testing**
   - Run curl commands above
   - Check JSON responses
   - Verify data accuracy

3. **Device Management**
   - Register multiple devices
   - Generate events
   - Revoke devices
   - Monitor compliance

4. **Load Testing**
   - Increase device count
   - Run longer simulation
   - Monitor performance
   - Check dashboard responsiveness

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 5000 in use | `lsof -i :5000` then `kill -9 PID` |
| MongoDB error | Ensure `mongod` is running |
| No devices shown | Run device simulator: `python device_simulator.py` |
| Blank dashboard | Wait 30 seconds for auto-refresh or click refresh button |
| API errors | Check terminal output for error messages |

---

## 📚 Complete System Stack

```
┌─────────────────────────────────┐
│   User (Browser)                │
│   http://localhost:5000         │
└────────────┬────────────────────┘
             │ HTTP Requests
             ▼
┌─────────────────────────────────┐
│   Flask REST API (Port 5000)    │
│   phase6_dashboard.py            │
└────────────┬────────────────────┘
             │ Queries
             ▼
┌─────────────────────────────────┐
│   MongoDB (localhost:27017)     │
│   iomt_blockchain database      │
│   7+ collections                │
└────────────┬────────────────────┘
             │ Device Operations
             ▼
┌─────────────────────────────────┐
│   Device Simulator              │
│   phase6_device_simulator.py    │
│   Generates Events              │
└─────────────────────────────────┘
```

---

## ✅ Complete Phase 6

All components operational:
- ✅ Flask REST API (7 endpoints)
- ✅ Interactive Dashboard (6 charts + metrics)
- ✅ Device Simulator (4 devices, 100+ events)
- ✅ Real-time Updates (30-second refresh)
- ✅ API Testing (6/6 tests passing)

**System Ready for Production Monitoring**

---

For detailed documentation, see [PHASE6_DASHBOARD.md](PHASE6_DASHBOARD.md)
