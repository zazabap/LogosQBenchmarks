"""
Visualize the VQA ansatz circuit for H2 VQE using PennyLane's draw_mpl.
"""

import matplotlib.pyplot as plt
import pennylane as qml
from pennylane import numpy as np

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

def draw_circuit():
    """Draws the VQA circuit using matplotlib."""
    num_qubits = 4
    reps = 3
    dev = qml.device("default.qubit", wires=num_qubits)
    ansatz = build_ansatz(reps=reps)

    @qml.qnode(dev)
    def circuit(params):
        ansatz(params)
        return qml.expval(qml.PauliZ(0)) # Dummy measurement for drawing

    # Generate dummy parameters for visualization
    # Shape: (reps, num_qubits)
    params = np.random.uniform(0, 2 * np.pi, size=(reps, num_qubits))

    # Draw the circuit using mpl
    print(f"Generating circuit diagram with {reps} layers...")
    fig, ax = qml.draw_mpl(circuit)(params)
    
    output_file = "pennylane_vqa_circuit.png"
    plt.savefig(output_file)
    print(f"Circuit diagram saved to {output_file}")

if __name__ == "__main__":
    draw_circuit()

