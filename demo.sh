#!/bin/bash

# LogosQ Benchmark Demo Script
# This script demonstrates the benchmarking system with sample data

set -e

echo "========================================"
echo "LogosQ Benchmark System Demo"
echo "========================================"

# Create necessary directories
mkdir -p results logs

echo "Generating sample benchmark results..."

# Create sample results for different libraries
cat > results/logosq_results.json << 'EOF'
{
  "library": "LogosQ",
  "version": "0.1.0",
  "results": [
    {"name": "GHZ-4", "num_qubits": 4, "num_gates": 4, "execution_time_ms": 1.25, "memory_usage_mb": 0.4, "circuit_depth": 2},
    {"name": "Random-4-40", "num_qubits": 4, "num_gates": 50, "execution_time_ms": 5.67, "memory_usage_mb": 0.6, "circuit_depth": 50},
    {"name": "QFT-4", "num_qubits": 4, "num_gates": 16, "execution_time_ms": 3.21, "memory_usage_mb": 0.5, "circuit_depth": 8},
    {"name": "GHZ-6", "num_qubits": 6, "num_gates": 6, "execution_time_ms": 2.45, "memory_usage_mb": 1.1, "circuit_depth": 2},
    {"name": "Random-6-60", "num_qubits": 6, "num_gates": 75, "execution_time_ms": 12.34, "memory_usage_mb": 1.8, "circuit_depth": 75},
    {"name": "QFT-6", "num_qubits": 6, "num_gates": 36, "execution_time_ms": 7.89, "memory_usage_mb": 1.5, "circuit_depth": 12},
    {"name": "GHZ-8", "num_qubits": 8, "num_gates": 8, "execution_time_ms": 4.56, "memory_usage_mb": 4.2, "circuit_depth": 2},
    {"name": "Random-8-80", "num_qubits": 8, "num_gates": 100, "execution_time_ms": 28.91, "memory_usage_mb": 7.5, "circuit_depth": 100}
  ],
  "total_time_ms": 66.28
}
EOF

cat > results/yao_results.json << 'EOF'
{
  "library": "Yao.jl",
  "version": "0.8.0",
  "results": [
    {"name": "GHZ-4", "num_qubits": 4, "num_gates": 4, "execution_time_ms": 2.15, "memory_usage_mb": 0.5, "circuit_depth": 2},
    {"name": "Random-4-40", "num_qubits": 4, "num_gates": 50, "execution_time_ms": 8.32, "memory_usage_mb": 0.8, "circuit_depth": 50},
    {"name": "QFT-4", "num_qubits": 4, "num_gates": 16, "execution_time_ms": 5.67, "memory_usage_mb": 0.6, "circuit_depth": 8},
    {"name": "GHZ-6", "num_qubits": 6, "num_gates": 6, "execution_time_ms": 4.23, "memory_usage_mb": 1.2, "circuit_depth": 2},
    {"name": "Random-6-60", "num_qubits": 6, "num_gates": 75, "execution_time_ms": 18.45, "memory_usage_mb": 2.1, "circuit_depth": 75},
    {"name": "QFT-6", "num_qubits": 6, "num_gates": 36, "execution_time_ms": 12.89, "memory_usage_mb": 1.8, "circuit_depth": 12},
    {"name": "GHZ-8", "num_qubits": 8, "num_gates": 8, "execution_time_ms": 8.91, "memory_usage_mb": 4.5, "circuit_depth": 2},
    {"name": "Random-8-80", "num_qubits": 8, "num_gates": 100, "execution_time_ms": 42.67, "memory_usage_mb": 8.3, "circuit_depth": 100}
  ],
  "total_time_ms": 103.29
}
EOF

cat > results/cpp_results.json << 'EOF'
{
  "library": "C++",
  "version": "1.0.0",
  "results": [
    {"name": "GHZ-4", "num_qubits": 4, "num_gates": 4, "execution_time_ms": 0.89, "memory_usage_mb": 0.3, "circuit_depth": 2},
    {"name": "Random-4-40", "num_qubits": 4, "num_gates": 50, "execution_time_ms": 3.45, "memory_usage_mb": 0.4, "circuit_depth": 50},
    {"name": "QFT-4", "num_qubits": 4, "num_gates": 16, "execution_time_ms": 2.12, "memory_usage_mb": 0.35, "circuit_depth": 8},
    {"name": "GHZ-6", "num_qubits": 6, "num_gates": 6, "execution_time_ms": 1.67, "memory_usage_mb": 0.9, "circuit_depth": 2},
    {"name": "Random-6-60", "num_qubits": 6, "num_gates": 75, "execution_time_ms": 8.23, "memory_usage_mb": 1.3, "circuit_depth": 75},
    {"name": "QFT-6", "num_qubits": 6, "num_gates": 36, "execution_time_ms": 5.34, "memory_usage_mb": 1.1, "circuit_depth": 12},
    {"name": "GHZ-8", "num_qubits": 8, "num_gates": 8, "execution_time_ms": 3.21, "memory_usage_mb": 3.5, "circuit_depth": 2},
    {"name": "Random-8-80", "num_qubits": 8, "num_gates": 100, "execution_time_ms": 19.87, "memory_usage_mb": 6.1, "circuit_depth": 100}
  ],
  "total_time_ms": 44.78
}
EOF

