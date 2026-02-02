/**
 * Hardhat Configuration for IoMT Blockchain Security Project
 * 
 * Purpose: Configure Hardhat for development and testing of smart contracts
 * Network: Local Ethereum (Hardhat network) and Ganache for integration testing
 */

require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    // Local Hardhat network (default)
    hardhat: {
      chainId: 1337,
      accounts: {
        mnemonic: "test test test test test test test test test test test junk",
        count: 20,
      },
    },

    // Ganache local blockchain (for integration testing)
    ganache: {
      url: "http://127.0.0.1:7545",
      chainId: 1337,
      accounts: [
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb476caded732d6d3946a7ec88c60",
      ],
    },
  },

  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },

  mocha: {
    timeout: 40000,
  },
};
