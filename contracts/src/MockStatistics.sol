// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MockStatistics
 * @dev Mock implementation of IStatistics for testing/arena environments.
 * All functions are no-ops since metrics are tracked in Python.
 */
contract MockStatistics {
    function saveNewLevel(address level) external {
        // No-op: metrics tracked in Python
    }

    function createNewInstance(address instance, address level, address player) external {
        // No-op: metrics tracked in Python
    }

    function submitFailure(address instance, address level, address player) external {
        // No-op: metrics tracked in Python
    }

    function submitSuccess(address instance, address level, address player) external {
        // No-op: metrics tracked in Python
    }
}
