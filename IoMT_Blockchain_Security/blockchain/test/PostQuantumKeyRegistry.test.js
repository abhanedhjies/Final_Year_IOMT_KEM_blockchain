/**
 * Smart Contract Tests - Phase 2
 * 
 * Tests for PostQuantumKeyRegistry contract
 * 
 * Framework: Hardhat + Chai + Ethers.js
 * 
 * Run with: npx hardhat test
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PostQuantumKeyRegistry", function () {
  let contract;
  let owner;
  let addr1;
  let addr2;

  // Sample test data
  const DEVICE_ID = "DEVICE_TEST_001";
  const DEVICE_ID_2 = "DEVICE_TEST_002";
  const KYBER_PUBLIC_KEY = "0x" + Buffer.from("kyber_public_key_test_data_1234567890123456").toString("hex");
  const KYBER_PUBLIC_KEY_2 = "0x" + Buffer.from("kyber_public_key_test_data_9999999999999999").toString("hex");
  const DILITHIUM_PUBLIC_KEY = "0x" + Buffer.from("dilithium_public_key_test_data_1234567890").toString("hex");
  const DILITHIUM_PUBLIC_KEY_2 = "0x" + Buffer.from("dilithium_public_key_test_data_9999999999").toString("hex");

  beforeEach(async function () {
    // Get signers
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy contract
    const PostQuantumKeyRegistry = await ethers.getContractFactory("PostQuantumKeyRegistry");
    contract = await PostQuantumKeyRegistry.deploy();
    await contract.deployed();
  });

  describe("Device Key Registration", function () {
    it("Should register a device key successfully", async function () {
      const tx = await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
      
      // Verify transaction
      const receipt = await tx.wait();
      expect(receipt.status).to.equal(1);

      // Verify device was registered
      const deviceKey = await contract.getDeviceKey(DEVICE_ID);
      expect(deviceKey.deviceOwner).to.equal(owner.address);
      expect(deviceKey.isActive).to.be.true;
    });

    it("Should reject empty Kyber key", async function () {
      await expect(
        contract.registerDeviceKey(DEVICE_ID, "0x", DILITHIUM_PUBLIC_KEY)
      ).to.be.revertedWith("Kyber key cannot be empty");
    });

    it("Should reject empty Dilithium key", async function () {
      await expect(
        contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, "0x")
      ).to.be.revertedWith("Dilithium key cannot be empty");
    });

    it("Should register multiple devices", async function () {
      // Register first device
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);

      // Register second device
      const tx = await contract.registerDeviceKey(DEVICE_ID_2, KYBER_PUBLIC_KEY_2, DILITHIUM_PUBLIC_KEY_2);
      await tx.wait();

      // Verify both devices exist
      const device1 = await contract.getDeviceKey(DEVICE_ID);
      const device2 = await contract.getDeviceKey(DEVICE_ID_2);

      expect(device1.isActive).to.be.true;
      expect(device2.isActive).to.be.true;
    });

    it("Should emit KeyRegistered event", async function () {
      await expect(contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY))
        .to.emit(contract, "KeyRegistered")
        .withArgs(DEVICE_ID, owner.address);
    });
  });

  describe("Device Key Retrieval", function () {
    beforeEach(async function () {
      // Register a device before testing retrieval
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
    });

    it("Should retrieve device key information", async function () {
      const deviceKey = await contract.getDeviceKey(DEVICE_ID);

      expect(deviceKey.deviceOwner).to.equal(owner.address);
      expect(deviceKey.kyberPublicKey).to.equal(KYBER_PUBLIC_KEY);
      expect(deviceKey.dilithiumPublicKey).to.equal(DILITHIUM_PUBLIC_KEY);
      expect(deviceKey.isActive).to.be.true;
    });

    it("Should have correct registration timestamp", async function () {
      const blockNumber = await ethers.provider.getBlockNumber();
      const block = await ethers.provider.getBlock(blockNumber);

      const deviceKey = await contract.getDeviceKey(DEVICE_ID);
      expect(deviceKey.registrationTime).to.equal(block.timestamp);
    });

    it("Should retrieve non-existent device", async function () {
      const deviceKey = await contract.getDeviceKey("NONEXISTENT_DEVICE");
      
      // Device should have default values
      expect(deviceKey.isActive).to.be.false;
    });
  });

  describe("Key Activation/Deactivation", function () {
    beforeEach(async function () {
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
    });

    it("Should deactivate a device key", async function () {
      // Verify key is active
      let isActive = await contract.isKeyActive(DEVICE_ID);
      expect(isActive).to.be.true;

      // Deactivate
      const tx = await contract.deactivateKey(DEVICE_ID);
      await tx.wait();

      // Verify key is deactivated
      isActive = await contract.isKeyActive(DEVICE_ID);
      expect(isActive).to.be.false;
    });

    it("Should only allow owner to deactivate", async function () {
      // Try to deactivate from different account
      await expect(contract.connect(addr1).deactivateKey(DEVICE_ID))
        .to.be.revertedWith("Only device owner can deactivate");
    });

    it("Should emit KeyDeactivated event", async function () {
      await expect(contract.deactivateKey(DEVICE_ID))
        .to.emit(contract, "KeyDeactivated")
        .withArgs(DEVICE_ID);
    });

    it("Should check if key is active", async function () {
      // Active key
      let isActive = await contract.isKeyActive(DEVICE_ID);
      expect(isActive).to.be.true;

      // After deactivation
      await contract.deactivateKey(DEVICE_ID);
      isActive = await contract.isKeyActive(DEVICE_ID);
      expect(isActive).to.be.false;
    });
  });

  describe("Multiple Users", function () {
    it("Should track owner of each device correctly", async function () {
      // Owner registers device
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);

      // Address1 registers different device
      await contract.connect(addr1).registerDeviceKey(DEVICE_ID_2, KYBER_PUBLIC_KEY_2, DILITHIUM_PUBLIC_KEY_2);

      // Verify owners
      const device1 = await contract.getDeviceKey(DEVICE_ID);
      const device2 = await contract.getDeviceKey(DEVICE_ID_2);

      expect(device1.deviceOwner).to.equal(owner.address);
      expect(device2.deviceOwner).to.equal(addr1.address);
    });

    it("Each user can only deactivate their own devices", async function () {
      // Register devices with different owners
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
      await contract.connect(addr1).registerDeviceKey(DEVICE_ID_2, KYBER_PUBLIC_KEY_2, DILITHIUM_PUBLIC_KEY_2);

      // Owner can deactivate their own device
      await expect(contract.deactivateKey(DEVICE_ID)).to.not.be.reverted;

      // Owner cannot deactivate addr1's device
      await expect(contract.deactivateKey(DEVICE_ID_2))
        .to.be.revertedWith("Only device owner can deactivate");
    });
  });

  describe("Gas Efficiency", function () {
    it("Should consume reasonable gas for registration", async function () {
      const tx = await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
      const receipt = await tx.wait();

      console.log(`    Gas used for registerDeviceKey: ${receipt.gasUsed}`);
      // Gas should be reasonable (< 200k for registration)
      expect(receipt.gasUsed).to.be.lt(200000);
    });

    it("Should consume minimal gas for key retrieval", async function () {
      await contract.registerDeviceKey(DEVICE_ID, KYBER_PUBLIC_KEY, DILITHIUM_PUBLIC_KEY);
      
      const tx = await contract.isKeyActive(DEVICE_ID);
      console.log(`    Gas used for isKeyActive (view): No gas (view function)`);
      
      // View functions don't consume gas
      expect(tx).to.be.true;
    });
  });
});
