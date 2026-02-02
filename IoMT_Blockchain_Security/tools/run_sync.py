import urllib.request
import json

BASE = 'http://127.0.0.1:5000'

def post_sync():
    url = f"{BASE}/api/sync-blockchain-details"
    req = urllib.request.Request(url, data=b'{}', headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=10) as r:
        print('SYNC STATUS:', r.status)
        print(r.read().decode())

def get_stored():
    url = f"{BASE}/api/stored-devices"
    with urllib.request.urlopen(url, timeout=10) as r:
        print('STORED DEVICES STATUS:', r.status)
        print(r.read().decode())

def get_details(device_id):
    url = f"{BASE}/api/encryption-details/{device_id}"
    with urllib.request.urlopen(url, timeout=10) as r:
        print('DETAILS STATUS:', r.status)
        print(r.read().decode())

if __name__ == '__main__':
    try:
        post_sync()
    except Exception as e:
        print('SYNC ERROR:', e)
    try:
        get_stored()
    except Exception as e:
        print('STORED ERROR:', e)
    try:
        get_details('DEVICE_TEST_001')
    except Exception as e:
        print('DETAILS ERROR:', e)
