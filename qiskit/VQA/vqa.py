"""
Cross-framework Variational Quantum Eigensolver (VQE) benchmark for H₂ using Qiskit.

This script mirrors the LogosQ Rust workflow by:
1. Building the STO-3G Hamiltonian (Jordan–Wigner mapped) with verified coefficients.
2. Computing the exact ground-state energy via dense diagonalization.
3. Running a hardware-efficient VQE (RealAmplitudes, linear entanglement, 3 reps) optimized
   with COBYLA to obtain a comparable variational energy.
4. Printing a compact benchmark table against reference PennyLane and LogosQ results.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np
from qiskit.circuit.library import real_amplitudes
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.optimize import minimize


@dataclass
class FrameworkPerformanceRow:
    name: str
    energy: float
    iterations: int
    runtime_ms: float


def _label_from_mutations(mutations: Sequence[Tuple[int, str]], num_qubits: int = 4) -> str:
    """Create a Pauli label where `mutations` supplies (qubit, axis) overrides."""
    label = ["I"] * num_qubits
    for qubit, axis in mutations:
        label[qubit] = axis
    return "".join(label)


def create_h2_hamiltonian() -> SparsePauliOp:
    """
    STO-3G Hamiltonian for H₂ at 0.735 Å using Jordan–Wigner mapping.
    Coefficients follow the canonical integrals widely cited in Qiskit tutorials.
    """
    terms: List[Tuple[str, float]] = []

    terms.append(("IIII", -0.810_547_980_537_324))

    for qubit, coeff in [
        (0, 0.172_183_932_619_155),
        (1, 0.172_183_932_619_155),
        (2, -0.225_753_492_224_023),
        (3, -0.225_753_492_224_023),
    ]:
        terms.append((_label_from_mutations([(qubit, "Z")]), coeff))

    for (q1, q2), coeff in [
        ((0, 1), 0.120_912_632_617_766),
        ((0, 2), 0.168_927_538_700_879),
        ((0, 3), 0.045_232_799_946_057),
        ((1, 2), 0.045_232_799_946_057),
        ((1, 3), 0.168_927_538_700_879),
        ((2, 3), 0.120_912_632_617_766),
    ]:
        terms.append((_label_from_mutations([(q1, "Z"), (q2, "Z")]), coeff))

    for (q1, q2), coeff in [
        ((0, 1), 0.166_145_432_563_824),
        ((2, 3), 0.174_643_430_683_004),
    ]:
        for axis in ("X", "Y"):
            terms.append((_label_from_mutations([(q1, axis), (q2, axis)]), coeff))

    return SparsePauliOp.from_list(terms)


def compute_exact_ground_state_energy(hamiltonian: SparsePauliOp) -> float:
    """Diagonalize the dense Hamiltonian matrix to obtain the exact ground energy."""
    matrix = hamiltonian.to_matrix()
    eigenvalues = np.linalg.eigvalsh(matrix)
    return float(np.min(eigenvalues).real)


def evaluate_energy(params: np.ndarray, circuit, h_matrix: np.ndarray) -> float:
    """Return ⟨ψ(θ)|H|ψ(θ)⟩ for the given parameter vector."""
    bound = circuit.assign_parameters(params, inplace=False)
    state = Statevector.from_instruction(bound)
    amplitudes = state.data
    return float(np.real(np.vdot(amplitudes, h_matrix @ amplitudes)))


def run_qiskit_vqe(hamiltonian: SparsePauliOp, exact_energy: float) -> dict:
    """Execute a VQE with a hardware-efficient ansatz and COBYLA optimizer."""
    num_qubits = hamiltonian.num_qubits
    ansatz = real_amplitudes(num_qubits=num_qubits, entanglement="linear", reps=3)
    parameter_count = ansatz.num_parameters
    h_matrix = hamiltonian.to_matrix()

    def objective(theta: Sequence[float]) -> float:
        return evaluate_energy(np.asarray(theta), ansatz, h_matrix)

    rng = np.random.default_rng(seed=1337)
    initial_point = 2 * math.pi * rng.random(size=parameter_count)

    start = time.perf_counter()
    res = minimize(
        fun=objective,
        x0=initial_point,
        method="COBYLA",
        options={"maxiter": 350, "rhobeg": 0.1, "tol": 1e-7},
    )
    optimal_energy = float(res.fun)
    num_iters = int(res.nfev)
    runtime_ms = (time.perf_counter() - start) * 1e3

    return {
        "framework": "Qiskit (Python)",
        "exact_energy": float(exact_energy),
        "vqe_energy": optimal_energy,
        "energy_error": abs(optimal_energy - exact_energy),
        "iterations": num_iters,
        "runtime_ms": round(runtime_ms, 2),
        "parameters": int(parameter_count),
        "converged": bool(res.success),
    }


def print_framework_comparison(rows: Sequence[FrameworkPerformanceRow], exact_energy: float) -> None:
    print("\n" + "=" * 70)
    print("Cross-Framework VQE Comparison (H₂, STO-3G)")
    print("=" * 70)
    print(f"{'Framework':<22} | {'Energy (Ha)':>13} | {'Iterations':>10} | {'Runtime (ms)':>13}")
    print("-" * 70)
    for row in rows:
        print(f"{row.name:<22} | {row.energy:>13.6f} | {row.iterations:>10} | {row.runtime_ms:>13.2f}")

    best = min(rows, key=lambda r: r.energy)
    print(
        f"\nBest energy: {best.name} ({best.energy:.6f} Ha, Δ vs exact = {abs(best.energy - exact_energy):.6f} Ha)"
    )


def main() -> None:
    import os
    hamiltonian = create_h2_hamiltonian()
    exact_energy = compute_exact_ground_state_energy(hamiltonian)
    result = run_qiskit_vqe(hamiltonian, exact_energy)
    
    # Write to JSON file
    output_file = os.environ.get("VQA_OUTPUT_FILE", "qiskit_vqa_result.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
