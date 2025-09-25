#!/bin/bash

# LogosQ Benchmark Runner Script
set -e

echo "========================================"
echo "LogosQ Quantum Computing Benchmark Suite"
echo "========================================"

# Create results and logs directories
mkdir -p results logs

# Function to monitor memory usage
monitor_memory() {
    local name=$1
    local pid=$2
    echo "Monitoring memory for $name (PID: $pid)"
    while kill -0 $pid 2>/dev/null; do
        ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -p $pid >> logs/${name}_memory.log 2>/dev/null || true
        sleep 0.1
    done
}

# Function to run benchmark with memory monitoring
run_benchmark() {
    local name=$1
    local command=$2
    
    echo "Running $name benchmark..."
    echo "Command: $command"
    
    # Start the benchmark process in background
    eval "$command" &
    local pid=$!
    
    # Start memory monitoring in background
    monitor_memory "$name" $pid &
    local monitor_pid=$!
    
    # Wait for benchmark to complete
    wait $pid
    local exit_code=$?
    
    # Stop memory monitoring
    kill $monitor_pid 2>/dev/null || true
    
    if [ $exit_code -eq 0 ]; then
        echo "$name benchmark completed successfully"
    else
        echo "$name benchmark failed with exit code $exit_code"
    fi
    
    return $exit_code
}

echo "Starting benchmarks..."

# Run LogosQ (Rust) benchmarks
if [ -f "rust/target/release/logosq_benchmark" ]; then
    run_benchmark "LogosQ-Rust" "cd rust && ./target/release/logosq_benchmark > ../results/logosq_results.json"
else
    echo "LogosQ Rust benchmark not found, skipping..."
fi

# Run Yao.jl benchmarks
if [ -f "julia/yao_benchmark.jl" ]; then
    run_benchmark "Yao.jl" "cd julia && julia yao_benchmark.jl > ../results/yao_results.json"
else
    echo "Yao.jl benchmark not found, skipping..."
fi

# Run C++ benchmarks
if [ -f "cpp/build/cpp_benchmark" ]; then
    run_benchmark "C++" "cd cpp/build && ./cpp_benchmark > ../../results/cpp_results.json"
else
    echo "C++ benchmark not found, skipping..."
fi

# Run PennyLane benchmarks
if [ -f "python/pennylane_benchmark.py" ]; then
    run_benchmark "PennyLane" "cd python && python3 pennylane_benchmark.py > ../results/pennylane_results.json"
else
    echo "PennyLane benchmark not found, skipping..."
fi

# Run Qiskit benchmarks
if [ -f "python/qiskit_benchmark.py" ]; then
    run_benchmark "Qiskit" "cd python && python3 qiskit_benchmark.py > ../results/qiskit_results.json"
else
    echo "Qiskit benchmark not found, skipping..."
fi

echo "All benchmarks completed!"
echo "Results saved in ./results/"
echo "Memory usage logs saved in ./logs/"

# Generate combined results
if [ -f "scripts/combine_results.py" ]; then
    echo "Generating combined results..."
    cd scripts && python3 combine_results.py
fi

echo "Benchmark suite finished successfully!"