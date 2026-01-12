# Ethernaut Arena Green Agent

A green agent (evaluator) for the [AgentBeats](https://agentbeats.dev) platform that evaluates AI agents on [Ethernaut](https://ethernaut.openzeppelin.com/) smart contract security challenges.

## Overview

This green agent orchestrates evaluations of purple agents (AI solvers) across 41 Ethernaut challenge levels (0-40). It:

- Deploys a local Anvil blockchain with Ethernaut contracts
- Provides tools for agents to interact with smart contracts
- Tracks metrics (success rate, turns, errors)
- Returns structured evaluation results

## Project Structure

```
src/
├── server.py              # A2A server entry point
├── agentbeats/            # AgentBeats framework
│   ├── green_executor.py  # GreenAgent base class & executor
│   ├── models.py          # EvalRequest/EvalResult models
│   ├── tool_provider.py   # Agent communication & tools
│   └── client.py          # A2A client utilities
├── ethernaut/             # Ethernaut evaluator
│   ├── evaluator.py       # Main EthernautEvaluator class
│   ├── anvil_manager.py   # Anvil blockchain management
│   ├── js_sandbox.py      # JavaScript console (ethers.js)
│   ├── metrics.py         # Evaluation metrics tracking
│   └── levels/            # 41 level configurations
└── messenger.py           # A2A messaging utilities

contracts/                 # Solidity contracts (Foundry)
├── src/                   # Contract source files
├── lib/                   # Dependencies (git submodules)
│   ├── forge-std/
│   ├── openzeppelin-contracts-06/
│   ├── openzeppelin-contracts-08/
│   ├── openzeppelin-contracts-upgradeable/
│   ├── openzeppelin-contracts-v4.6.0/
│   └── openzeppelin-contracts-v5.4.0/
├── foundry.toml           # Forge configuration
├── foundry.lock           # Locked dependency versions
└── remappings.txt         # Import path mappings

js_sandbox/                # Node.js sandbox for ethers.js
├── package.json           # npm dependencies
└── sandbox.js             # JavaScript runtime

.gitmodules                # Git submodule definitions
```

## Prerequisites

### For Local Development

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/)
- **Foundry** (for Anvil blockchain): `curl -L https://foundry.paradigm.xyz | bash && foundryup`
- **Node.js 18+** with npm
- **Git** (for submodule management)

### For Docker

- Docker only (all dependencies included in image)
- Git submodules must be checked out before building

## Local Development

### First-Time Setup

```bash
# 1. Clone the repository (if not already done)
git clone <repo-url>
cd ethernaut-arena-green-agent

# 2. Initialize and fetch Foundry dependencies (git submodules)
git submodule update --init

# 3. Install Python dependencies
uv sync

# 4. Compile Solidity contracts
cd contracts && forge build && cd ..

# 5. Install JavaScript dependencies
cd js_sandbox && npm install && cd ..
```

### Running the Server

```bash
# Start the green agent
uv run src/server.py --host 127.0.0.1 --port 9009
```

The agent will be available at `http://127.0.0.1:9009/`.

### Verify Agent Card

```bash
curl http://localhost:9009/.well-known/agent.json
```

## Docker

**Important:** Git submodules must be checked out before building the Docker image.

```bash
# Ensure submodules are initialized
git submodule update --init

# Build the image
docker build -t ethernaut-green-agent .

# Run the container
docker run -p 9009:9009 ethernaut-green-agent
```

## Foundry Dependencies

Solidity dependencies are managed via [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules), the standard approach for Foundry projects.

| Dependency | Version | Description |
|------------|---------|-------------|
| `forge-std` | v1.12.0 | Foundry standard library |
| `openzeppelin-contracts-06` | v3.4.0 | OpenZeppelin for Solidity 0.6.x |
| `openzeppelin-contracts-08` | v4.9.0 | OpenZeppelin for Solidity 0.8.x |
| `openzeppelin-contracts-upgradeable` | - | Upgradeable contracts |
| `openzeppelin-contracts-v4.6.0` | v4.6.0 | Specific OZ version |
| `openzeppelin-contracts-v5.4.0` | v5.4.0 | Latest OZ version |

