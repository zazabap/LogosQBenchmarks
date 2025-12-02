"""
XYZ-Heisenberg Model Benchmark for PennyLane.

This benchmark measures the performance of simulating the XYZ-Heisenberg model
using PennyLane. The Hamiltonian is:
H = -Σᵢⱼ [Jₓ XᵢXⱼ + Jᵧ YᵢYⱼ + Jᵧ ZᵢZⱼ] - h Σᵢ Zᵢ

This benchmark measures:
- Circuit execution time
- Energy expectation values
- Resource usage
"""

import json
import os
import time
from typing import List, Tuple

import numpy as np
import pennylane as qml
import psutil


def create_xyz_heisenberg_hamiltonian(
    num_qubits: int, jx: float, jy: float, jz: float, external_field: float
) -> qml.Hamiltonian:
    """
    Create the XYZ Heisenberg Hamiltonian for a 1D chain with nearest-neighbor interactions.
    
    H = -Σᵢ [Jₓ XᵢXᵢ₊₁ + Jᵧ YᵢYᵢ₊₁ + Jᵧ ZᵢZᵢ₊₁] - h Σᵢ Zᵢ
    """
    coeffs: List[float] = []
    ops: List[qml.operation.Operator] = []
    
    # Nearest-neighbor interactions (chain topology)
    for i in range(num_qubits - 1):
        # XX interaction
        if abs(jx) > 1e-10:
            coeffs.append(-jx)
            ops.append(qml.PauliX(i) @ qml.PauliX(i + 1))
        
        # YY interaction
        if abs(jy) > 1e-10:
            coeffs.append(-jy)
            ops.append(qml.PauliY(i) @ qml.PauliY(i + 1))
        
        # ZZ interaction
        if abs(jz) > 1e-10:
            coeffs.append(-jz)
            ops.append(qml.PauliZ(i) @ qml.PauliZ(i + 1))
    
    # External magnetic field (Z direction)
    if abs(external_field) > 1e-10:
        for i in range(num_qubits):
            coeffs.append(-external_field)
            ops.append(qml.PauliZ(i))
    
    # If no operators, return identity with zero coefficient
    if not ops:
        return qml.Hamiltonian([0.0], [qml.Identity(0)])
    
    return qml.Hamiltonian(coeffs, ops)


def calculate_energy(state: np.ndarray, hamiltonian: qml.Hamiltonian, num_qubits: int) -> float:
    """Calculate the expectation value of the Hamiltonian for a given state."""
    # Convert state to density matrix if needed
    if len(state.shape) == 1:
        # Pure state: |ψ⟩⟨ψ|
        state_dm = np.outer(state, np.conj(state))
    else:
        state_dm = state
    
    # Get Hamiltonian matrix
    h_matrix = qml.matrix(hamiltonian, wire_order=range(num_qubits))
    
    # Calculate Tr(H * ρ)
    energy = np.trace(h_matrix @ state_dm).real
    return float(energy)


def build_time_evolution_circuit(
    num_qubits: int,
    hamiltonian: qml.Hamiltonian,
    time_steps: int,
    dt: float,
    jx: float,
    jy: float,
    jz: float,
    time_dependent_field: bool = False,
    field_amplitude: float = 0.0,
    field_frequency: float = 1.0,
) -> qml.QNode:
    """
    Build a circuit that implements time evolution using Trotterization.
    
    If time_dependent_field is True, adds a time-dependent external field
    h(t) = field_amplitude * sin(field_frequency * t) to break energy conservation.
    """
    dev = qml.device("default.qubit", wires=num_qubits)
    
    @qml.qnode(dev)
    def circuit():
        # Prepare initial state: |1111...⟩ (all spins up)
        for i in range(num_qubits):
            qml.PauliX(i)
        
        # Apply time evolution using Trotterization
        current_time = 0.0
        for step in range(time_steps):
            if time_dependent_field:
                # Create time-dependent Hamiltonian with oscillating field
                h_t = field_amplitude * np.sin(field_frequency * current_time)
                time_dep_hamiltonian = create_xyz_heisenberg_hamiltonian(
                    num_qubits, jx, jy, jz, h_t
                )
                qml.ApproxTimeEvolution(time_dep_hamiltonian, time=dt, n=1)
            else:
                qml.ApproxTimeEvolution(hamiltonian, time=dt, n=1)
            current_time += dt
        
        return qml.state()
    
    return circuit


def run_xyz_heisenberg_benchmark(
    num_qubits: int,
    jx: float = 1.0,
    jy: float = 1.0,
    jz: float = 1.0,
    external_field: float = 0.0,
    time_steps: int = 10,
    dt: float = 0.1,
    time_dependent_field: bool = False,
    field_amplitude: float = 0.0,
    field_frequency: float = 1.0,
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
    initial_state = np.zeros(2**num_qubits, dtype=complex)
    initial_state[-1] = 1.0  # |1111...⟩ is the last basis state
    
    # Calculate initial energy
    initial_energy = calculate_energy(initial_state, hamiltonian, num_qubits)
    
    # Build and execute circuit
    circuit = build_time_evolution_circuit(
        num_qubits, hamiltonian, time_steps, dt, jx, jy, jz,
        time_dependent_field, field_amplitude, field_frequency
    )
    
    # Measure memory before
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Measure execution time
    start = time.perf_counter()
    final_state = circuit()
    runtime_ms = (time.perf_counter() - start) * 1e3
    
    # Measure memory after
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_usage_mb = max(0.0, mem_after - mem_before)
    
    # Calculate final energy
    # For time-dependent case, use the Hamiltonian at final time
    if time_dependent_field:
        final_time = time_steps * dt
        h_final = field_amplitude * np.sin(field_frequency * final_time)
        final_hamiltonian = create_xyz_heisenberg_hamiltonian(
            num_qubits, jx, jy, jz, h_final
        )
        final_energy = calculate_energy(final_state, final_hamiltonian, num_qubits)
    else:
        final_energy = calculate_energy(final_state, hamiltonian, num_qubits)
    energy_change = final_energy - initial_energy
    
    # Count operations (approximate: each time step has Trotter steps)
    # For nearest-neighbor interactions: 3*(n-1) terms per time step
    num_interactions = 3 * (num_qubits - 1) if num_qubits > 1 else 0
    num_field_terms = num_qubits if abs(external_field) > 1e-10 else 0
    num_operations = time_steps * (num_interactions + num_field_terms)
    
    return {
        "framework": "PennyLane (Python)",
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
        "memory_usage_mb": round(memory_usage_mb, 2),
        "time_dependent_field": time_dependent_field,
        "field_amplitude": round(field_amplitude, 6) if time_dependent_field else 0.0,
        "field_frequency": round(field_frequency, 6) if time_dependent_field else 0.0,
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
    
    # Time-dependent field parameters (for non-conserved energy case)
    time_dependent = os.environ.get("XYZ_TIME_DEPENDENT", "false").lower() == "true"
    field_amplitude = float(os.environ.get("XYZ_FIELD_AMPLITUDE", "2.0"))
    field_frequency = float(os.environ.get("XYZ_FIELD_FREQUENCY", "1.0"))
    
    # Run benchmark
    result = run_xyz_heisenberg_benchmark(
        num_qubits=num_qubits,
        jx=jx,
        jy=jy,
        jz=jz,
        external_field=external_field,
        time_steps=time_steps,
        dt=dt,
        time_dependent_field=time_dependent,
        field_amplitude=field_amplitude,
        field_frequency=field_frequency,
    )
    
    # Write to JSON file
    output_file = os.environ.get("XYZ_OUTPUT_FILE", "pennylane_xyz_heisenberg.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()

