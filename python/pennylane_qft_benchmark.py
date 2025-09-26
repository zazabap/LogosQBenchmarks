import pennylane as qml
import numpy as np
import time
import json
import psutil
import os
from math import pi
from typing import Dict, List, Tuple

# Import QFT functions from the original file
from pennylane_qft import qft_crz, qft_inverse_crz

class QFTBenchmark:
    """Comprehensive benchmarking class for QFT performance analysis"""
    
    def __init__(self):
        self.results = []
        self.system_info = self.get_system_info()
    
    def get_system_info(self) -> Dict:
        """Get system information for benchmark context"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "pennylane_version": qml.version()
        }
    
    def measure_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def count_gates_in_qft(self, n_qubits: int) -> Dict[str, int]:
        """Count gates in QFT circuit for theoretical analysis"""
        # Theoretical gate counts for QFT
        hadamard_gates = n_qubits
        crz_gates = sum(range(n_qubits))  # n*(n-1)/2
        swap_gates = n_qubits // 2
        
        return {
            "Hadamard": hadamard_gates,
            "CRZ": crz_gates,
            "SWAP": swap_gates,
            "total": hadamard_gates + crz_gates + swap_gates
        }
    
    def benchmark_qft_circuit(self, n_qubits: int, num_trials: int = 5) -> Dict:
        """Benchmark QFT circuit for given number of qubits"""
        print(f"Benchmarking {n_qubits}-qubit QFT...")
        
        # Create device
        dev = qml.device("default.qubit", wires=n_qubits)
        
        @qml.qnode(dev)
        def qft_circuit():
            # Prepare a simple input state
            qml.PauliX(wires=0)
            qft_crz(range(n_qubits))
            return qml.probs(wires=range(n_qubits))
        
        # Warm-up run
        _ = qft_circuit()
        
        # Get actual gate counts from the circuit
        tape = qft_circuit.tape
        actual_gate_counts = {}
        for op in tape.operations:
            gate_name = op.name
            actual_gate_counts[gate_name] = actual_gate_counts.get(gate_name, 0) + 1
        
        # Performance measurements
        execution_times = []
        memory_usage_before = []
        memory_usage_after = []
        
        for trial in range(num_trials):
            # Measure memory before
            mem_before = self.measure_memory_usage()
            memory_usage_before.append(mem_before)
            
            # Measure execution time
            start_time = time.perf_counter()
            result = qft_circuit()
            end_time = time.perf_counter()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            execution_times.append(execution_time)
            
            # Measure memory after
            mem_after = self.measure_memory_usage()
            memory_usage_after.append(mem_after)
        
        # Calculate statistics
        theoretical_gates = self.count_gates_in_qft(n_qubits)
        
        return {
            "n_qubits": n_qubits,
            "execution_time_ms": {
                "mean": np.mean(execution_times),
                "std": np.std(execution_times),
                "min": np.min(execution_times),
                "max": np.max(execution_times),
                "median": np.median(execution_times)
            },
            "memory_usage_mb": {
                "before_mean": np.mean(memory_usage_before),
                "after_mean": np.mean(memory_usage_after),
                "delta_mean": np.mean(memory_usage_after) - np.mean(memory_usage_before)
            },
            "gate_counts": {
                "theoretical": theoretical_gates,
                "actual": actual_gate_counts,
                "total_actual": sum(actual_gate_counts.values())
            },
            "circuit_depth": len(tape.operations),
            "state_vector_size": 2**n_qubits,
            "num_trials": num_trials
        }
    
    def benchmark_qft_inverse_circuit(self, n_qubits: int, num_trials: int = 5) -> Dict:
        """Benchmark QFT + Inverse QFT circuit (round-trip test)"""
        print(f"Benchmarking {n_qubits}-qubit QFT + Inverse QFT...")
        
        dev = qml.device("default.qubit", wires=n_qubits)
        
        @qml.qnode(dev)
        def qft_inverse_circuit():
            qml.PauliX(wires=0)
            qft_crz(range(n_qubits))
            qft_inverse_crz(range(n_qubits))
            return qml.probs(wires=range(n_qubits))
        
        # Warm-up
        _ = qft_inverse_circuit()
        
        # Get gate counts
        tape = qft_inverse_circuit.tape
        gate_counts = {}
        for op in tape.operations:
            gate_name = op.name
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
        
        execution_times = []
        fidelities = []
        
        for trial in range(num_trials):
            start_time = time.perf_counter()
            result = qft_inverse_circuit()
            end_time = time.perf_counter()
            
            execution_time = (end_time - start_time) * 1000
            execution_times.append(execution_time)
            
            # Check fidelity (should recover |001...⟩ state)
            expected_state_idx = 1  # Binary 1 = |001...⟩
            fidelity = result[expected_state_idx]
            fidelities.append(fidelity)
        
        return {
            "n_qubits": n_qubits,
            "execution_time_ms": {
                "mean": np.mean(execution_times),
                "std": np.std(execution_times),
                "min": np.min(execution_times),
                "max": np.max(execution_times)
            },
            "fidelity": {
                "mean": np.mean(fidelities),
                "std": np.std(fidelities),
                "min": np.min(fidelities)
            },
            "total_gates": sum(gate_counts.values()),
            "circuit_depth": len(tape.operations)
        }
    
    def run_comprehensive_benchmark(self, qubit_range: range, num_trials: int = 5):
        """Run comprehensive benchmark across qubit range"""
        print("Starting Comprehensive QFT Benchmark")
        print("=" * 60)
        print(f"System Info: {self.system_info}")
        print(f"Testing qubits: {list(qubit_range)}")
        print(f"Trials per test: {num_trials}")
        print("=" * 60)
        
        for n_qubits in qubit_range:
            try:
                # QFT-only benchmark
                qft_result = self.benchmark_qft_circuit(n_qubits, num_trials)
                
                # QFT + Inverse benchmark (for smaller systems)
                if n_qubits <= 15:  # Limit for round-trip tests
                    inverse_result = self.benchmark_qft_inverse_circuit(n_qubits, num_trials)
                else:
                    inverse_result = None
                
                # Store results
                benchmark_entry = {
                    "qft_only": qft_result,
                    "qft_inverse": inverse_result,
                    "timestamp": time.time()
                }
                
                self.results.append(benchmark_entry)
                
                # Print summary for this qubit count
                self.print_benchmark_summary(qft_result, inverse_result)
                
            except Exception as e:
                print(f"Error benchmarking {n_qubits} qubits: {e}")
                continue
        
        # Generate final report
        self.generate_report()
    
    def print_benchmark_summary(self, qft_result: Dict, inverse_result: Dict = None):
        """Print summary for a single benchmark"""
        n_qubits = qft_result["n_qubits"]
        
        print(f"\n--- {n_qubits} Qubit Results ---")
        print(f"QFT Execution Time: {qft_result['execution_time_ms']['mean']:.3f} ± {qft_result['execution_time_ms']['std']:.3f} ms")
        print(f"Memory Usage: {qft_result['memory_usage_mb']['delta_mean']:.2f} MB")
        print(f"Total Gates: {qft_result['gate_counts']['total_actual']}")
        print(f"Circuit Depth: {qft_result['circuit_depth']}")
        print(f"State Vector Size: {qft_result['state_vector_size']:,}")
        
        if inverse_result:
            print(f"QFT+IQFT Time: {inverse_result['execution_time_ms']['mean']:.3f} ± {inverse_result['execution_time_ms']['std']:.3f} ms")
            print(f"Fidelity: {inverse_result['fidelity']['mean']:.6f}")
        
        print("-" * 40)
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        report = {
            "benchmark_info": {
                "timestamp": time.time(),
                "system_info": self.system_info,
                "total_tests": len(self.results)
            },
            "results": self.results,
            "summary": self.generate_summary_statistics()
        }
        
        # Save to JSON
        output_file = "/app/python/qft_benchmark_results.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Benchmark Report Generated")
        print(f"Results saved to: {output_file}")
        
        # Print performance scaling analysis
        self.print_scaling_analysis()
    
    def generate_summary_statistics(self) -> Dict:
        """Generate summary statistics across all tests"""
        qft_times = []
        gate_counts = []
        qubit_counts = []
        
        for result in self.results:
            qft_data = result["qft_only"]
            qft_times.append(qft_data["execution_time_ms"]["mean"])
            gate_counts.append(qft_data["gate_counts"]["total_actual"])
            qubit_counts.append(qft_data["n_qubits"])
        
        return {
            "execution_time_scaling": {
                "min_time_ms": min(qft_times) if qft_times else 0,
                "max_time_ms": max(qft_times) if qft_times else 0,
                "time_range_factor": max(qft_times) / min(qft_times) if qft_times and min(qft_times) > 0 else 0
            },
            "gate_count_scaling": {
                "min_gates": min(gate_counts) if gate_counts else 0,
                "max_gates": max(gate_counts) if gate_counts else 0,
                "gates_range_factor": max(gate_counts) / min(gate_counts) if gate_counts and min(gate_counts) > 0 else 0
            },
            "qubit_range": {
                "min_qubits": min(qubit_counts) if qubit_counts else 0,
                "max_qubits": max(qubit_counts) if qubit_counts else 0
            }
        }
    
    def print_scaling_analysis(self):
        """Print performance scaling analysis"""
        print("\n📈 Performance Scaling Analysis")
        print("=" * 50)
        
        if len(self.results) < 2:
            print("Not enough data for scaling analysis")
            return
        
        # Extract data for analysis
        data = []
        for result in self.results:
            qft_data = result["qft_only"]
            data.append({
                "qubits": qft_data["n_qubits"],
                "time_ms": qft_data["execution_time_ms"]["mean"],
                "gates": qft_data["gate_counts"]["total_actual"],
                "memory_mb": qft_data["memory_usage_mb"]["delta_mean"],
                "state_size": qft_data["state_vector_size"]
            })
        
        # Sort by qubit count
        data.sort(key=lambda x: x["qubits"])
        
        print("Qubit | Time (ms) | Gates | Memory (MB) | State Size")
        print("-" * 55)
        for d in data:
            print(f"{d['qubits']:5d} | {d['time_ms']:9.3f} | {d['gates']:5d} | {d['memory_mb']:11.2f} | {d['state_size']:10,d}")
        
        # Calculate scaling factors
        if len(data) >= 2:
            first, last = data[0], data[-1]
            qubit_factor = last["qubits"] / first["qubits"]
            time_factor = last["time_ms"] / first["time_ms"] if first["time_ms"] > 0 else 0
            gate_factor = last["gates"] / first["gates"] if first["gates"] > 0 else 0
            
            print(f"\nScaling from {first['qubits']} to {last['qubits']} qubits:")
            print(f"• Qubit factor: {qubit_factor:.1f}x")
            print(f"• Time factor: {time_factor:.1f}x")
            print(f"• Gate factor: {gate_factor:.1f}x")
            print(f"• Theoretical gate scaling: O(n²) = {qubit_factor**2:.1f}x")

def main():
    """Main benchmarking function"""
    benchmark = QFTBenchmark()
    
    # Test different ranges based on system capabilities
    print("Select benchmark range:")
    print("1. Small (1-8 qubits) - Fast test")
    print("2. Medium (1-12 qubits) - Moderate test") 
    print("3. Large (1-16 qubits) - Comprehensive test")
    print("4. Custom range")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        qubit_range = range(1, 9)
        trials = 10
    elif choice == "2":
        qubit_range = range(1, 13)
        trials = 5
    elif choice == "3":
        qubit_range = range(1, 17)
        trials = 3
    elif choice == "4":
        start = int(input("Start qubits: "))
        end = int(input("End qubits: ")) + 1
        trials = int(input("Trials per test: "))
        qubit_range = range(start, end)
    else:
        print("Invalid choice, using default small range")
        qubit_range = range(1, 9)
        trials = 5
    
    # Run benchmark
    benchmark.run_comprehensive_benchmark(qubit_range, trials)

if __name__ == "__main__":
    main()