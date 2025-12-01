"""
Visualize the Quantum Fourier Transform circuit diagram using PennyLane's matplotlib drawing.
"""

import matplotlib.pyplot as plt
import pennylane as qml
from math import pi
from pennylane_qft import qft_crz, qft_inverse_crz

def visualize_qft_circuit(n_qubits: int = 4, save_path: str = None):
    """
    Visualize the QFT circuit for a given number of qubits.
    
    Args:
        n_qubits: Number of qubits in the circuit
        save_path: Path to save the circuit diagram (optional)
    """
    print(f"Generating QFT circuit diagram for {n_qubits} qubits...")
    
    # Create device
    dev = qml.device("default.qubit", wires=n_qubits)
    
    # Define QFT circuit
    @qml.qnode(dev)
    def qft_circuit():
        # Prepare a simple input state (first qubit in |1⟩)
        qml.PauliX(wires=0)
        
        # Apply QFT
        qft_crz(range(n_qubits))
        
        # Return probabilities for measurement
        return qml.probs(wires=range(n_qubits))
    
    # Execute once to build the circuit
    _ = qft_circuit()
    
    # Draw the circuit using matplotlib
    fig, ax = qml.draw_mpl(qft_circuit, decimals=2, style='black_white')()
    
    # Set title
    ax.set_title(f'Quantum Fourier Transform Circuit ({n_qubits} qubits)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Adjust layout (bbox_inches='tight' handles layout automatically)
    
    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Circuit diagram saved to: {save_path}")
    else:
        plt.show()
    
    plt.close(fig)

def visualize_qft_vs_inverse(n_qubits: int = 3):
    """
    Visualize both QFT and QFT + Inverse QFT circuits side by side.
    
    Args:
        n_qubits: Number of qubits in the circuit
    """
    print(f"Generating QFT vs QFT+Inverse comparison for {n_qubits} qubits...")
    
    dev = qml.device("default.qubit", wires=n_qubits)
    
    # QFT only circuit
    @qml.qnode(dev)
    def qft_only():
        qml.PauliX(wires=0)
        qft_crz(range(n_qubits))
        return qml.probs(wires=range(n_qubits))
    
    # QFT + Inverse QFT circuit
    @qml.qnode(dev)
    def qft_inverse():
        qml.PauliX(wires=0)
        qft_crz(range(n_qubits))
        qft_inverse_crz(range(n_qubits))
        return qml.probs(wires=range(n_qubits))
    
    # Execute to build circuits
    _ = qft_only()
    _ = qft_inverse()
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
    
    # Draw QFT only
    qml.draw_mpl(qft_only, decimals=2, style='black_white', ax=ax1)()
    ax1.set_title(f'QFT Circuit ({n_qubits} qubits)', 
                  fontsize=12, fontweight='bold', pad=15)
    
    # Draw QFT + Inverse
    qml.draw_mpl(qft_inverse, decimals=2, style='black_white', ax=ax2)()
    ax2.set_title(f'QFT + Inverse QFT Circuit ({n_qubits} qubits)', 
                  fontsize=12, fontweight='bold', pad=15)
    
    # bbox_inches='tight' handles layout automatically
    save_path = f"/app/pennylane/QuantumFourierTransform/qft_vs_inverse_{n_qubits}q.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Comparison diagram saved to: {save_path}")
    
    plt.close(fig)

def visualize_multiple_sizes():
    """Visualize QFT circuits for multiple qubit counts."""
    qubit_counts = [3, 4, 5]
    
    for n_qubits in qubit_counts:
        save_path = f"/app/pennylane/QuantumFourierTransform/qft_circuit_{n_qubits}q.png"
        visualize_qft_circuit(n_qubits=n_qubits, save_path=save_path)
    
    # Also create comparison for 3 qubits
    visualize_qft_vs_inverse(n_qubits=3)

if __name__ == "__main__":
    print("=" * 60)
    print("Quantum Fourier Transform Circuit Visualization")
    print("=" * 60)
    
    # Visualize circuits for different sizes
    visualize_multiple_sizes()
    
    print("\n" + "=" * 60)
    print("All circuit diagrams generated successfully!")
    print("=" * 60)

