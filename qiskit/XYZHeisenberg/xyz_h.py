"""
XYZ-Heisenberg Model Benchmark for Qiskit.

This benchmark measures the performance of simulating the XYZ-Heisenberg model
using Qiskit. The Hamiltonian is:
H = -Σᵢⱼ [Jₓ XᵢXⱼ + Jᵧ YᵢYⱼ + Jᵧ ZᵢZⱼ] - h Σᵢ Zᵢ

This benchmark measures:
- Circuit execution time
- Energy expectation values
- Resource usage
"""

import json
import os
import time
from typing import List

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import RXXGate, RYYGate, RZZGate, RZGate
from qiskit.quantum_info import SparsePauliOp, Statevector


def create_xyz_heisenberg_hamiltonian(
    num_qubits: int, jx: float, jy: float, jz: float, external_field: float
) -> SparsePauliOp:
    """
    Create the XYZ Heisenberg Hamiltonian for a 1D chain with nearest-neighbor interactions.
    
    H = -Σᵢ [Jₓ XᵢXᵢ₊₁ + Jᵧ YᵢYᵢ₊₁ + Jᵧ ZᵢZᵢ₊₁] - h Σᵢ Zᵢ
    """
    terms: List[tuple] = []
    
    # Nearest-neighbor interactions (chain topology)
    for i in range(num_qubits - 1):
        # XX interaction
        if abs(jx) > 1e-10:
            label = ["I"] * num_qubits
            label[i] = "X"
            label[i + 1] = "X"
            terms.append(("".join(label), -jx))
        
        # YY interaction
        if abs(jy) > 1e-10:
            label = ["I"] * num_qubits
            label[i] = "Y"
            label[i + 1] = "Y"
            terms.append(("".join(label), -jy))
        
        # ZZ interaction
        if abs(jz) > 1e-10:
            label = ["I"] * num_qubits
            label[i] = "Z"
            label[i + 1] = "Z"
            terms.append(("".join(label), -jz))
    
    # External magnetic field (Z direction)
    if abs(external_field) > 1e-10:
        for i in range(num_qubits):
            label = ["I"] * num_qubits
            label[i] = "Z"
            terms.append(("".join(label), -external_field))
    
    # If no operators, return identity with zero coefficient
    if not terms:
        return SparsePauliOp.from_list([("I" * num_qubits, 0.0)])
    
    return SparsePauliOp.from_list(terms)


def calculate_energy(state: Statevector, hamiltonian: SparsePauliOp) -> float:
    """Calculate the expectation value of the Hamiltonian for a given state."""
    # Get Hamiltonian matrix
    h_matrix = hamiltonian.to_matrix()
    
    # Get state vector
    state_vector = state.data
    
    # Calculate <ψ|H|ψ> = state_vector^H @ h_matrix @ state_vector
    energy = np.real(np.vdot(state_vector, h_matrix @ state_vector))
    return float(energy)


def build_time_evolution_circuit(
    num_qubits: int,
    hamiltonian: SparsePauliOp,
    time_steps: int,
    dt: float,
) -> QuantumCircuit:
    """
    Build a circuit that implements time evolution using Trotterization.
    Manually implements first-order Trotter decomposition.
    """
    circuit = QuantumCircuit(num_qubits)
    
    # Prepare initial state: |1111...⟩ (all spins up)
    for i in range(num_qubits):
        circuit.x(i)
    
    # Apply time evolution using Trotterization
    # For each time step, apply exp(-i*H*dt) ≈ ∏ exp(-i*H_i*dt)
    for _ in range(time_steps):
        # Get Hamiltonian terms
        for pauli, coeff in zip(hamiltonian.paulis, hamiltonian.coeffs):
            # Skip identity terms
            if pauli.num_qubits == 0:
                continue
            
            # Find non-identity Pauli operators
            non_id_indices = []
            pauli_labels = []
            for i in range(pauli.num_qubits):
                label = pauli[i]
                if label != "I":
                    non_id_indices.append(i)
                    pauli_labels.append(label)
            
            if len(non_id_indices) == 0:
                continue
            
            # Apply rotation gates based on Pauli operators
            if len(non_id_indices) == 1:
                # Single-qubit rotation
                qubit = non_id_indices[0]
                angle = 2 * float(coeff.real) * dt
                if pauli_labels[0] == "X":
                    circuit.rx(angle, qubit)
                elif pauli_labels[0] == "Y":
                    circuit.ry(angle, qubit)
                elif pauli_labels[0] == "Z":
                    circuit.rz(angle, qubit)
            elif len(non_id_indices) == 2:
                # Two-qubit rotation (XX, YY, or ZZ)
                q1, q2 = non_id_indices[0], non_id_indices[1]
                angle = 2 * float(coeff.real) * dt
                if pauli_labels[0] == "X" and pauli_labels[1] == "X":
                    circuit.append(RXXGate(angle), [q1, q2])
                elif pauli_labels[0] == "Y" and pauli_labels[1] == "Y":
                    circuit.append(RYYGate(angle), [q1, q2])
                elif pauli_labels[0] == "Z" and pauli_labels[1] == "Z":
                    circuit.append(RZZGate(angle), [q1, q2])
    
    return circuit


