FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Install system dependencies (as root)
USER root
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Foundry (as root, then make available to all users)
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup && \
    cp /root/.foundry/bin/* /usr/local/bin/

# Create agent user
RUN adduser --disabled-password --gecos '' agent
USER agent
WORKDIR /home/agent

# Configure git for submodule operations
RUN git config --global user.email "agent@localhost" && \
    git config --global user.name "Agent"

# Copy Python project files
COPY --chown=agent:agent pyproject.toml uv.lock README.md ./
COPY --chown=agent:agent src src

# Copy contracts (including submodules - they should be checked out before docker build)
COPY --chown=agent:agent contracts contracts

# Copy JS sandbox
COPY --chown=agent:agent js_sandbox js_sandbox

# Copy git metadata for submodules
COPY --chown=agent:agent .gitmodules ./

# Install Python dependencies
RUN uv sync --locked

# Compile Solidity contracts
RUN cd contracts && forge build

# Install JS dependencies
RUN cd js_sandbox && npm install

ENTRYPOINT ["uv", "run", "src/server.py"]
CMD ["--host", "0.0.0.0"]
EXPOSE 9009
