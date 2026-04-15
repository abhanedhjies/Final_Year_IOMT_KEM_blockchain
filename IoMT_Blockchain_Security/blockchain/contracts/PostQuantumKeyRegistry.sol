// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PostQuantumKeyRegistry
 * @notice Smart contract for managing post-quantum cryptographic public keys
 *         with Role-Based Access Control (RBAC) for healthcare security.
 *
 * Access model:
 *   - Admin (deployer): full control — register providers, grant/revoke access,
 *                       assign devices to patients, deactivate keys
 *   - Healthcare Provider (Doctor / Nurse): can read device keys only for patients
 *                       they have been explicitly granted access to
 *   - No wallet / unregistered address: can only read public metadata
 */

contract PostQuantumKeyRegistry {

    // ─────────────────────────────────────────────────────────────────
    //  Roles & Admin
    // ─────────────────────────────────────────────────────────────────

    address public admin;

    modifier onlyAdmin() {
        require(msg.sender == admin, "ACCESS DENIED: Admin only");
        _;
    }

    // ─────────────────────────────────────────────────────────────────
    //  Structs
    // ─────────────────────────────────────────────────────────────────

    struct DeviceKey {
        address deviceOwner;
        bytes   kyberPublicKey;
        bytes   dilithiumPublicKey;
        uint256 registrationTime;
        bool    isActive;
        string  patientId;          // Patient this device belongs to
    }

    struct HealthcareProvider {
        string  name;
        string  role;               // e.g. "DOCTOR", "NURSE", "RADIOLOGIST"
        bool    isRegistered;       // false if revoked
        uint256 registeredAt;
    }

    // ─────────────────────────────────────────────────────────────────
    //  Storage
    // ─────────────────────────────────────────────────────────────────

    mapping(string  => DeviceKey)            public deviceKeys;
    mapping(address => HealthcareProvider)   public providers;
    // provider → patientId → hasAccess
    mapping(address => mapping(string => bool)) public accessPermissions;

    address[] private providerList;

    // ─────────────────────────────────────────────────────────────────
    //  Events
    // ─────────────────────────────────────────────────────────────────

    event KeyRegistered(string indexed deviceId, address indexed owner, uint256 timestamp);
    event KeyDeactivated(string indexed deviceId, uint256 timestamp);
    event DeviceAssignedToPatient(string indexed deviceId, string patientId, uint256 timestamp);

    event ProviderRegistered(address indexed providerAddr, string name, string role, uint256 timestamp);
    event ProviderRevoked(address indexed providerAddr, uint256 timestamp);

    event AccessGranted(address indexed providerAddr, string indexed patientId, address indexed grantedBy, uint256 timestamp);
    event AccessRevoked(address indexed providerAddr, string indexed patientId, address indexed revokedBy, uint256 timestamp);

    // ─────────────────────────────────────────────────────────────────
    //  Constructor
    // ─────────────────────────────────────────────────────────────────

    constructor() {
        admin = msg.sender;
    }

    // ─────────────────────────────────────────────────────────────────
    //  Admin: Provider Management
    // ─────────────────────────────────────────────────────────────────

    /**
     * @notice Register a new healthcare provider (admin only).
     * @param providerAddr Ethereum address of the provider's wallet
     * @param name         Full name of the provider
     * @param role         Role string — "DOCTOR", "NURSE", etc.
     */
    function registerProvider(
        address providerAddr,
        string  memory name,
        string  memory role
    ) public onlyAdmin {
        require(!providers[providerAddr].isRegistered, "Provider already registered");
        providers[providerAddr] = HealthcareProvider({
            name:         name,
            role:         role,
            isRegistered: true,
            registeredAt: block.timestamp
        });
        providerList.push(providerAddr);
        emit ProviderRegistered(providerAddr, name, role, block.timestamp);
    }

    /**
     * @notice Revoke a healthcare provider's registration (admin only).
     *         All their access permissions become invalid automatically
     *         because checkAccess verifies isRegistered first.
     */
    function revokeProvider(address providerAddr) public onlyAdmin {
        require(providers[providerAddr].isRegistered, "Provider not registered");
        providers[providerAddr].isRegistered = false;
        emit ProviderRevoked(providerAddr, block.timestamp);
    }

    // ─────────────────────────────────────────────────────────────────
    //  Admin: Per-Patient Access Control
    // ─────────────────────────────────────────────────────────────────

    /**
     * @notice Grant a registered provider access to a specific patient's data.
     */
    function grantAccess(address providerAddr, string memory patientId) public onlyAdmin {
        require(providers[providerAddr].isRegistered, "Provider is not registered");
        accessPermissions[providerAddr][patientId] = true;
        emit AccessGranted(providerAddr, patientId, msg.sender, block.timestamp);
    }

    /**
     * @notice Revoke a provider's access to a specific patient.
     */
    function revokeAccess(address providerAddr, string memory patientId) public onlyAdmin {
        accessPermissions[providerAddr][patientId] = false;
        emit AccessRevoked(providerAddr, patientId, msg.sender, block.timestamp);
    }

    /**
     * @notice Check whether a provider has active access to a patient.
     */
    function checkAccess(address providerAddr, string memory patientId) public view returns (bool) {
        if (!providers[providerAddr].isRegistered) return false;
        return accessPermissions[providerAddr][patientId];
    }

    // ─────────────────────────────────────────────────────────────────
    //  Admin: Device ↔ Patient Assignment
    // ─────────────────────────────────────────────────────────────────

    /**
     * @notice Assign an IoMT device to a patient ID (admin only).
     */
    function assignDeviceToPatient(
        string memory deviceId,
        string memory patientId
    ) public onlyAdmin {
        require(deviceKeys[deviceId].isActive, "Device not active or not registered");
        deviceKeys[deviceId].patientId = patientId;
        emit DeviceAssignedToPatient(deviceId, patientId, block.timestamp);
    }

    // ─────────────────────────────────────────────────────────────────
    //  Device Key Registration (gateway / device owner)
    // ─────────────────────────────────────────────────────────────────

    /**
     * @dev Register a device's post-quantum public keys.
     */
    function registerDeviceKey(
        string memory deviceId,
        bytes  memory kyberPublicKey,
        bytes  memory dilithiumPublicKey
    ) public {
        require(kyberPublicKey.length > 0,    "Kyber key cannot be empty");
        require(dilithiumPublicKey.length > 0, "Dilithium key cannot be empty");

        deviceKeys[deviceId] = DeviceKey({
            deviceOwner:       msg.sender,
            kyberPublicKey:    kyberPublicKey,
            dilithiumPublicKey: dilithiumPublicKey,
            registrationTime:  block.timestamp,
            isActive:          true,
            patientId:         ""
        });

        emit KeyRegistered(deviceId, msg.sender, block.timestamp);
    }

    // ─────────────────────────────────────────────────────────────────
    //  Access-Controlled Data Read
    // ─────────────────────────────────────────────────────────────────

    /**
     * @notice Retrieve full device key data.
     *         - Admin: always allowed.
     *         - Registered provider: allowed only if grantAccess was called
     *           for the patient this device is assigned to.
     *         - Anyone else: DENIED.
     */
    function getDeviceKey(string memory deviceId)
        public
        view
        returns (DeviceKey memory)
    {
        if (msg.sender == admin) {
            return deviceKeys[deviceId];
        }
        string memory patientId = deviceKeys[deviceId].patientId;
        require(
            bytes(patientId).length > 0,
            "ACCESS DENIED: Device not assigned to a patient"
        );
        require(
            checkAccess(msg.sender, patientId),
            "ACCESS DENIED: No permission for this patient"
        );
        return deviceKeys[deviceId];
    }

    /**
     * @notice Public metadata only — no sensitive key material returned.
     *         Safe to call from any address.
     */
    function getDevicePublicInfo(string memory deviceId)
        public
        view
        returns (address owner, uint256 registrationTime, bool active, string memory patientId)
    {
        DeviceKey memory dk = deviceKeys[deviceId];
        return (dk.deviceOwner, dk.registrationTime, dk.isActive, dk.patientId);
    }

    // ─────────────────────────────────────────────────────────────────
    //  Provider Info Queries
    // ─────────────────────────────────────────────────────────────────

    function getProvider(address providerAddr)
        public
        view
        returns (HealthcareProvider memory)
    {
        return providers[providerAddr];
    }

    function getProviderCount() public view returns (uint256) {
        return providerList.length;
    }

    function getProviderAt(uint256 index) public view returns (address) {
        require(index < providerList.length, "Index out of range");
        return providerList[index];
    }

    // ─────────────────────────────────────────────────────────────────
    //  Key Deactivation
    // ─────────────────────────────────────────────────────────────────

    /**
     * @dev Deactivate a device's key — admin or device owner only.
     */
    function deactivateKey(string memory deviceId) public {
        require(
            msg.sender == admin || deviceKeys[deviceId].deviceOwner == msg.sender,
            "Only admin or device owner can deactivate"
        );
        deviceKeys[deviceId].isActive = false;
        emit KeyDeactivated(deviceId, block.timestamp);
    }

    /**
     * @dev Check if a key is active.
     */
    function isKeyActive(string memory deviceId)
        public
        view
        returns (bool) 
    {
        return deviceKeys[deviceId].isActive;
    }
}
