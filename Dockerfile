# Multi-stage Dockerfile for LogosQ Benchmarking System
FROM ubuntu:22.04 as base

# Install system dependencies (excluding julia)
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
COPY . .

# Install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN pip3 install pennylane qiskit matplotlib pandas numpy psutil

# Install Julia dependencies
RUN julia -e 'using Pkg; Pkg.add(["Yao", "BenchmarkTools", "JSON", "CSV", "DataFrames"])'

# Install Node.js dependencies for visualization
RUN npm install -g http-server
RUN cd visualization && npm install

# Build Rust components
RUN cd rust && cargo build --release

# Build C++ components
RUN cd cpp && mkdir -p build && cd build && cmake .. && make

# Expose port for web visualization
EXPOSE 8080

# Default command
CMD ["./run_benchmarks.sh"]