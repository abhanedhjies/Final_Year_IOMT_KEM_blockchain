// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PostQuantumKeyRegistry
 * @notice Smart contract for managing post-quantum cryptographic public keys
 * @dev This contract stores device public keys (Kyber, Dilithium) on-chain
 * 
 * Phase 1: Basic key registration and retrieval
 * Phase 2: Key rotation and expiration logic
 * Phase 3: Integration with device authentication
 */

contract PostQuantumKeyRegistry {
    
    // Structure to store device key information
    struct DeviceKey {
        address deviceOwner;        // Owner of the device
        bytes kyberPublicKey;       // Kyber (KEM) public key
        bytes dilithiumPublicKey;   // Dilithium (signature) public key
        uint256 registrationTime;   // Timestamp of registration
        bool isActive;              // Key activation status
    }

    // Mapping: device_id => DeviceKey
    mapping(string => DeviceKey) public deviceKeys;

    // Event: Key Registration
    event KeyRegistered(
        string indexed deviceId,
        address indexed owner,
        uint256 timestamp
    );

    // Event: Key Deactivation
    event KeyDeactivated(
        string indexed deviceId,
        uint256 timestamp
    );

    /**
     * @dev Register a device's post-quantum public keys
     * @param deviceId Unique identifier for the device
     * @param kyberPublicKey Kyber public key (bytes)
     * @param dilithiumPublicKey Dilithium public key (bytes)
     */
    function registerDeviceKey(
        string memory deviceId,
        bytes memory kyberPublicKey,
        bytes memory dilithiumPublicKey
    ) public {
        require(kyberPublicKey.length > 0, "Kyber key cannot be empty");
        require(dilithiumPublicKey.length > 0, "Dilithium key cannot be empty");

        deviceKeys[deviceId] = DeviceKey({
            deviceOwner: msg.sender,
            kyberPublicKey: kyberPublicKey,
            dilithiumPublicKey: dilithiumPublicKey,
            registrationTime: block.timestamp,
            isActive: true
        });

        emit KeyRegistered(deviceId, msg.sender, block.timestamp);
    }

    /**
     * @dev Retrieve device keys
     * @param deviceId Device identifier
     * @return Device key structure
     */
    function getDeviceKey(string memory deviceId) 
        public 
        view 
        returns (DeviceKey memory) 
    {
        return deviceKeys[deviceId];
    }

    /**
     * @dev Deactivate a device's key
     * @param deviceId Device identifier
     */
    function deactivateKey(string memory deviceId) public {
        require(
            deviceKeys[deviceId].deviceOwner == msg.sender,
            "Only device owner can deactivate"
        );
        deviceKeys[deviceId].isActive = false;
        emit KeyDeactivated(deviceId, block.timestamp);
    }

    /**
     * @dev Check if a key is active
     * @param deviceId Device identifier
     * @return Boolean indicating if key is active
     */
    function isKeyActive(string memory deviceId) 
        public 
        view 
        returns (bool) 
    {
        return deviceKeys[deviceId].isActive;
    }
}
