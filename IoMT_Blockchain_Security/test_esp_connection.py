#!/usr/bin/env python3
"""
Test script to simulate ESP32 device sending sensor data to dashboard
"""

import requests
import json
from datetime import datetime
import time

# Dashboard endpoint
DASHBOARD_URL = "http://localhost:5000"

def test_esp_provision():
    """Test provisioning an ESP device"""
    print("\n" + "="*70)
    print("TESTING ESP DEVICE PROVISIONING")
    print("="*70 + "\n")
    
    # Step 1: Create a device
    print("[*] Creating simulated device...")
    response = requests.post(f"{DASHBOARD_URL}/api/create-device", json={
        "device_id": "ESP32_SENSOR_001",
        "device_type": "Temperature Sensor",
        "manufacturer": "Espressif"
    })
    
    if response.status_code == 200:
        print("[+] Device created successfully")
        print(f"    Response: {response.json()}")
    else:
        print(f"[-] Failed to create device: {response.status_code}")
        return
    
    # Step 2: Register to blockchain
    print("\n[*] Registering device to blockchain...")
    response = requests.post(f"{DASHBOARD_URL}/api/register-blockchain", json={
        "device_id": "ESP32_SENSOR_001",
        "gateway_id": "GATEWAY_HUB_001"
    })
    
    if response.status_code == 200:
        result = response.json()
        print("[+] Device registered successfully")
        print(f"    TX Hash: {result.get('blockchain_tx', 'N/A')[:32]}...")
        print(f"    Block: {result.get('block_number', 'N/A')}")
    else:
        print(f"[-] Failed to register device: {response.status_code}")
        return
    
    # Step 3: Send sensor readings
    print("\n[*] Sending sensor readings from ESP device...")
    
    for i in range(3):
        print(f"\n[*] Sending reading #{i+1}...")
        
        timestamp = datetime.now().isoformat()
        
        response = requests.post(f"{DASHBOARD_URL}/api/esp-sensor-upload", json={
            "device_id": "ESP32_SENSOR_001",
            "sensor_type": "Temperature",
            "reading_value": f"25.{i}°C",
            "timestamp": timestamp,
            "encrypted_data": f"ENCRYPTED_PAYLOAD_{i}" * 5  # Simulate encrypted data
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"[+] Sensor reading #{i+1} uploaded successfully")
            print(f"    Data Hash: {result.get('data_hash', 'N/A')[:32]}...")
            print(f"    Status: {result.get('blockchain_status', 'N/A')}")
        else:
            print(f"[-] Failed to upload reading: {response.status_code}")
            print(f"    Error: {response.text}")
        
        time.sleep(1)
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)
    print("\n[*] Check the dashboard at: http://localhost:5000")
    print("[*] You should see:")
    print("    - ESP32_SENSOR_001 in the 'Connected ESP Devices' section")
    print("    - Latest packets and hashes in the 'Latest Received Packets & Hashes' section")
    print()

if __name__ == "__main__":
    try:
        test_esp_provision()
    except requests.exceptions.ConnectionError:
        print("[-] Failed to connect to dashboard at http://localhost:5000")
        print("[*] Make sure the dashboard is running: python iot_integrated_dashboard.py")
    except Exception as e:
        print(f"[-] Error: {e}")
