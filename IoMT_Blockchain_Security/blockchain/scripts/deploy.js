/**
 * Hardhat Deployment Script - Phase 2
 * 
 * Purpose: Deploy PostQuantumKeyRegistry smart contract to blockchain
 * 
 * Network: Hardhat (local) or Ganache (local testnet)
 * 
 * Usage:
 *   npx hardhat run scripts/deploy.js              (Hardhat network)
 *   npx hardhat run scripts/deploy.js --network ganache  (Ganache network)
 */

import hre from "hardhat";

async function main() {
  console.log("\n========================================");
  console.log("PostQuantumKeyRegistry Deployment");
  console.log("========================================\n");

  // Get the contract factory
  const PostQuantumKeyRegistry = await hre.ethers.getContractFactory("PostQuantumKeyRegistry");

  // Get deployment account
  const [deployer] = await hre.ethers.getSigners();
  console.log(`[*] Deploying contract with account: ${deployer.address}`);
  console.log(`[*] Account balance: ${(await deployer.getBalance()).toString()}`);

  // Deploy the contract
  console.log("\n[*] Deploying PostQuantumKeyRegistry...");
  const contract = await PostQuantumKeyRegistry.deploy();
  
  // Wait for deployment to finish
  await contract.deployed();

  console.log(`\n[+] Contract deployed successfully!`);
  console.log(`[+] Contract address: ${contract.address}`);
  console.log(`[+] Network: ${hre.network.name}`);

  // Get contract details
  const deploymentTx = contract.deployTransaction;
  console.log(`[+] Deployment transaction: ${deploymentTx.hash}`);
  console.log(`[+] Block number: ${deploymentTx.blockNumber}`);

  // Save deployment info
  const deploymentInfo = {
    contractName: "PostQuantumKeyRegistry",
    address: contract.address,
    deployer: deployer.address,
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    transactionHash: deploymentTx.hash,
    blockNumber: deploymentTx.blockNumber
  };

  console.log("\n[*] Deployment Information:");
  console.log(JSON.stringify(deploymentInfo, null, 2));

  // Test the contract with a sample device
  console.log("\n========================================");
  console.log("Testing Contract Functions");
  console.log("========================================\n");

  try {
    // Create sample data
    const deviceId = "DEVICE_TEST_001";
    const kyberPublicKey = "0x" + Buffer.from("kyber_public_key_test_data_1234567890123456").toString("hex");
    const dilithiumPublicKey = "0x" + Buffer.from("dilithium_public_key_test_data_1234567890").toString("hex");

    // Register a device key
    console.log(`[*] Registering device: ${deviceId}`);
    const tx = await contract.registerDeviceKey(deviceId, kyberPublicKey, dilithiumPublicKey);
    await tx.wait();
    console.log(`[+] Device registered successfully`);
    console.log(`[+] Transaction: ${tx.hash}`);

    // Retrieve the device key
    console.log(`\n[*] Retrieving device key...`);
    const deviceKey = await contract.getDeviceKey(deviceId);
    console.log(`[+] Device Owner: ${deviceKey.deviceOwner}`);
    console.log(`[+] Kyber PK (first 32 chars): ${deviceKey.kyberPublicKey.substring(0, 32)}...`);
    console.log(`[+] Registration Time: ${new Date(deviceKey.registrationTime * 1000).toISOString()}`);
    console.log(`[+] Is Active: ${deviceKey.isActive}`);

    // Check if key is active
    console.log(`\n[*] Checking if key is active...`);
    const isActive = await contract.isKeyActive(deviceId);
    console.log(`[+] Key is active: ${isActive}`);

  } catch (error) {
    console.log(`[-] Test failed: ${error.message}`);
  }

  console.log("\n========================================");
  console.log("Deployment Complete");
  console.log("========================================\n");

  return deploymentInfo;
}

main()
  .then((info) => {
    process.exit(0);
  })
  .catch((error) => {
    console.error(`[-] Deployment failed: ${error}`);
    process.exit(1);
  });
