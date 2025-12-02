# Multi-stage Dockerfile for LogosQ Benchmarking System
FROM ubuntu:22.04 as base

# Install system dependencies (excluding julia)
# Include essential devcontainer tools: sudo, procps, less, vim, etc.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    pkg-config \
    libssl-dev \
    htop \
    time \
    valgrind \
    libeigen3-dev \
    sudo \
    procps \
    less \
    vim \
    nano \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Julia manually
RUN wget https://julialang-s3.julialang.org/bin/linux/x64/1.8/julia-1.8.5-linux-x86_64.tar.gz && \
    tar -xvzf julia-1.8.5-linux-x86_64.tar.gz && \
    mv julia-1.8.5 /opt/julia && \
    ln -s /opt/julia/bin/julia /usr/local/bin/julia && \
    rm julia-1.8.5-linux-x86_64.tar.gz

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Create working directory
WORKDIR /app

# Copy project files
# Note: The full directory will be mounted as a volume in docker-compose,
# but we need these files for the build process during image creation
COPY . .

# Install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    (pip3 install -r requirements.txt || pip3 install pennylane qiskit matplotlib pandas numpy psutil scipy)

# Install Julia dependencies
# Note: CSV and DataFrames are optional (not actively used in current code)
RUN julia -e 'using Pkg; Pkg.add(["Yao", "BenchmarkTools", "JSON", "Zygote"])'

# Install Node.js dependencies for visualization (if summary directory exists)
RUN if [ -f "summary/package.json" ]; then cd summary && npm install || true; fi

# Build Rust components (LogosQ)
RUN cd logosq && cargo build --release || echo "Warning: Rust build may have failed, but continuing..."

# Expose port for web visualization
EXPOSE 8080

# Set up environment for devcontainer
# Ensure PATH is set correctly and container stays alive
ENV DEBIAN_FRONTEND=noninteractive

# Default command - keep container running for devcontainers
# docker-compose will override this with 'sleep infinity'
CMD ["sleep", "infinity"]