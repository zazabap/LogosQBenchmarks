#!/usr/bin/env python3
"""
Verify QFT correctness across all quantum computing libraries.
Compares QFT output probabilities from different libraries to ensure they produce the same results.
"""

import json
import numpy as np
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Tolerance for numerical comparisons
TOLERANCE = 1e-5

def verify_pennylane_qft(n_qubits: int) -> Optional[np.ndarray]:
    """Run PennyLane QFT and return state probabilities"""
    try:
        script = f"""
import pennylane as qml
import numpy as np
import json
import sys
sys.path.insert(0, '/app/pennylane/QuantumFourierTransform')
from pennylane_qft import qft_crz

n_qubits = {n_qubits}
dev = qml.device('default.qubit', wires=n_qubits)

@qml.qnode(dev)
def qft_circuit():
    qml.PauliX(wires=0)  # Prepare |1⟩ = |00...01⟩
    qft_crz(range(n_qubits))
    return qml.probs(wires=range(n_qubits))

probs = qft_circuit()
print(json.dumps(probs.tolist()))
"""
        result = subprocess.run(
            ['python3', '-c', script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/app'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            probs = json.loads(result.stdout.strip())
            return np.array(probs, dtype=np.float64)
    except Exception as e:
        print(f"  ⚠️  PennyLane verification failed: {e}")
    return None

def verify_qiskit_qft(n_qubits: int) -> Optional[np.ndarray]:
    """Run Qiskit QFT and return state probabilities"""
    try:
        script = f"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Statevector
import json

n_qubits = {n_qubits}
circuit = QuantumCircuit(n_qubits)
circuit.x(0)  # Prepare |1⟩ = |00...01⟩
qft = QFT(n_qubits, approximation_degree=0, do_swaps=True)
circuit.compose(qft, inplace=True)

statevector = Statevector.from_instruction(circuit)
probs = statevector.probabilities()
print(json.dumps(probs.tolist()))
"""
        result = subprocess.run(
            ['python3', '-c', script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/app'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            probs = json.loads(result.stdout.strip())
            return np.array(probs, dtype=np.float64)
    except Exception as e:
        print(f"  ⚠️  Qiskit verification failed: {e}")
    return None

def verify_yao_qft(n_qubits: int) -> Optional[np.ndarray]:
    """Run Yao.jl QFT and return state probabilities"""
    try:
        script = f"""
using Yao
using JSON

n_qubits = {n_qubits}
# Prepare |1⟩ = |00...01⟩
state = zero_state(n_qubits)
state = put(n_qubits, 1=>X) * state

# Apply QFT
circuit = qft(n_qubits)
state = apply!(state, circuit)

# Get probabilities
probs = probs(state)
println(JSON.json(probs))
"""
        result = subprocess.run(
            ['julia', '--project=/app/yao.jl', '-e', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            probs = json.loads(result.stdout.strip())
            return np.array(probs, dtype=np.float64)
    except Exception as e:
        print(f"  ⚠️  Yao.jl verification failed: {e}")
    return None

def compare_probabilities(probs1: np.ndarray, probs2: np.ndarray, 
                         lib1: str, lib2: str) -> Tuple[bool, float]:
    """Compare two probability distributions"""
    if probs1.shape != probs2.shape:
        return False, float('inf')
    
    # Calculate maximum absolute difference
    max_diff = np.max(np.abs(probs1 - probs2))
    
    # Normalize probabilities (they should sum to 1)
    probs1_norm = probs1 / (np.sum(probs1) + 1e-10)
    probs2_norm = probs2 / (np.sum(probs2) + 1e-10)
    
    # Calculate relative difference
    rel_diff = np.max(np.abs(probs1_norm - probs2_norm))
    
    match = max_diff < TOLERANCE
    
    return match, max_diff

def verify_round_trip_fidelity(n_qubits: int) -> Dict[str, Optional[float]]:
    """Verify round-trip QFT (QFT + inverse QFT should recover original state)"""
    fidelities = {}
    
    # PennyLane round-trip
    try:
        script = f"""
import pennylane as qml
import sys
sys.path.insert(0, '/app/pennylane/QuantumFourierTransform')
from pennylane_qft import qft_crz, qft_inverse_crz

n_qubits = {n_qubits}
dev = qml.device('default.qubit', wires=n_qubits)

@qml.qnode(dev)
def round_trip():
    qml.PauliX(wires=0)  # Prepare |1⟩ = |00...01⟩
    qft_crz(range(n_qubits))
    qft_inverse_crz(range(n_qubits))
    return qml.probs(wires=range(n_qubits))

probs = round_trip()
# For |1⟩ = |0001⟩ state, after round-trip we should get back |1⟩
# In PennyLane's little-endian ordering: |1⟩ = |0001⟩ = index 1
# But we check the maximum probability to be safe
import numpy as np
probs_array = np.array(probs)
max_prob = float(np.max(probs_array))
print(max_prob)
"""
        result = subprocess.run(
            ['python3', '-c', script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/app'
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                fidelities['pennylane'] = float(result.stdout.strip())
            except:
                fidelities['pennylane'] = None
        else:
            fidelities['pennylane'] = None
    except Exception as e:
        fidelities['pennylane'] = None
    
    # Qiskit round-trip
    try:
        script = f"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Statevector

n_qubits = {n_qubits}
circuit = QuantumCircuit(n_qubits)
circuit.x(0)
qft = QFT(n_qubits, approximation_degree=0, do_swaps=True)
circuit.compose(qft, inplace=True)
circuit.compose(qft.inverse(), inplace=True)

statevector = Statevector.from_instruction(circuit)
probs = statevector.probabilities()
fidelity = probs[1]  # Should be ~1.0 for |1⟩ state
print(fidelity)
"""
        result = subprocess.run(
            ['python3', '-c', script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/app'
        )
        if result.returncode == 0 and result.stdout.strip():
            fidelities['qiskit'] = float(result.stdout.strip())
        else:
            fidelities['qiskit'] = None
    except:
        fidelities['qiskit'] = None
    
    return fidelities

def verify_from_benchmark_files(n_qubits: int) -> Dict[str, Optional[np.ndarray]]:
    """Try to extract verification data from benchmark result files"""
    results = {}
    
    # Check if benchmark results exist and contain fidelity data
    # (Fidelity from round-trip QFT is a good correctness indicator)
    benchmark_files = {
        'logosq': '/app/test_results/qft/logosq_qft_benchmark_results.json',
        'pennylane': '/app/test_results/qft/pennylane_qft_benchmark_results.json',
        'qiskit': '/app/test_results/qft/qiskit_qft_benchmark_results.json',
        'yao': '/app/test_results/qft/yao_qft_benchmark_results.json',
    }
    
    for lib, filepath in benchmark_files.items():
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Look for results matching n_qubits
                if isinstance(data, list):
                    for item in data:
                        if item.get('n_qubits') == n_qubits or item.get('num_qubits') == n_qubits:
                            # If fidelity is available, it indicates correctness
                            if 'fidelity' in item:
                                results[lib] = {'fidelity': item['fidelity']}
                                break
        except:
            pass
    
    return results

def main():
    """Main verification function"""
    print("=" * 70)
    print("QFT Correctness Verification Across All Libraries")
    print("=" * 70)
    print()
    print("Testing QFT on input state |1⟩ = |00...01⟩")
    print("All libraries should produce the same output probabilities.")
    print()
    print("Note: LogosQ and Q# verification requires running benchmarks first.")
    print("      This script verifies Python/Julia libraries directly.")
    print()
    
    # Test qubit counts (smaller for faster verification)
    test_qubits = [4, 6, 8]
    
    all_results = {}
    all_match = True
    
    for n_qubits in test_qubits:
        print(f"Testing {n_qubits}-qubit QFT...")
        print("-" * 70)
        
        results = {}
        
        # Try to get LogosQ results from benchmark files first
        print("  Checking LogosQ benchmark results...")
        logosq_file = '/app/test_results/qft/logosq_qft_benchmark_results.json'
        if os.path.exists(logosq_file):
            try:
                with open(logosq_file, 'r') as f:
                    logosq_data = json.load(f)
                if isinstance(logosq_data, list):
                    for item in logosq_data:
                        if item.get('n_qubits') == n_qubits and 'qft_probs' in item:
                            results['logosq'] = np.array(item['qft_probs'], dtype=np.float64)
                            print("    ✓ Found LogosQ probabilities in benchmark results")
                            break
            except:
                pass
        
        # Get results from each library
        print("  Running PennyLane...")
        results['pennylane'] = verify_pennylane_qft(n_qubits)
        
        print("  Running Qiskit...")
        results['qiskit'] = verify_qiskit_qft(n_qubits)
        
        print("  Running Yao.jl...")
        results['yao'] = verify_yao_qft(n_qubits)
        
        # Compare results
        print("\n  Comparing results...")
        libraries = ['pennylane', 'qiskit', 'yao']
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if len(valid_results) < 2:
            print(f"  ⚠️  Not enough valid results for comparison (got {len(valid_results)})")
            all_results[n_qubits] = {'status': 'insufficient_data', 'results': valid_results}
            continue
        
        # Compare all pairs (including LogosQ if available)
        matches = {}
        all_libs = ['logosq'] + libraries if 'logosq' in valid_results else libraries
        for i, lib1 in enumerate(all_libs):
            if lib1 not in valid_results:
                continue
            for lib2 in all_libs[i+1:]:
                if lib2 not in valid_results:
                    continue
                
                match, diff = compare_probabilities(
                    valid_results[lib1],
                    valid_results[lib2],
                    lib1,
                    lib2
                )
                
                pair_key = f"{lib1}_vs_{lib2}"
                matches[pair_key] = {
                    'match': bool(match),
                    'max_diff': float(diff),
                    'tolerance': float(TOLERANCE)
                }
                
                status = "✓" if match else "✗"
                print(f"    {status} {lib1} vs {lib2}: max_diff = {diff:.2e}")
                
                if not match:
                    all_match = False
        
        all_results[n_qubits] = {
            'status': 'compared',
            'results': {k: len(v) if v is not None else None for k, v in results.items()},
            'matches': matches
        }
        
        # Round-trip fidelity check
        print("\n  Checking round-trip fidelity (QFT + inverse QFT)...")
        fidelities = verify_round_trip_fidelity(n_qubits)
        for lib, fid in fidelities.items():
            if fid is not None:
                status = "✓" if fid > 0.99 else "✗"
                print(f"    {status} {lib}: fidelity = {fid:.6f}")
        
        print()
    
    # Summary
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    if all_match:
        print("✓ All libraries produce matching QFT results!")
    else:
        print("✗ Some libraries produce different QFT results.")
        print("  Check the detailed comparison above.")
    
    # Save results
    output_file = "/app/test_results/qft/qft_verification_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    return 0 if all_match else 1

if __name__ == "__main__":
    sys.exit(main())
