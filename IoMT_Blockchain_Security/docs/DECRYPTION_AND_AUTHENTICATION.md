# Decryption and Blockchain-based Device Authentication

This page documents how decryption is performed in the codebase and how device authentication is anchored using the on-chain `PostQuantumKeyRegistry`.

**Where to look in code**
- Device-side and gateway authentication and KEM logic: [IoMT_Blockchain_Security/blockchain/auth_protocol.py](IoMT_Blockchain_Security/blockchain/auth_protocol.py#L1-L300)
- On-chain key registry smart contract: [IoMT_Blockchain_Security/blockchain/contracts/PostQuantumKeyRegistry.sol](IoMT_Blockchain_Security/blockchain/contracts/PostQuantumKeyRegistry.sol#L1-L200)

**Summary (high-level)**
- The gateway and device perform a simplified KEM-based authentication (encapsulate/decapsulate) to derive a shared secret.
- The gateway registers or looks up the device's public keys on the `PostQuantumKeyRegistry` smart contract to confirm the device identity and key status.
- Once the shared secret is derived, both sides create a session key and authenticate messages using HMAC + AES encryption.

Decryption and session flow (code location)
- The main session class is `DeviceAuthenticationSession` in `auth_protocol.py`.
  - `start_authentication(device_public_key)` (gateway): performs KEM encapsulation and returns a `ciphertext` and a `commitment` derived from the shared secret.
  - `AuthenticationProtocol.decapsulate(private_key, ciphertext, public_key)` (device): recovers the same shared secret from the received `ciphertext`.
  - `verify_authentication(device_commitment)` (gateway): gateway verifies the device's commitment matches its shared secret and derives the `session_key`.
  - `encrypt_message(...)` and `decrypt_message(...)` (session): encrypt/decrypt using AES-CBC + HMAC for integrity.

Decryption details
- The gateway and device derive a 256-bit shared secret using a hash over ephemeral and public key material.
- The session key is derived with HMAC over the shared secret and `session_id` via `create_session_key()`.
- Decryption method (in `DeviceAuthenticationSession`) expects `iv_hex`, `ciphertext_hex`, and `hmac_hex`:
  1. Convert hex values back to bytes.
  2. Verify HMAC over the ciphertext using the session key; abort if mismatch.
  3. Decrypt using AES-CBC with the session key and IV.
  4. Unpad and return plaintext.

Where blockchain fits in (device authentication)
- `PostQuantumKeyRegistry` stores device public keys on-chain: `registerDeviceKey(deviceId, kyberPublicKey, dilithiumPublicKey)` and retrieval via `getDeviceKey(deviceId)`.
- Typical gateway behavior (conceptual):
  1. On device onboarding, the device owner (or gateway operator) calls `registerDeviceKey` on-chain with the device ID and its public keys.
  2. Before starting an authentication session, the gateway can call `getDeviceKey(deviceId)` and/or `isKeyActive(deviceId)` to verify the device's public key and active status.
  3. The gateway uses the on-chain `kyberPublicKey` (or the one supplied by the device) to run `encapsulate()` and start the protocol.

Example pseudo-code (gateway side, using Web3.py)

```python
# assume web3 is configured and contract is loaded
registry = web3.eth.contract(address=DEPLOYED_ADDRESS, abi=ABI)
device_info = registry.functions.getDeviceKey(device_id).call()
if not device_info[4]:
    raise Exception("Device key is deactivated")
kyber_public_key = device_info[1]  # bytes

# proceed with authentication using kyber_public_key
session = DeviceAuthenticationSession(device_id, gateway_id)
response = session.start_authentication(kyber_public_key)
# send response['ciphertext'] to device
```

Notes and limitations
- The implemented KEM and key derivation in `auth_protocol.py` are simplified and aimed for demonstration. For production use, replace with a vetted post-quantum library (for example, `liboqs`/Kyber or equivalent) and use proper KDF and AEAD primitives (e.g., AES-GCM or an AEAD construction).
- On-chain registry stores public keys and activation state. The gateway must ensure on-chain key retrieval and local trust checks are part of the authentication flow.

Further reading and references
- See `auth_protocol.py` for step-by-step demo flow and example usage (generate keys, start session, encapsulate/decapsulate, encrypt/decrypt).
- See `PostQuantumKeyRegistry.sol` for on-chain storage and retrieval of device keys.

