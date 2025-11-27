# LogosQ Quantum Computing Benchmarks

A comprehensive benchmarking suite for comparing quantum computing libraries including LogosQ (Rust), Yao.jl (Julia), PennyLane (Python), and Qiskit (Python). This project evaluates performance across various quantum algorithms and provides tools for analysis and visualization.

## Features

- **Multi-Library Support**: Benchmarks LogosQ, Yao.jl, PennyLane, and Qiskit.
- **Comprehensive Metrics**: Execution time, energy accuracy (VQE), and resource usage.
- **Multiple Benchmark Types**:
    - **GHZ States**: Entanglement generation performance.
    - **Random Circuits**: General circuit simulation capabilities.
    - **Quantum Fourier Transform (QFT)**: O(n²) algorithm scaling.
    - **Variational Quantum Eigensolver (VQE)**: Hybrid quantum-classical optimization for H₂ chemistry, including parameter sweeps.
    - **Gradient Differentiation**: Verification of automatic differentiation correctness and memory safety.
- **Reproducibility**: Standardized seeds, optimizers, and circuit structures for fair comparison.
- **Visualization**: Python-based plotting scripts for generating publication-quality figures.

## Use Cases

This benchmarking suite is designed for researchers, developers, and educators who need to:

1. **Compare Framework Performance**: Objectively evaluate which library (LogosQ, Qiskit, PennyLane, Yao.jl) performs best for specific quantum tasks like state preparation, VQE, or QFT.
2. **Resource Planning**: Estimate memory and CPU requirements for simulating quantum circuits of varying sizes.
3. **Algorithm Optimization**: Analyze runtime scaling and memory overhead to optimize quantum algorithms before deployment.
4. **Simulator Selection**: Choose the appropriate simulation backend based on circuit depth and qubit count.
5. **Educational Analysis**: Visualize and demonstrate the computational complexity differences between various quantum simulation approaches.

## Quick Start

### Prerequisites

- **Rust**: Latest stable toolchain
- **Julia**: 1.6+ (with `Yao`, `BenchmarkTools`, `JSON`)
- **Python**: 3.8+ (with `pennylane`, `qiskit`, `matplotlib`, `numpy`, `scipy`, `psutil`)

### Running Benchmarks

The `scripts/` directory contains shell scripts to orchestrate benchmarks for different algorithms.

1. **VQE Parameter Sweep (H₂)**:
   Runs VQE optimization across LogosQ, Qiskit, PennyLane, and Yao.jl with varying ansatz depths (12-28 parameters).
   ```bash
   # Run the benchmark sweep
   bash scripts/run_vqa_parameter_sweep.sh
   
   # Generate analysis plots
   python3 scripts/plot_vqa_benchmark.py
   ```
   *Output*: JSON results and plots in `test_results/vqa_parameter_sweep/`

2. **Quantum Fourier Transform (QFT)**:
   Benchmarks QFT execution time and memory usage. Automatically generates comparison plots.
   ```bash
   bash scripts/run_qft_benchmark.sh
   ```
   *Output*: JSON results and comparison plots in `test_results/qft/`

3. **Gradient Calculation Tests**:
   Verifies the correctness of gradient calculations across frameworks.
   ```bash
   bash scripts/run_gradient_tests.sh
   ```
   *Output*: Test logs in `test_results/gradient/`

## Project Structure

```
LogosQBenchmarks/
├── logosq/                     # LogosQ (Rust) implementation
│   ├── src/                    # Source code
│   ├── VQA/                    # VQE benchmark implementation
│   ├── QuantumFourierTransform/# QFT benchmark implementation
│   └── MemoryCircuitDifferentiation/ # Gradient correctness tests
├── qiskit/                     # Qiskit (Python) benchmarks
│   ├── VQA/                    # VQE implementation
│   ├── QuantumFourierTransform/# QFT benchmark implementation
│   └── MemoryDifferentiation/  # Gradient correctness tests
├── pennylane/                  # PennyLane (Python) benchmarks
│   ├── VQA/                    # VQE implementation
│   ├── QuantumFourierTransform/# QFT benchmark implementation
│   └── MemoryCicuitDifferentiation/ # Gradient correctness tests
├── yao.jl/                     # Yao.jl (Julia) benchmarks
│   ├── VQA/                    # VQE implementation
│   ├── QuantumFourierTransform/# QFT benchmark implementation
│   └── MemoryCircuitDifferentiation/ # Gradient correctness tests
├── scripts/                    # Orchestration and plotting scripts
│   ├── run_vqa_parameter_sweep.sh
│   ├── plot_vqa_benchmark.py
│   ├── run_qft_benchmark.sh
│   ├── plot_qft_comparison.py
│   └── run_gradient_tests.sh
├── test_results/               # Generated benchmark results and plots
│   ├── vqa_parameter_sweep/
│   ├── qft/
│   └── gradient/
└── summary/                    # Visualization dashboard (web-based)
```

## Benchmark Details

### Variational Quantum Eigensolver (VQE)
Benchmarks hybrid quantum-classical optimization finding the ground state energy of the H₂ molecule (STO-3G basis).
- **Hamiltonian**: H₂ at 0.735 Å (mapped via Jordan-Wigner).
- **Ansatz**: Hardware-efficient (Ry rotations + linear CNOT entanglement).
- **Optimizer**: Adam (lr=0.01, tol=1e-7).
- **Metrics**: Exact energy error, number of iterations, total runtime.

### Quantum Fourier Transform (QFT)
Benchmarks the quantum algorithm with O(n²) complexity, testing simulation speed and memory management for increasing qubit counts.

### Gradient Calculation & Differentiation
Validates the correctness of gradient computations for parameterized quantum circuits. Tests for specific issues such as:
- Memory safety during differentiation (preventing segfaults/leaks).
- Correct handling of complex coefficients.
- Generator validity and operation broadcasting.
- Numerical stability (NaN detection).

## License

MIT License - see LICENSE file for details.

## Citation

If you use this benchmarking suite in your research, please cite:

```bibtex
@software{logosq_benchmarks,
  title={LogosQ Quantum Computing Benchmarks},
  author={LogosQ Team},
  year={2024},
  url={https://github.com/zazabap/LogosQBenchmarks}
}
```
