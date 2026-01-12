const ethers = require("ethers");
const readline = require("readline");

// Global context (persistent across commands)
let provider;
let wallet;
let player;
let ethernaut;
let contract;

// ============================================================================
// Console capture mechanism
// ============================================================================

// Store captured console output
let capturedLogs = [];

// Save original console methods (for IPC communication)
const originalConsole = {
  log: console.log.bind(console),
  error: console.error.bind(console),
  warn: console.warn.bind(console),
  info: console.info.bind(console),
};

// Override console methods to capture output during user code execution
const userConsole = {
  log: (...args) => {
    capturedLogs.push({ level: 'log', message: args.map(String).join(' ') });
  },
  error: (...args) => {
    capturedLogs.push({ level: 'error', message: args.map(String).join(' ') });
  },
  warn: (...args) => {
    capturedLogs.push({ level: 'warn', message: args.map(String).join(' ') });
  },
  info: (...args) => {
    capturedLogs.push({ level: 'info', message: args.map(String).join(' ') });
  },
};

// ============================================================================
// Helper functions matching original Ethernaut browser console API
// These mirror the functions available via window.help() in the original game
// ============================================================================

/**
 * Get ETH balance of an address in ether (not wei).
 * Mirrors: window.getBalance(address) from original Ethernaut
 * @param {string} address - Ethereum address to check
 * @returns {Promise<string>} - Balance in ether as string
 */
const getBalance = async (address) => {
  const balance = await provider.getBalance(address);
  return ethers.formatEther(balance);
};

/**
 * Get current blockchain block number.
 * Mirrors: window.getBlockNumber() from original Ethernaut
 * @returns {Promise<number>} - Current block number
 */
const getBlockNumber = async () => {
  return await provider.getBlockNumber();
};

/**
 * Send a raw transaction.
 * Mirrors: window.sendTransaction({options}) from original Ethernaut
 * Note: 'from' field is ignored since wallet is pre-configured
 * @param {Object} options - Transaction options {to, value, data, gas, gasPrice}
 * @returns {Promise<Object>} - Transaction response
 */
const sendTransaction = async (options) => {
  // Mirror web3.js API: {from, to, value, data, gas, gasPrice}
  // The 'from' is ignored since wallet is already configured
  return await wallet.sendTransaction(options);
};

/**
 * Get network/chain ID.
 * Mirrors: window.getNetworkId() from original Ethernaut
 * @returns {Promise<bigint>} - Chain ID
 */
const getNetworkId = async () => {
  const network = await provider.getNetwork();
  return network.chainId;
};

/**
 * Convert ether units to wei.
 * Mirrors: window.toWei(ether) from original Ethernaut
 * @param {string|number} ether - Amount in ether
 * @returns {bigint} - Amount in wei
 */
const toWei = (ether) => {
  return ethers.parseEther(ether.toString());
};

/**
 * Convert wei units to ether.
 * Mirrors: window.fromWei(wei) from original Ethernaut
 * @param {bigint|string|number} wei - Amount in wei
 * @returns {string} - Amount in ether
 */
const fromWei = (wei) => {
  return ethers.formatEther(wei);
};

/**
 * Initialize the sandbox with blockchain configuration.
 * @param {Object} config - Configuration object with rpcUrl, playerPrivateKey, ethernautAddress, ethernautAbi
 * @returns {Promise<Object>} - {success: true} or {success: false, error: message}
 */