def run_xyz_heisenberg_benchmark(
    num_qubits: int,
    jx: float = 1.0,
    jy: float = 1.0,
    jz: float = 1.0,
    external_field: float = 0.0,
    time_steps: int = 10,
    dt: float = 0.1,
) -> dict:
    """
    Run the XYZ Heisenberg model benchmark.
    
    Returns a dictionary with benchmark results.
    """
    # Create Hamiltonian
    hamiltonian = create_xyz_heisenberg_hamiltonian(
        num_qubits, jx, jy, jz, external_field
    )
    
    # Prepare initial state: |1111...⟩
    initial_state_vector = np.zeros(2**num_qubits, dtype=complex)
    initial_state_vector[-1] = 1.0  # |1111...⟩ is the last basis state
    initial_state = Statevector(initial_state_vector)
    
    # Calculate initial energy
    initial_energy = calculate_energy(initial_state, hamiltonian)
    
    # Build circuit
    circuit = build_time_evolution_circuit(num_qubits, hamiltonian, time_steps, dt)
    
    # Measure execution time
    start = time.perf_counter()
    final_state = Statevector.from_instruction(circuit)
    runtime_ms = (time.perf_counter() - start) * 1e3
    
    # Calculate final energy
    final_energy = calculate_energy(final_state, hamiltonian)
    energy_change = final_energy - initial_energy
    
    # Count operations (approximate: each time step has Trotter steps)
    # For nearest-neighbor interactions: 3*(n-1) terms per time step
    num_interactions = 3 * (num_qubits - 1) if num_qubits > 1 else 0
    num_field_terms = num_qubits if abs(external_field) > 1e-10 else 0
    num_operations = time_steps * (num_interactions + num_field_terms) + num_qubits  # +num_qubits for initial X gates
    
    return {
        "framework": "Qiskit (Python)",
        "qubits": num_qubits,
        "time_steps": time_steps,
        "dt": round(dt, 6),
        "jx": round(jx, 6),
        "jy": round(jy, 6),
        "jz": round(jz, 6),
        "external_field": round(external_field, 6),
        "initial_energy": round(initial_energy, 10),
        "final_energy": round(final_energy, 10),
        "energy_change": round(energy_change, 10),
        "runtime_ms": round(runtime_ms, 2),
        "num_operations": num_operations,
    }


def main():
    """Main entry point for the benchmark."""
    # Parse configuration from environment variables
    num_qubits = int(os.environ.get("XYZ_QUBITS", "4"))
    time_steps = int(os.environ.get("XYZ_STEPS", "10"))
    dt = float(os.environ.get("XYZ_DT", "0.1"))
    jx = float(os.environ.get("XYZ_JX", "1.0"))
    jy = float(os.environ.get("XYZ_JY", "1.0"))
    jz = float(os.environ.get("XYZ_JZ", "1.0"))
    external_field = float(os.environ.get("XYZ_FIELD", "0.0"))
    
    # Run benchmark
    result = run_xyz_heisenberg_benchmark(
        num_qubits=num_qubits,
        jx=jx,
        jy=jy,
        jz=jz,
        external_field=external_field,
        time_steps=time_steps,
        dt=dt,
    )
    
    # Write to JSON file
    output_file = os.environ.get("XYZ_OUTPUT_FILE", "qiskit_xyz_heisenberg.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()

