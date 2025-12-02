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
    """
    # Hamiltonian matches the benchmark setup
    hamiltonian = create_xyz_heisenberg_hamiltonian(
        num_qubits=num_qubits,
        jx=jx,
        jy=jy,
        jz=jz,
        external_field=external_field,
    )

    dev = qml.device("default.qubit", wires=num_qubits)

    @qml.qnode(dev)
    def circuit():
        # Prepare initial state: |111...1⟩ (all spins up), same as in `xyz_h.py`
        for i in range(num_qubits):
            qml.PauliX(i)

        # Apply time evolution using first-order Trotterization, as in `xyz_h.py`
        for _ in range(time_steps):
            qml.ApproxTimeEvolution(hamiltonian, time=dt, n=1)

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
    # Use device expansion so ApproxTimeEvolution is decomposed into
    # elementary gates (CNOT/Rot/etc.) for a clearer circuit diagram.
    fig, ax = qml.draw_mpl(
        circuit,
        style="black_white",
        decimals=2,
        expansion_strategy="device",
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


