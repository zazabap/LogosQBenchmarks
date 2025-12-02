"""
Visualize the XYZ-Heisenberg time-evolution circuit used in `xyz_h.py`
using PennyLane's matplotlib circuit drawer.
"""

import matplotlib.pyplot as plt
import pennylane as qml

from xyz_h import create_xyz_heisenberg_hamiltonian


def build_xyz_time_evolution_qnode(
    num_qubits: int,
    time_steps: int,
    dt: float,
    jx: float = 1.0,
    jy: float = 1.0,
    jz: float = 1.0,
    external_field: float = 0.0,
) -> qml.QNode:
    """Build the same time-evolution circuit as in `build_time_evolution_circuit`
    from `xyz_h.py`, but return a QNode suitable for visualization.
    
    Uses explicit Trotter-Suzuki decomposition: exp(-i*H*dt) ≈ ∏ᵢ exp(-i*Hᵢ*dt)
    Each term exp(-i*Hᵢ*dt) is implemented as a rotation gate.
    """
    dev = qml.device("default.qubit", wires=num_qubits)

    @qml.qnode(dev)
    def circuit():
        # Prepare initial state: |111...1⟩ (all spins up), same as in `xyz_h.py`
        for i in range(num_qubits):
            qml.PauliX(i)

        # Apply time evolution using explicit Trotter-Suzuki decomposition
        # For H = -Σᵢ [Jₓ XᵢXᵢ₊₁ + Jᵧ YᵢYᵢ₊₁ + Jᵧ ZᵢZᵢ₊₁] - h Σᵢ Zᵢ
        # exp(-i*H*dt) ≈ ∏ᵢ exp(-i*Hᵢ*dt)
        for step in range(time_steps):
            # Nearest-neighbor interactions (XX, YY, ZZ)
            for i in range(num_qubits - 1):
                # XX interaction: exp(-i*(-Jₓ*XᵢXᵢ₊₁)*dt) = exp(i*Jₓ*XᵢXᵢ₊₁*dt)
                # RXX(θ) = exp(-i*θ/2 * X⊗X), so RXX(-2*Jₓ*dt) = exp(i*Jₓ*dt * X⊗X)
                if abs(jx) > 1e-10:
                    qml.IsingXX(-2.0 * jx * dt, wires=[i, i + 1])
                
                # YY interaction: exp(-i*(-Jᵧ*YᵢYᵢ₊₁)*dt) = exp(i*Jᵧ*YᵢYᵢ₊₁*dt)
                # RYY(θ) = exp(-i*θ/2 * Y⊗Y), so RYY(-2*Jᵧ*dt) = exp(i*Jᵧ*dt * Y⊗Y)
                if abs(jy) > 1e-10:
                    qml.IsingYY(-2.0 * jy * dt, wires=[i, i + 1])
                
                # ZZ interaction: exp(-i*(-Jᵧ*ZᵢZᵢ₊₁)*dt) = exp(i*Jᵧ*ZᵢZᵢ₊₁*dt)
                # RZZ(θ) = exp(-i*θ/2 * Z⊗Z), so RZZ(-2*Jᵧ*dt) = exp(i*Jᵧ*dt * Z⊗Z)
                if abs(jz) > 1e-10:
                    qml.IsingZZ(-2.0 * jz * dt, wires=[i, i + 1])
            
            # External magnetic field (Z direction)
            # exp(-i*(-h*Zᵢ)*dt) = exp(i*h*Zᵢ*dt)
            # RZ(θ) = exp(-i*θ/2 * Z), so RZ(-2*h*dt) = exp(i*h*dt * Z)
            if abs(external_field) > 1e-10:
                for i in range(num_qubits):
                    qml.RZ(-2.0 * external_field * dt, wires=i)

        # Dummy measurement to make the circuit drawable
        return qml.probs(wires=range(num_qubits))

    return circuit


def visualize_xyz_circuit(
    num_qubits: int,
    time_steps: int,
    dt: float,
    jx: float = 1.0,
    jy: float = 1.0,
    jz: float = 1.0,
    external_field: float = 0.0,
    save_path: str | None = None,
) -> None:
    """Visualize the XYZ-Heisenberg circuit for given parameters."""
    print(
        f"Generating XYZ-Heisenberg circuit diagram: "
        f"{num_qubits} qubits, {time_steps} steps, dt={dt}"
    )

    circuit = build_xyz_time_evolution_qnode(
        num_qubits=num_qubits,
        time_steps=time_steps,
        dt=dt,
        jx=jx,
        jy=jy,
        jz=jz,
        external_field=external_field,
    )

    # Execute once to build the tape
    _ = circuit()

    # Draw with matplotlib
    # Since we're using explicit gates (IsingXX, IsingYY, IsingZZ, RZ),
    # no expansion strategy is needed - the gates are already decomposed.
    fig, ax = qml.draw_mpl(
        circuit,
        style="black_white",
        decimals=2,
    )()

    title = (
        f"XYZ-Heisenberg Time Evolution\n"
        f"{num_qubits} qubits, {time_steps} Trotter steps, dt={dt}"
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=20)

    # bbox_inches="tight" handles layout; no tight_layout() needed
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✓ Circuit diagram saved to: {save_path}")
    else:
        plt.show()

    plt.close(fig)


def visualize_standard_setups() -> None:
    """Generate circuit diagrams for a few standard benchmark-style setups.

    These mirror the kinds of circuits used in `xyz_h.py` and match the
    existing filenames in this directory.
    """
    # (qubits, steps, dt, output_name)
    configs = [
        (3, 3, 0.1, "xyz_heisenberg_circuit_3q_3steps.png"),
        (4, 4, 0.1, "xyz_heisenberg_circuit_4q_4steps.png"),
        (4, 5, 0.1, "xyz_heisenberg_circuit_4q_5steps.png"),
        (5, 5, 0.1, "xyz_heisenberg_circuit_5q_5steps.png"),
    ]

    for num_qubits, steps, dt, filename in configs:
        save_path = f"/app/pennylane/XYZHeisenberg/{filename}"
        visualize_xyz_circuit(
            num_qubits=num_qubits,
            time_steps=steps,
            dt=dt,
            jx=1.0,
            jy=1.0,
            jz=1.0,
            external_field=0.0,
            save_path=save_path,
        )


if __name__ == "__main__":
    print("=" * 70)
    print("XYZ-Heisenberg Circuit Visualization (PennyLane)")
    print("=" * 70)

    visualize_standard_setups()

    print("\n" + "=" * 70)
    print("All XYZ-Heisenberg circuit diagrams generated successfully!")
    print("=" * 70)