async function initialize(config) {
  try {
    // Create provider
    provider = new ethers.JsonRpcProvider(config.rpcUrl);

    // Create wallet from private key
    wallet = new ethers.Wallet(config.playerPrivateKey, provider);

    // Set player address
    player = wallet.address;

    // Create ethernaut contract instance
    ethernaut = new ethers.Contract(
      config.ethernautAddress,
      config.ethernautAbi,
      wallet,
    );

    // Initialize contract to undefined (will be set by set_contract)
    contract = undefined;

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Execute JavaScript code in the persistent context with timeout.
 * @param {string} code - JavaScript code to execute
 * @returns {Promise<Object>} - {success: true, result: string, logs: array} or {success: false, error: message, logs: array}
 */
async function executeCode(code) {
  const timeoutMs = 5000; // 5 seconds

  // Clear captured logs from previous execution
  capturedLogs = [];

  // Replace console with capturing version
  console.log = userConsole.log;
  console.error = userConsole.error;
  console.warn = userConsole.warn;
  console.info = userConsole.info;

  try {
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Execution timeout (5s)")), timeoutMs),
    );

    // Create execution promise
    const execPromise = (async () => {
      let result;

      // Strategy: Try with return() first (captures expression values like "await contract.owner()")
      // If syntax error (due to ; or const/let), fall back to no-return (supports multi-statement)
      try {
        result = await eval(`(async () => { return (${code}) })()`);
      } catch (e) {
        // If syntax error (likely due to ; or const/let), try without return wrapper
        if (e instanceof SyntaxError) {
          result = await eval(`(async () => { ${code} })()`);
        } else {
          throw e; // Re-throw non-syntax errors (e.g., runtime errors)
        }
      }

      // Convert result to string, handling objects and BigInts properly
      if (result === null || result === undefined) {
        return String(result);
      }
      if (typeof result === 'object') {
        // For objects, use JSON.stringify with BigInt support
        return JSON.stringify(result, (key, value) =>
          typeof value === 'bigint' ? value.toString() : value
        );
      }
      return String(result);
    })();

    // Race between execution and timeout
    const resultStr = await Promise.race([execPromise, timeoutPromise]);

    // Don't restore console - keep capturing version active for async callbacks
    // IPC uses originalConsole directly to avoid interference

    // Truncate if too long
    if (resultStr.length > 10000) {
      return {
        success: true,
        result: resultStr.substring(0, 9990) + "... (truncated)",
        logs: capturedLogs,
      };
    }

    return {
      success: true,
      result: resultStr,
      logs: capturedLogs,
    };
  } catch (error) {
    // Don't restore console - keep capturing version active for async callbacks
    // IPC uses originalConsole directly to avoid interference

    return {
      success: false,
      error: error.message,
      logs: capturedLogs,
    };
  }
}

/**
 * Set the current contract instance.
 * @param {string} address - Contract address
 * @param {Array} abi - Contract ABI
 * @returns {Object} - {success: true} or {success: false, error: message}
 */
function setContract(address, abi) {
  try {
    // Create contract instance with wallet as signer
    contract = new ethers.Contract(address, abi, wallet);

    // Add compatibility properties to match original Ethernaut browser console API
    // In ethers.js v6, .address was replaced with .target
    // The original Ethernaut uses web3.js/Truffle which has .address
    Object.defineProperty(contract, 'address', {
      get: function() { return this.target; },
      enumerable: true,
      configurable: true
    });

    // Add abi property for compatibility
    Object.defineProperty(contract, 'abi', {
      get: function() { return abi; },
      enumerable: true,
      configurable: true
    });

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Main IPC loop
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

rl.on("line", async (line) => {
  try {
    const msg = JSON.parse(line);
    let response;

    switch (msg.command) {
      case "init":
        response = await initialize(msg.config);
        break;
      case "exec":
        response = await executeCode(msg.code);
        break;
      case "set_contract":
        response = setContract(msg.address, msg.abi);
        break;
      default:
        response = { success: false, error: "Unknown command" };
    }

    // Use originalConsole for IPC to avoid interference with user console capture
    originalConsole.log(JSON.stringify(response));
  } catch (error) {
    originalConsole.log(
      JSON.stringify({
        success: false,
        error: error.message,
      }),
    );
  }
});

// Handle uncaught errors
process.on("uncaughtException", (error) => {
  originalConsole.log(
    JSON.stringify({
      success: false,
      error: `Uncaught: ${error.message}`,
    }),
  );
});

process.on("unhandledRejection", (error) => {
  originalConsole.log(
    JSON.stringify({
      success: false,
      error: `Unhandled rejection: ${error.message}`,
    }),
  );
});
