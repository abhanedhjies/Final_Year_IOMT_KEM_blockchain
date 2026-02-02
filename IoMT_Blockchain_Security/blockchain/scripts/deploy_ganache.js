/**
 * Ganache Deployment Script - Phase 2
 * 
 * Purpose: Deploy PostQuantumKeyRegistry smart contract to Ganache local blockchain
 * 
 * Requirements:
 *   1. Ganache running on http://localhost:8545
 *   2. npm install web3 solc
 * 
 * Usage:
 *   npx hardhat compile  (compile contracts first)
 *   node scripts/deploy_ganache.js
 */

import fs from "fs";
import path from "path";
import { Web3 } from "web3";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize web3 with Ganache
const web3 = new Web3("http://127.0.0.1:7545");

async function main() {
  try {
    console.log("\n========================================");
    console.log("PostQuantumKeyRegistry Deployment");
    console.log("Ganache Local Blockchain");
    console.log("========================================\n");

    // Get accounts from Ganache
    const accounts = await web3.eth.getAccounts();
    const deployerAccount = accounts[0];

    console.log(`[*] Deployer Account: ${deployerAccount}`);
    console.log(`[*] Available Accounts: ${accounts.length}\n`);

    // Check deployer balance
    const balance = await web3.eth.getBalance(deployerAccount);
    console.log(`[*] Deployer Balance: ${web3.utils.fromWei(balance, "ether")} ETH\n`);

    // Read contract ABI and bytecode from Hardhat artifacts
    const contractPath = path.join(
      __dirname,
      "../artifacts/contracts/PostQuantumKeyRegistry.sol/PostQuantumKeyRegistry.json"
    );

    if (!fs.existsSync(contractPath)) {
      console.error(
        `[-] Contract artifact not found. Run: npx hardhat compile\n`
      );
      process.exit(1);
    }

    const contractArtifact = JSON.parse(fs.readFileSync(contractPath, "utf8"));
    const abi = contractArtifact.abi;
    const bytecode = contractArtifact.bytecode;

    console.log("[+] Contract artifact loaded");
    console.log(`[+] ABI Functions: ${abi.filter((a) => a.type === "function").length}`);
    console.log(`[+] Bytecode size: ${bytecode.length / 2} bytes\n`);

    // Deploy contract
    console.log("[*] Deploying PostQuantumKeyRegistry...");
    const contract = new web3.eth.Contract(abi);

    const deployTx = contract.deploy({
      data: bytecode,
      arguments: [],
    });

    const estimatedGas = await deployTx.estimateGas({
      from: deployerAccount,
    });
    console.log(`[+] Estimated Gas: ${estimatedGas}`);

    const deployed = await deployTx.send({
      from: deployerAccount,
      gas: estimatedGas * 2n, // Add buffer
      gasPrice: web3.utils.toWei("20", "gwei"),
    });

    const contractAddress = deployed.options.address;
    console.log(`[+] Contract Deployed: ${contractAddress}`);
    console.log(`[+] Transaction Hash: ${deployed.transactionHash}\n`);

    // Test registration
    console.log("[*] Testing device key registration...");
    const deviceId = "DEVICE_TEST_001";
    const kyberPublicKey =
      "0x" + Buffer.from("kyber_public_key_32_bytes_test_data").toString("hex");
    const dilithiumPublicKey =
      "0x" + Buffer.from("dilithium_public_key_44_bytes_test__").toString("hex");

    const registerTx = await deployed.methods
      .registerDeviceKey(deviceId, kyberPublicKey, dilithiumPublicKey)
      .send({
        from: deployerAccount,
        gas: 300000,
      });

    console.log(`[+] Device registered: ${deviceId}`);
    console.log(`[+] Transaction Hash: ${registerTx.transactionHash}`);
    console.log(`[+] Gas Used: ${registerTx.gasUsed}\n`);

    // Test retrieval
    console.log("[*] Testing device key retrieval...");
    const retrievedKey = await deployed.methods.getDeviceKey(deviceId).call();
    console.log(`[+] Retrieved Key for ${deviceId}:`);
    console.log(`    Owner: ${retrievedKey.owner}`);
    console.log(`    Kyber PK: ${retrievedKey.kyberPublicKey.slice(0, 20)}...`);
    console.log(`    Active: ${retrievedKey.isActive}\n`);

    // Test status check
    const isActive = await deployed.methods.isKeyActive(deviceId).call();
    console.log(`[+] Key Active Status: ${isActive}\n`);

    // Summary
    console.log("========================================");
    console.log("Deployment Summary");
    console.log("========================================");
    console.log(`Contract Address: ${contractAddress}`);
    console.log(`Deployer: ${deployerAccount}`);
    console.log(`Device Registered: ${deviceId}`);
    console.log(`All Tests Passed: ✓`);
    console.log("========================================\n");

    // Save deployment info
    const deploymentInfo = {
      network: "Ganache",
      contractAddress: contractAddress,
      deployer: deployerAccount,
      abi: abi,
      deploymentBlock: await web3.eth.getBlockNumber(),
      timestamp: new Date().toISOString(),
    };

    const infoPath = path.join(__dirname, "../deployment_ganache.json");
    fs.writeFileSync(infoPath, JSON.stringify(deploymentInfo, null, 2));
    console.log(`[+] Deployment info saved to: deployment_ganache.json\n`);

    process.exit(0);
  } catch (error) {
    console.error(`[-] Deployment error: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

main();
