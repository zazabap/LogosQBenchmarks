# LogosQ Quantum Computing Benchmarks

A comprehensive benchmarking suite for comparing quantum computing libraries including LogosQ (Rust), Yao.jl (Julia), PennyLane (Python), and Qiskit (Python). This project evaluates performance across various quantum algorithms and provides tools for analysis and visualization.

## Features

- **Multi-Library Support**: Benchmarks LogosQ, Yao.jl, PennyLane, and Qiskit
- **Comprehensive Metrics**: Execution time, energy accuracy (VQE), and resource usage
- **Multiple Benchmark Types**: GHZ States, Random Circuits, QFT, VQE, Gradient Differentiation
- **Reproducibility**: Standardized seeds, optimizers, and circuit structures
- **Visualization**: Python-based plotting scripts for publication-quality figures

## Quick Start

### Option 1: VS Code Dev Containers (Recommended)

1. Clone and open in VS Code:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd LogosQBenchmarks
   code .
   ```

2. Click "Reopen in Container" when prompted (or `F1` → "Dev Containers: Reopen in Container")

3. Wait for setup (15-30 min first time), then run benchmarks:
   ```bash
   bash scripts/run_vqa_parameter_sweep.sh
   bash scripts/run_xyz_heisenberg_benchmark.sh
   bash scripts/run_qft_benchmark.sh
   ```

### Option 2: Docker

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd LogosQBenchmarks
docker-compose build
docker-compose run --rm benchmark bash scripts/run_vqa_parameter_sweep.sh
```

**For detailed setup instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

## Prerequisites

- **Rust**: Latest stable (logosq 0.2.3)
- **Julia**: 1.8.5 (Yao, BenchmarkTools, JSON, Zygote)
- **Python**: 3.8+ (see `requirements.txt`)
- **.NET SDK**: 6.0+ (optional, for Q# benchmarks)

**Complete dependency list: [REQUIREMENTS.md](REQUIREMENTS.md)**

## Available Benchmarks

| Benchmark | Script | Output |
|-----------|--------|--------|
| VQE Parameter Sweep | `scripts/run_vqa_parameter_sweep.sh` | `test_results/vqa_parameter_sweep/` |
| XYZ Heisenberg Model | `scripts/run_xyz_heisenberg_benchmark.sh` | `test_results/xyz_heisenberg/` |
| Quantum Fourier Transform | `scripts/run_qft_benchmark.sh` | `test_results/qft/` |
| Gradient Tests | `scripts/run_gradient_tests.sh` | `test_results/gradient/` |

## Project Structure

```
LogosQBenchmarks/
├── logosq/          # LogosQ (Rust) benchmarks
├── qiskit/          # Qiskit (Python) benchmarks
├── pennylane/       # PennyLane (Python) benchmarks
├── yao.jl/          # Yao.jl (Julia) benchmarks
├── qsharp/          # Q# benchmarks
├── scripts/         # Orchestration and plotting scripts
└── test_results/    # Generated results and plots
```

## Benchmark Details

### Variational Quantum Eigensolver (VQE)
Ground state energy optimization for H₂ molecule (STO-3G basis). Hardware-efficient ansatz with Adam optimizer.

### Quantum Fourier Transform (QFT)
O(n²) algorithm scaling test for simulation speed and memory management.

### Gradient Differentiation
Validates automatic differentiation correctness and memory safety across frameworks.

## License

MIT License

## Citation

```bibtex
@software{logosq_benchmarks,
  title={LogosQ Quantum Computing Benchmarks},
  author={LogosQ Team},
  year={2024},
  url={https://github.com/zazabap/LogosQBenchmarks}
}
```
