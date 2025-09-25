#!/usr/bin/env python3

import time
import json
import sys
import psutil
import os
import random
import numpy as np
from typing import List, Dict, Any

# Qiskit imports
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import QFT
import qiskit

class BenchmarkResult:
    def __init__(self, name: str, num_qubits: int, num_gates: int, 
                 execution_time_ms: float, memory_usage_mb: float, circuit_depth: int):
        self.name = name
        self.num_qubits = num_qubits
        self.num_gates = num_gates
        self.execution_time_ms = execution_time_ms
        self.memory_usage_mb = memory_usage_mb
        self.circuit_depth = circuit_depth
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "num_qubits": self.num_qubits,
            "num_gates": self.num_gates,
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "circuit_depth": self.circuit_depth
        }

class BenchmarkSuite:
    def __init__(self, library: str, version: str, results: List[BenchmarkResult], total_time_ms: float):
        self.library = library
        self.version = version
        self.results = results
        self.total_time_ms = total_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "library": self.library,
            "version": self.version,
            "results": [result.to_dict() for result in self.results],
            "total_time_ms": self.total_time_ms
        }

def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def benchmark_ghz_state(num_qubits: int) -> BenchmarkResult:
    """Benchmark GHZ state creation"""
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Create GHZ state circuit
    circuit = QuantumCircuit(num_qubits)
    circuit.h(0)
    for i in range(1, num_qubits):
        circuit.cx(0, i)
    
    # Execute circuit using statevector simulator
    statevector = Statevector.from_instruction(circuit)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    execution_time = (end_time - start_time) * 1000  # Convert to ms
    memory_usage = end_memory - start_memory
    
    return BenchmarkResult(
        name=f"GHZ-{num_qubits}",
        num_qubits=num_qubits,
        num_gates=num_qubits,  # 1 H + (n-1) CNOT
        execution_time_ms=execution_time,
        memory_usage_mb=memory_usage,
        circuit_depth=2
    )

def benchmark_random_circuit(num_qubits: int, num_gates: int) -> BenchmarkResult:
    """Benchmark random quantum circuit"""
    start_memory = get_memory_usage()
    start_time = time.time()
    
    random.seed(42)  # For reproducibility
    
    circuit = QuantumCircuit(num_qubits)
    
    # Add random single-qubit gates
    for _ in range(num_gates):
        gate_type = random.randint(0, 5)
        qubit = random.randint(0, num_qubits - 1)
        angle = random.uniform(0, 2 * np.pi)
        
        if gate_type == 0:
            circuit.h(qubit)
        elif gate_type == 1:
            circuit.x(qubit)
        elif gate_type == 2:
            circuit.y(qubit)
        elif gate_type == 3:
            circuit.z(qubit)
        elif gate_type == 4:
            circuit.rx(angle, qubit)
        else:
            circuit.ry(angle, qubit)
    
    # Add some CNOT gates for entanglement
    num_cnots = num_gates // 4
    for _ in range(num_cnots):
        control = random.randint(0, num_qubits - 1)
        target = random.randint(0, num_qubits - 1)
        while target == control:
            target = random.randint(0, num_qubits - 1)
        circuit.cx(control, target)
    
    # Execute circuit
    statevector = Statevector.from_instruction(circuit)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    execution_time = (end_time - start_time) * 1000
    memory_usage = end_memory - start_memory
    
    return BenchmarkResult(
        name=f"Random-{num_qubits}-{num_gates}",
        num_qubits=num_qubits,
        num_gates=num_gates + num_cnots,
        execution_time_ms=execution_time,
        memory_usage_mb=memory_usage,
        circuit_depth=circuit.depth()
    )

def benchmark_qft_circuit(num_qubits: int) -> BenchmarkResult:
    """Benchmark Quantum Fourier Transform circuit"""
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Create QFT circuit using Qiskit's built-in QFT
    qft = QFT(num_qubits, approximation_degree=0, do_swaps=True)
    circuit = QuantumCircuit(num_qubits)
    circuit.compose(qft, inplace=True)
    
    # Execute circuit
    statevector = Statevector.from_instruction(circuit)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    execution_time = (end_time - start_time) * 1000
    memory_usage = end_memory - start_memory
    
    # Estimate number of gates (QFT has O(n^2) gates)
    num_gates = num_qubits + (num_qubits * (num_qubits - 1)) // 2 * 2
    
    return BenchmarkResult(
        name=f"QFT-{num_qubits}",
        num_qubits=num_qubits,
        num_gates=num_gates,
        execution_time_ms=execution_time,
        memory_usage_mb=memory_usage,
        circuit_depth=circuit.depth()
    )

def main():
    suite_start = time.time()
    results = []
    
    print("Starting Qiskit benchmarks...", file=sys.stderr)
    
    # Test different qubit sizes
    qubit_sizes = [4, 6, 8, 10, 12]
    
    for num_qubits in qubit_sizes:
        if num_qubits <= 14:  # Limit for exponential memory growth
            print(f"Benchmarking {num_qubits} qubits...", file=sys.stderr)
            
            # GHZ state benchmark
            results.append(benchmark_ghz_state(num_qubits))
            
            # Random circuit benchmark
            gate_count = num_qubits * 10
            results.append(benchmark_random_circuit(num_qubits, gate_count))
            
            # QFT benchmark (only for smaller systems due to complexity)
            if num_qubits <= 10:
                results.append(benchmark_qft_circuit(num_qubits))
    
    suite_end = time.time()
    total_time = (suite_end - suite_start) * 1000  # Convert to ms
    
    benchmark_suite = BenchmarkSuite(
        library="Qiskit",
        version=qiskit.__version__,
        results=results,
        total_time_ms=total_time
    )
    
    print(json.dumps(benchmark_suite.to_dict(), indent=2))
    print(f"Qiskit benchmarks completed in {total_time:.2f}ms", file=sys.stderr)

if __name__ == "__main__":
    main()