# Deployment Guide

Complete guide for setting up and running benchmarks on a new device.

## Prerequisites

- **Docker**: 20.10+ (or VS Code with Dev Containers extension)
- **Git**: For cloning the repository
- **8GB+ RAM** (16GB recommended)
- **10GB free disk space**

## Setup Methods

### Method 1: VS Code Dev Containers (Easiest) ⭐

**Best for**: Developers who want IDE integration

1. **Clone and open:**
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd LogosQBenchmarks
   code .
   ```

2. **Reopen in Container:**
   - Click "Reopen in Container" when prompted, or
   - Press `F1` → "Dev Containers: Reopen in Container"

3. **Wait for setup** (15-30 min first time)

4. **Run benchmarks** in VS Code terminal:
   ```bash
   bash scripts/run_vqa_parameter_sweep.sh
   bash scripts/run_xyz_heisenberg_benchmark.sh
   bash scripts/run_qft_benchmark.sh
   ```

**Benefits**: Automatic setup, full IDE integration, extensions auto-installed

### Method 2: Docker Command Line

1. **Clone repository:**
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd LogosQBenchmarks
   ```

2. **Build image:**
   ```bash
   docker-compose build
   ```
   *Takes 15-30 minutes on first build*

3. **Run benchmarks:**
   ```bash
   # Interactive container
   docker-compose run --rm benchmark bash
   
   # Or run directly
   docker-compose run --rm benchmark bash scripts/run_vqa_parameter_sweep.sh
   ```

### Method 3: Native Installation

**Prerequisites**: Rust, Julia 1.8.5, Python 3.8+, .NET SDK 6.0+ (optional)

1. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y build-essential cmake python3 python3-pip \
       pkg-config libssl-dev libeigen3-dev curl wget git
   
   # macOS
   brew install cmake python3 pkg-config openssl eigen
   ```

2. **Install Rust:**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

3. **Install Julia 1.8.5:**
   ```bash
   # Linux
   wget https://julialang-s3.julialang.org/bin/linux/x64/1.8/julia-1.8.5-linux-x86_64.tar.gz
   tar -xvzf julia-1.8.5-linux-x86_64.tar.gz
   sudo mv julia-1.8.5 /opt/julia
   sudo ln -s /opt/julia/bin/julia /usr/local/bin/julia
   
   # macOS
   brew install julia@1.8
   ```

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Julia packages:**
   ```bash
   julia -e 'using Pkg; Pkg.add(["Yao", "BenchmarkTools", "JSON", "Zygote"])'
   ```

6. **Build Rust components:**
   ```bash
   cd logosq && cargo build --release
   ```

7. **Install .NET SDK (optional, for Q#):**
   ```bash
   # Ubuntu/Debian
   wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb
   sudo dpkg -i packages-microsoft-prod.deb
   sudo apt-get install -y dotnet-sdk-6.0
   
   # macOS
   brew install --cask dotnet-sdk
   ```

## Running Benchmarks

All benchmarks save results to `test_results/`:

```bash
# VQE Parameter Sweep
bash scripts/run_vqa_parameter_sweep.sh

# XYZ Heisenberg Model (interactive - prompts for qubit range)
bash scripts/run_xyz_heisenberg_benchmark.sh

# Or set environment variables for non-interactive:
export XYZ_START_QUBITS=4
export XYZ_END_QUBITS=24
export XYZ_STEP_QUBITS=2
bash scripts/run_xyz_heisenberg_benchmark.sh

# Quantum Fourier Transform
bash scripts/run_qft_benchmark.sh

# Gradient Tests
bash scripts/run_gradient_tests.sh
```

## Generating Plots

Plots are auto-generated, but you can regenerate:
```bash
python3 scripts/plot_vqa_benchmark.py
python3 scripts/plot_xyz_heisenberg_comparison.py
python3 scripts/plot_qft_comparison.py
```

## Common Docker Commands

```bash
# Build image
docker-compose build

# Interactive container
docker-compose run --rm benchmark bash

# Run specific benchmark
docker-compose run --rm benchmark bash scripts/run_vqa_parameter_sweep.sh

# View logs
docker-compose logs

# Clean rebuild
docker-compose build --no-cache
```

## Troubleshooting

### Docker Issues

**Build fails with "out of memory"**: Increase Docker memory limit (Docker Desktop → Settings → Resources → Memory)

**Permission denied**: Add user to docker group: `sudo usermod -aG docker $USER` (log out and back in)

### Native Installation Issues

**Rust build fails**: Update Rust: `rustup update stable`

**Julia packages fail**: Try `julia -e 'using Pkg; Pkg.update()'` then retry

**Python packages fail**: Use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Q# benchmarks fail**: Ensure .NET SDK 6.0+ is installed: `dotnet --version`

## Performance Tips

- Use Docker BuildKit: `DOCKER_BUILDKIT=1 docker-compose build`
- Monitor memory usage for large benchmarks
- Start with smaller qubit ranges to test setup
