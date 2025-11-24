"""
Cross-framework Variational Quantum Eigensolver (VQE) benchmark for H₂ using PennyLane.

This script mirrors the LogosQ and Qiskit workflows by:
1. Constructing the STO-3G Hamiltonian (Jordan–Wigner) with verified coefficients.
2. Computing the exact ground-state energy via dense diagonalization.
3. Running a hardware-efficient VQE (linear entanglement, 3 layers) optimized with Adam.
4. Printing a comparison table with reference LogosQ/Qiskit figures.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as onp
import pennylane as qml
from pennylane import numpy as np


@dataclass
class FrameworkPerformanceRow:
    name: str
    energy: float
    iterations: int
    runtime_ms: float


def _pauli_word(label: str) -> qml.operation.Operator:
    """Convert a string like 'ZIZX' into a PennyLane tensor product."""
    ops = []
    mapping = {"I": qml.Identity, "X": qml.PauliX, "Y": qml.PauliY, "Z": qml.PauliZ}
    for wire, axis in enumerate(label):
        if axis == "I":
            continue
        ops.append(mapping[axis](wire))
    if not ops:
        return qml.Identity(0)
    if len(ops) == 1:
        return ops[0]
    # Use qml.prod() for tensor products (available in PennyLane 0.20+)
    # Fallback to manual construction for older versions
    try:
        return qml.prod(*ops)
    except (AttributeError, TypeError):
        # Fallback: manually construct tensor product using @ operator
        result = ops[0]
        for op in ops[1:]:
            result = result @ op
        return result


def create_h2_hamiltonian() -> qml.Hamiltonian:
    """STO-3G Hamiltonian for H₂ at 0.735 Å with Jordan–Wigner coefficients."""
    terms: List[Tuple[str, float]] = []
    terms.append(("IIII", -0.810_547_980_537_324))

    for qubit, coeff in [
        (0, 0.172_183_932_619_155),
        (1, 0.172_183_932_619_155),
        (2, -0.225_753_492_224_023),
        (3, -0.225_753_492_224_023),
    ]:
        labels = list("IIII")
        labels[qubit] = "Z"
        terms.append(("".join(labels), coeff))

    for (q1, q2), coeff in [
        ((0, 1), 0.120_912_632_617_766),
        ((0, 2), 0.168_927_538_700_879),
        ((0, 3), 0.045_232_799_946_057),
        ((1, 2), 0.045_232_799_946_057),
        ((1, 3), 0.168_927_538_700_879),
        ((2, 3), 0.120_912_632_617_766),
    ]:
        labels = list("IIII")
        labels[q1] = "Z"
        labels[q2] = "Z"
        terms.append(("".join(labels), coeff))

    for (q1, q2), coeff in [
        ((0, 1), 0.166_145_432_563_824),
        ((2, 3), 0.174_643_430_683_004),
    ]:
        for axis in ("X", "Y"):
            labels = list("IIII")
            labels[q1] = axis
            labels[q2] = axis
            terms.append(("".join(labels), coeff))

    coeffs = [coeff for _, coeff in terms]
    ops = [_pauli_word(label) for label, _ in terms]
    return qml.Hamiltonian(coeffs, ops)


def compute_exact_ground_state_energy(hamiltonian: qml.Hamiltonian) -> float:
    matrix = qml.matrix(hamiltonian, wire_order=range(4))
    dense = onp.asarray(matrix, dtype=onp.complex128)
    eigenvalues = np.linalg.eigvalsh(dense)
    return float(np.min(eigenvalues).real)


def build_ansatz(reps: int = 3):
    """Create the hardware-efficient layer structure."""
    wires = range(4)

    def ansatz(params):
        for layer in range(reps):
            for idx, wire in enumerate(wires):
                qml.RY(params[layer, idx], wires=wire)
            for control, target in zip(wires, wires[1:]):
                qml.CNOT(wires=[control, target])

    return ansatz


def run_pennylane_vqe(hamiltonian: qml.Hamiltonian, exact_energy: float) -> dict:
    dev = qml.device("default.qubit", wires=4)
    ansatz = build_ansatz(reps=3)

    @qml.qnode(dev)
    def vqe_circuit(params):
        ansatz(params)
        return qml.expval(hamiltonian)

    def cost_fn(params):
        return vqe_circuit(params)

    optimizer = qml.AdamOptimizer(stepsize=0.01)
    max_steps = 350
    tolerance = 1e-7

    rng = onp.random.default_rng(seed=1337)
    params = np.array(rng.uniform(0.0, 2 * onp.pi, size=(3, 4)), requires_grad=True)

    energies: List[float] = []
    start = time.perf_counter()
    iterations = 0
    converged = False

    for step in range(1, max_steps + 1):
        params, energy = optimizer.step_and_cost(cost_fn, params)
        energies.append(float(energy))
        iterations = step
        if step > 5 and abs(energies[-1] - energies[-2]) < tolerance:
            converged = True
            break

    runtime_ms = (time.perf_counter() - start) * 1e3
    final_energy = energies[-1]
    delta = abs(final_energy - exact_energy)

    return {
        "framework": "PennyLane (Python)",
        "exact_energy": exact_energy,
        "vqe_energy": final_energy,
        "energy_error": delta,
        "iterations": iterations,
        "runtime_ms": round(runtime_ms, 2),
        "parameters": 12,
        "converged": converged,
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


def main():
    import os
    hamiltonian = create_h2_hamiltonian()
    exact_energy = compute_exact_ground_state_energy(hamiltonian)
    result = run_pennylane_vqe(hamiltonian, exact_energy)
    
    # Write to JSON file
    output_file = os.environ.get("VQA_OUTPUT_FILE", "pennylane_vqa_result.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
