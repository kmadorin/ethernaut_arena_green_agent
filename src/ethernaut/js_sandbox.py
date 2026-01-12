"""Python wrapper for JavaScript sandbox subprocess."""

import asyncio
import subprocess
import json
from pathlib import Path
from loguru import logger


class JSSandbox:
    """Wrapper for Node.js JavaScript sandbox subprocess."""

    def __init__(self):
        """Initialize JSSandbox."""
        self.process: subprocess.Popen | None = None
        self.sandbox_dir = Path(__file__).parent.parent.parent / "js_sandbox"

    async def start(self, rpc_url: str, contracts: dict, player_key: str) -> None:
        """Start the Node.js sandbox process and initialize it.

        Args:
            rpc_url: Ethereum RPC URL (e.g., http://127.0.0.1:8545)
            contracts: Dictionary with ethernaut contract details
            player_key: Player's private key

        Raises:
            RuntimeError: If sandbox fails to start
        """
        try:
            # Start Node.js subprocess
            self.process = subprocess.Popen(
                ["node", "sandbox.js"],
                cwd=self.sandbox_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            logger.info(f"JS Sandbox process started with PID {self.process.pid}")

            # Send init command
            init_response = await self.send_command(
                {
                    "command": "init",
                    "config": {
                        "rpcUrl": rpc_url,
                        "playerPrivateKey": player_key,
                        "ethernautAddress": contracts["ethernaut_address"],
                        "ethernautAbi": contracts["ethernaut_abi"],
                    },
                }
            )

            if not init_response.get("success"):
                raise RuntimeError(
                    f"Failed to initialize sandbox: {init_response.get('error')}"
                )

            logger.info("JS Sandbox initialized successfully")

        except FileNotFoundError as e:
            logger.error(f"Node.js or sandbox.js not found: {e}")
            raise RuntimeError(f"Failed to start sandbox: {e}")
        except Exception as e:
            logger.error(f"Failed to start sandbox: {e}")
            if self.process:
                self.process.terminate()
            raise

    async def send_command(self, command: dict, timeout: float = 10.0) -> dict:
        """Send a command to the sandbox and receive response.

        Args:
            command: Command dictionary (command, code, address, abi, etc.)
            timeout: Timeout in seconds

        Returns:
            Response dictionary from sandbox

        Raises:
            TimeoutError: If command times out
            RuntimeError: If sandbox is not running
        """
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Sandbox process not running")

        try:
            # Write command to stdin
            command_json = json.dumps(command) + "\n"
            self.process.stdin.write(command_json)
            self.process.stdin.flush()

            # Log JavaScript code for exec commands
            if command.get('command') == 'exec':
                code = command.get('code', '')
                logger.info(f"Executing JS: {code}")
            logger.debug(f"Sent command: {command.get('command')}")

            # Read response from stdout with timeout
            async def read_line():
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.process.stdout.readline)

            response_line = await asyncio.wait_for(read_line(), timeout=timeout)

            if not response_line:
                raise RuntimeError("Sandbox closed unexpectedly")

            # Log raw response before parsing (helps debug parsing errors)
            logger.debug(f"Raw sandbox response: {response_line.strip()[:300]}")

            response = json.loads(response_line)
            # Enhanced logging with result preview
            result_preview = str(response.get('result', ''))[:100]
            logger.debug(f"Received response: success={response.get('success')}, result={result_preview}")

            return response

        except asyncio.TimeoutError:
            logger.error(f"Sandbox command timed out after {timeout}s")
            return {"success": False, "error": f"Timeout after {timeout}s"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sandbox response: {e}")
            # Log what we tried to parse to help debug
            try:
                logger.error(f"Raw response that failed to parse: {response_line[:200]}")
            except:
                pass
            return {"success": False, "error": f"Invalid response: {e}"}
        except Exception as e:
            logger.error(f"Error sending command to sandbox: {e}")
            return {"success": False, "error": str(e)}

    async def exec_code(self, code: str) -> dict:
        """Execute JavaScript code in the sandbox.

        Args:
            code: JavaScript code to execute

        Returns:
            Response dictionary with success and result/error
        """
        return await self.send_command({"command": "exec", "code": code})

    async def set_contract(self, address: str, abi: list) -> dict:
        """Set the current contract instance in the sandbox.

        Args:
            address: Contract address
            abi: Contract ABI

        Returns:
            Response dictionary with success status
        """
        return await self.send_command(
            {"command": "set_contract", "address": address, "abi": abi}
        )

    async def stop(self) -> None:
        """Stop the sandbox process gracefully.

        Terminates the process and waits for it to exit.
        If still running after timeout, kills it forcefully.
        """
        if not self.process:
            logger.debug("Sandbox process not running")
            return

        try:
            logger.info(f"Stopping JS Sandbox process (PID {self.process.pid})")

            # Close stdin to signal shutdown
            if self.process.stdin:
                self.process.stdin.close()

            # Terminate gracefully
            self.process.terminate()

            # Wait for process to exit
            try:
                self.process.wait(timeout=5)
                logger.info("JS Sandbox process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("JS Sandbox did not terminate, killing forcefully")
                self.process.kill()
                self.process.wait(timeout=2)
                logger.info("JS Sandbox process killed")

        except Exception as e:
            logger.error(f"Error stopping sandbox: {e}")

        finally:
            self.process = None