cat > results/pennylane_results.json << 'EOF'
{
  "library": "PennyLane",
  "version": "0.32.0",
  "results": [
    {"name": "GHZ-4", "num_qubits": 4, "num_gates": 4, "execution_time_ms": 12.45, "memory_usage_mb": 2.1, "circuit_depth": 2},
    {"name": "Random-4-40", "num_qubits": 4, "num_gates": 50, "execution_time_ms": 35.67, "memory_usage_mb": 3.2, "circuit_depth": 50},
    {"name": "QFT-4", "num_qubits": 4, "num_gates": 16, "execution_time_ms": 23.89, "memory_usage_mb": 2.8, "circuit_depth": 8},
    {"name": "GHZ-6", "num_qubits": 6, "num_gates": 6, "execution_time_ms": 28.34, "memory_usage_mb": 5.4, "circuit_depth": 2},
    {"name": "Random-6-60", "num_qubits": 6, "num_gates": 75, "execution_time_ms": 78.91, "memory_usage_mb": 8.7, "circuit_depth": 75},
    {"name": "QFT-6", "num_qubits": 6, "num_gates": 36, "execution_time_ms": 56.23, "memory_usage_mb": 7.1, "circuit_depth": 12},
    {"name": "GHZ-8", "num_qubits": 8, "num_gates": 8, "execution_time_ms": 67.12, "memory_usage_mb": 18.9, "circuit_depth": 2},
    {"name": "Random-8-80", "num_qubits": 8, "num_gates": 100, "execution_time_ms": 156.78, "memory_usage_mb": 32.4, "circuit_depth": 100}
  ],
  "total_time_ms": 459.39
}
EOF

cat > results/qiskit_results.json << 'EOF'
{
  "library": "Qiskit",
  "version": "1.0.0",
  "results": [
    {"name": "GHZ-4", "num_qubits": 4, "num_gates": 4, "execution_time_ms": 18.34, "memory_usage_mb": 3.2, "circuit_depth": 2},
    {"name": "Random-4-40", "num_qubits": 4, "num_gates": 50, "execution_time_ms": 45.67, "memory_usage_mb": 4.1, "circuit_depth": 50},
    {"name": "QFT-4", "num_qubits": 4, "num_gates": 16, "execution_time_ms": 31.23, "memory_usage_mb": 3.8, "circuit_depth": 8},
    {"name": "GHZ-6", "num_qubits": 6, "num_gates": 6, "execution_time_ms": 34.56, "memory_usage_mb": 7.5, "circuit_depth": 2},
    {"name": "Random-6-60", "num_qubits": 6, "num_gates": 75, "execution_time_ms": 89.12, "memory_usage_mb": 12.3, "circuit_depth": 75},
    {"name": "QFT-6", "num_qubits": 6, "num_gates": 36, "execution_time_ms": 67.89, "memory_usage_mb": 9.8, "circuit_depth": 12},
    {"name": "GHZ-8", "num_qubits": 8, "num_gates": 8, "execution_time_ms": 78.91, "memory_usage_mb": 25.6, "circuit_depth": 2},
    {"name": "Random-8-80", "num_qubits": 8, "num_gates": 100, "execution_time_ms": 189.34, "memory_usage_mb": 42.7, "circuit_depth": 100}
  ],
  "total_time_ms": 555.06
}
EOF

echo "Generating sample memory usage logs..."

# Create sample memory logs
cat > logs/LogosQ-Rust_memory.log << 'EOF'
12345   1 logosq_benchmark     0.5  10.2
12345   1 logosq_benchmark     0.8  15.4
12345   1 logosq_benchmark     1.2  22.1
12345   1 logosq_benchmark     0.9  18.7
12345   1 logosq_benchmark     0.6  12.3
EOF

cat > logs/Yao.jl_memory.log << 'EOF'
12346   1 julia               1.2  8.5
12346   1 julia               1.8  12.3
12346   1 julia               2.1  16.8
12346   1 julia               1.9  14.2
12346   1 julia               1.5  10.9
EOF

echo "Running results combination script..."
if [ -f "scripts/combine_results.py" ]; then
    cd scripts && python3 combine_results.py
    cd ..
fi

echo "Starting visualization server..."
if command -v node >/dev/null 2>&1; then
    echo "Node.js found. Starting server..."
    cd visualization
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing Node.js dependencies..."
        npm install --silent
    fi
    
    echo ""
    echo "============================================"
    echo "Demo server starting on http://localhost:8080"
    echo "============================================"
    echo ""
    echo "Open your browser and navigate to:"
    echo "  http://localhost:8080"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    node server.js
else
    echo "Node.js not found. Skipping visualization server."
    echo ""
    echo "============================================"
    echo "Demo results generated successfully!"
    echo "============================================"
    echo ""
    echo "Sample benchmark results created in ./results/"
    echo "Memory logs created in ./logs/"
    echo ""
    echo "To view the visualization dashboard:"
    echo "1. Install Node.js"
    echo "2. Run: cd visualization && npm install && npm start"
    echo "3. Open http://localhost:8080 in your browser"
fi