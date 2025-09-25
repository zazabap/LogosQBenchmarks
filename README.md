# LogosQ Quantum Computing Benchmarks

A comprehensive benchmarking suite for comparing quantum computing libraries including LogosQ (Rust), Yao.jl, C++, PennyLane, and Qiskit. This project provides Docker containerization, memory usage monitoring, and interactive D3.js visualizations.

## Features

- **Multi-Library Support**: Benchmarks LogosQ, Yao.jl, C++, PennyLane, and Qiskit
- **Docker Containerization**: Complete environment setup with single command
- **Memory Monitoring**: Real-time memory usage tracking during benchmarks
- **Interactive Visualization**: D3.js dashboard for analyzing results
- **Comprehensive Metrics**: Execution time, memory usage, circuit depth analysis
- **Multiple Benchmark Types**: GHZ states, random circuits, QFT implementations

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/zazabap/LogosQBenchmarks
cd LogosQBenchmarks
```

2. Build and run the complete benchmark suite:
```bash
docker-compose up --build
```

3. Access the visualization dashboard at `http://localhost:8080`

### Manual Setup

#### Prerequisites

- Rust (latest stable)
- Julia 1.6+
- Python 3.8+
- Node.js 16+
- C++ compiler with CMake
- Essential build tools

#### Installation

1. **Install Rust dependencies:**
```bash
cd rust
cargo build --release
```

2. **Install Julia dependencies:**
```bash
julia -e 'using Pkg; Pkg.add(["Yao", "BenchmarkTools", "JSON", "CSV", "DataFrames"])'
```

3. **Install Python dependencies:**
```bash
pip install pennylane qiskit matplotlib pandas numpy psutil
```

4. **Build C++ components:**
```bash
cd cpp
mkdir build && cd build
cmake ..
make
```

5. **Install visualization dependencies:**
```bash
cd visualization
npm install
```

#### Running Benchmarks

1. **Run all benchmarks:**
```bash
./run_benchmarks.sh
```

2. **Run specific library benchmarks:**
```bash
# LogosQ (Rust)
cd rust && cargo run --release

# Yao.jl
cd julia && julia yao_benchmark.jl

# C++
cd cpp/build && ./cpp_benchmark

# PennyLane
cd python && python pennylane_benchmark.py

# Qiskit
cd python && python qiskit_benchmark.py
```

3. **Start visualization server:**
```bash
cd visualization
npm start
```

## Project Structure

```
LogosQBenchmarks/
├── rust/                     # LogosQ Rust implementation
│   ├── src/
│   │   ├── lib.rs            # Core quantum simulation library
│   │   └── main.rs           # Benchmark runner
│   └── Cargo.toml
├── julia/                    # Yao.jl benchmarks
│   └── yao_benchmark.jl
├── cpp/                      # C++ quantum simulator
│   ├── src/
│   │   ├── quantum_simulator.hpp
│   │   ├── quantum_simulator.cpp
│   │   └── main.cpp
│   └── CMakeLists.txt
├── python/                   # Python benchmarks
│   ├── qiskit_benchmark.py
│   └── pennylane_benchmark.py
├── visualization/            # D3.js dashboard
│   ├── public/
│   │   ├── index.html
│   │   ├── dashboard.js
│   │   └── styles.css
│   ├── server.js
│   └── package.json
├── scripts/                  # Utility scripts
│   └── combine_results.py
├── results/                  # Benchmark outputs (created at runtime)
├── logs/                     # Memory usage logs (created at runtime)
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Container definition
└── run_benchmarks.sh        # Main benchmark runner
```

## Benchmark Types

### 1. GHZ States
Tests creation of maximally entangled states: |000...0⟩ + |111...1⟩

### 2. Random Circuits
Evaluates performance on circuits with random single-qubit gates and CNOT gates

### 3. Quantum Fourier Transform (QFT)
Benchmarks the quantum algorithm with O(n²) complexity

## Visualization Dashboard

The D3.js dashboard provides four main views:

1. **Performance**: Execution time comparisons with filtering options
2. **Memory**: Memory usage analysis and scaling with qubit count
3. **Scalability**: Performance scaling and circuit depth analysis
4. **Summary**: Overall library comparison and rankings

### Dashboard Features

- Interactive filtering by benchmark type
- Logarithmic/linear scale options
- Detailed tooltips with comprehensive metrics
- Responsive design for different screen sizes
- Real-time data loading from benchmark results

## Memory Monitoring

The system monitors memory usage during benchmark execution:

- **Real-time tracking**: Memory usage sampled every 100ms
- **Per-library logs**: Separate memory profiles for each library
- **Visualization**: Memory usage trends in the dashboard
- **Analysis**: Memory efficiency comparisons

## Results Format

Benchmark results are stored in JSON format with the following structure:

```json
{
  "library": "LibraryName",
  "version": "1.0.0",
  "results": [
    {
      "name": "GHZ-8",
      "num_qubits": 8,
      "num_gates": 8,
      "execution_time_ms": 42.5,
      "memory_usage_mb": 12.3,
      "circuit_depth": 2
    }
  ],
  "total_time_ms": 1250.0
}
```

## Configuration

### Qubit Limits
Default configuration tests up to 14 qubits to balance thoroughness with execution time. Modify `qubit_sizes` arrays in benchmark scripts to adjust.

### Benchmark Parameters
- **Random Circuit Gates**: 10 * num_qubits per circuit
- **Memory Sampling**: Every 100ms during execution
- **QFT Limit**: Up to 10 qubits due to complexity

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Add your improvements or new library support
4. Run the benchmark suite to ensure compatibility
5. Submit a pull request

### Adding New Libraries

To add support for a new quantum library:

1. Create a new directory: `newlibrary/`
2. Implement benchmark scripts following the existing pattern
3. Update `run_benchmarks.sh` to include the new library
4. Add library colors and configuration to `visualization/public/dashboard.js`
5. Update documentation

## Performance Notes

- **Exponential Scaling**: Memory usage grows exponentially with qubit count
- **Optimization Levels**: C++ and Rust use high optimization (-O3, --release)
- **Simulator Backends**: Different libraries use different simulation backends
- **Hardware Dependencies**: Performance may vary significantly across different hardware

## System Requirements

### Minimum
- 4GB RAM
- 2 CPU cores
- 2GB disk space

### Recommended
- 16GB+ RAM for larger qubit counts
- 8+ CPU cores for parallel execution
- SSD for faster I/O

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

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in each component directory
- Review the Docker logs for debugging information

---

**Note**: This benchmarking suite is designed for CPU-based quantum simulation. GPU acceleration and quantum hardware benchmarks are planned for future releases.