### Updating Dependencies

```bash
# Update a specific submodule to a new version
cd contracts/lib/forge-std
git fetch --tags
git checkout v1.13.0  # or desired version
cd ../../..

# Commit the update
git add contracts/lib/forge-std
git commit -m "Update forge-std to v1.13.0"
```

## Running an Evaluation

Send an evaluation request to the green agent with a purple agent URL:

```bash
curl -X POST http://localhost:9009/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{
        "type": "text",
        "text": "{\"participants\": {\"agent\": \"http://localhost:9020\"}, \"config\": {\"levels\": [0]}}"
      }]
    }
  }'
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `levels` | `list[int]` or `"all"` | Levels to evaluate (e.g., `[0, 1, 2]` or `"all"`) |
| `max_turns_per_level` | `int` | Maximum interaction turns per level (default: 30) |
| `timeout_per_level` | `int` | Timeout in seconds per level (default: 300) |
| `stop_on_failure` | `bool` | Stop on first level failure (default: false) |

### Example Configurations

```json
// Single level
{"participants": {"agent": "http://localhost:9020"}, "config": {"levels": [0]}}

// Multiple levels
{"participants": {"agent": "http://localhost:9020"}, "config": {"levels": [0, 1, 2, 3]}}

// All 41 levels
{"participants": {"agent": "http://localhost:9020"}, "config": {"levels": "all"}}

// With options
{
  "participants": {"agent": "http://localhost:9020"},
  "config": {
    "levels": [0, 1, 2],
    "max_turns_per_level": 50,
    "timeout_per_level": 600
  }
}
```

## Available Tools

The green agent provides these tools to purple agents:

| Tool | Description |
|------|-------------|
| `get_new_instance` | Deploy a new level instance contract |
| `exec_console` | Execute JavaScript in ethers.js environment |
| `view_source` | Read Solidity source code of contracts |
| `deploy_attack_contract` | Compile and deploy custom attack contracts |
| `submit_instance` | Submit solution for verification |

## Evaluation Results

The green agent returns structured results:

```json
{
  "winner": "agent",
  "detail": {
    "success_rate": 0.75,
    "levels_completed": 3,
    "levels_attempted": 4,
    "avg_turns_per_level": 12.5,
    "total_time_seconds": 180.5,
    "per_level": [
      {"level_id": 0, "name": "Hello Ethernaut", "completed": true, "turns": 8},
      {"level_id": 1, "name": "Fallback", "completed": true, "turns": 15},
      {"level_id": 2, "name": "Fallout", "completed": true, "turns": 10},
      {"level_id": 3, "name": "Coin Flip", "completed": false, "turns": 30}
    ]
  }
}
```

## Testing

```bash
# Install test dependencies
uv sync --extra test

# Start the agent
uv run src/server.py &

# Run A2A conformance tests
uv run pytest --agent-url http://localhost:9009
```

## Publishing to AgentBeats

1. **Ensure submodules are checked out:**
   ```bash
   git submodule update --init
   ```

2. **Build and push Docker image:**
   ```bash
   docker build -t ghcr.io/<username>/ethernaut-arena-green-agent:latest .
   docker push ghcr.io/<username>/ethernaut-arena-green-agent:latest
   ```

3. **Register on AgentBeats:**
   - Go to [agentbeats.dev](https://agentbeats.dev)
   - Register as a green agent with your Docker image reference
   - Connect to your leaderboard repository

## CI/CD

The repository includes a GitHub Actions workflow that automatically:
1. Checks out submodules
2. Builds the Docker image (including Foundry and contracts compilation)
3. Runs A2A conformance tests
4. Publishes to GitHub Container Registry

- **Push to `main`** → publishes `latest` tag
- **Create a git tag** (e.g., `v1.0.0`) → publishes version tags

## Troubleshooting

### Missing contract dependencies

If `forge build` fails with "file not found" errors:
```bash
git submodule update --init
```

### Submodules not cloning

If submodules show as empty directories:
```bash
git submodule sync
git submodule update --init
```

### Docker build fails

Ensure submodules are checked out before building:
```bash
git submodule update --init
docker build -t ethernaut-green-agent .
```

## License

MIT
