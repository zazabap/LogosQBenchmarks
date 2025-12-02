# Requirements

Complete dependency list for the LogosQ Benchmark Suite.

## Python Dependencies

Install with: `pip install -r requirements.txt`

| Package | Version | Purpose |
|---------|---------|---------|
| pennylane | >=0.30.0 | Quantum computing framework |
| qiskit | >=0.40.0 | Quantum computing framework |
| numpy | >=1.21.0 | Numerical computing |
| scipy | >=1.7.0 | Scientific computing (optimization) |
| pandas | >=1.3.0 | Data manipulation |
| matplotlib | >=3.5.0 | Plotting and visualization |
| psutil | >=5.8.0 | System utilities (memory profiling) |

## Rust Dependencies (LogosQ)

Install with: `cd logosq && cargo build --release`

| Package | Version | Purpose |
|---------|---------|---------|
| logosq | 0.2.3 | Main quantum computing library |
| serde | 1.0 | Serialization |
| serde_json | 1.0 | JSON serialization |
| rand | 0.8 | Random number generation |
| num-complex | 0.4 | Complex numbers |
| criterion | 0.5 | Benchmarking |
| rayon | 1.7 | Data parallelism |
| nalgebra | 0.32 | Linear algebra |
| tqdm | 0.8.0 | Progress bars |

## Julia Dependencies (Yao.jl)

Install with: `julia -e 'using Pkg; Pkg.add(["Yao", "BenchmarkTools", "JSON", "Zygote"])'`

| Package | Version | Purpose |
|---------|---------|---------|
| Yao | 0.8.14 | Main quantum computing framework |
| BenchmarkTools | 1.6.3 | Benchmarking utilities |
| JSON | 0.21.4 | JSON serialization |
| Zygote | 0.7.4 | Automatic differentiation |

## Q# Dependencies (.NET)

Install with: `dotnet restore`

| Package | Version | Purpose |
|---------|---------|---------|
| Microsoft.Quantum.Sdk | 0.28.302812 | Quantum Development Kit |
| System.Text.Json | 6.0.3 | JSON serialization |
| .NET SDK | 6.0+ | Runtime (required) |

## System Dependencies

### Ubuntu/Debian
```bash
sudo apt-get install -y build-essential cmake python3 python3-pip \
    pkg-config libssl-dev libeigen3-dev curl wget git
```

### macOS
```bash
brew install cmake python3 pkg-config openssl eigen
```

## Version Compatibility

| Component | Tested Version |
|----------|----------------|
| Python | 3.8+ |
| Rust | Latest stable (2021 edition) |
| Julia | 1.8.5 (compatible with 1.8.x) |
| .NET | 6.0+ |
| Node.js | 14+ (optional, for dashboard) |

## Installation Order (Native)

1. System dependencies
2. Rust (via rustup.rs)
3. Julia 1.8.5
4. Python packages (`pip install -r requirements.txt`)
5. Julia packages (`julia -e 'using Pkg; Pkg.add([...])'`)
6. .NET SDK (optional, for Q#)
7. Build Rust (`cd logosq && cargo build --release`)

**Or use Docker/Dev Containers for automatic setup** (see [DEPLOYMENT.md](DEPLOYMENT.md))
