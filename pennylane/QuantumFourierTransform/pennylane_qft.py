import pennylane as qml
import numpy as np
from math import pi

def qft(wires):
    """
    Quantum Fourier Transform implementation with PennyLane.
    
    Args:
        wires (list): List of qubit indices where QFT is applied
    """
    n = len(wires)
    
    # Apply H gates and controlled phase rotations
    for i in range(n):
        qml.Hadamard(wires=wires[i])
        
        # Apply controlled phase rotations
        for j in range(i+1, n):
            # Use ctrl decorator with PhaseShift instead of ControlledPhaseShift
            qml.ctrl(qml.PhaseShift(pi/2**(j-i), wires=wires[i]), control=wires[j])
    
    # Apply SWAP gates to reverse the order
    for i in range(n//2):
        qml.SWAP(wires=[wires[i], wires[n-i-1]])

def qft_inverse(wires):
    """
    Inverse Quantum Fourier Transform implementation.
    
    Args:
        wires (list): List of qubit indices where inverse QFT is applied
    """
    n = len(wires)
    
    # Apply SWAP gates to reverse the order
    for i in range(n//2):
        qml.SWAP(wires=[wires[i], wires[n-i-1]])
    
    # Apply gates in reverse order with conjugated phases
    for i in range(n-1, -1, -1):
        for j in range(n-1, i, -1):
            # Use ctrl decorator with negative phase
            qml.ctrl(qml.PhaseShift(-pi/2**(j-i), wires=wires[i]), control=wires[j])
        
        qml.Hadamard(wires=wires[i])

# Alternative implementation using CRZ gates (more common approach)
def qft_crz(wires):
    """
    QFT implementation using controlled-RZ gates (alternative approach).
    
    Args:
        wires (list): List of qubit indices where QFT is applied
    """
    n = len(wires)
    
    for i in range(n):
        qml.Hadamard(wires=wires[i])
        
        # Apply controlled rotations
        for j in range(i+1, n):
            qml.CRZ(pi/2**(j-i), wires=[wires[j], wires[i]])
    
    # Apply SWAP gates to reverse the order
    for i in range(n//2):
        qml.SWAP(wires=[wires[i], wires[n-i-1]])

def qft_inverse_crz(wires):
    """
    Inverse QFT implementation using controlled-RZ gates.
    
    Args:
        wires (list): List of qubit indices where inverse QFT is applied
    """
    n = len(wires)
    
    # Apply SWAP gates to reverse the order
    for i in range(n//2):
        qml.SWAP(wires=[wires[i], wires[n-i-1]])
    
    # Apply gates in reverse order with conjugated phases
    for i in range(n-1, -1, -1):
        for j in range(n-1, i, -1):
            qml.CRZ(-pi/2**(j-i), wires=[wires[j], wires[i]])
        
        qml.Hadamard(wires=wires[i])

# Create a device and quantum circuit
def run_qft_example():
    """Run a QFT example and display results for 1 to 10 qubits"""
    
    print("QFT Results for Different Qubit Counts:")
    print("=" * 60)
    
    # Test QFT for 1 to 10 qubits
    for n_qubits in range(1, 11):
        print(f"\n--- {n_qubits} Qubit{'s' if n_qubits > 1 else ''} ---")
        
        # Create a simulator device
        dev = qml.device("default.qubit", wires=n_qubits)
        
        # Define a quantum circuit with QFT using CRZ gates
        @qml.qnode(dev)
        def circuit(input_state):
            # Prepare input state
            for i, bit in enumerate(input_state):
                if bit == '1':
                    qml.PauliX(wires=i)
            
            # Apply QFT using CRZ implementation (more stable)
            qft_crz(range(n_qubits))
            
            # Return probabilities
            return qml.probs(wires=range(n_qubits))
        
        # Generate a few test states for this qubit count
        # For larger systems, we'll test fewer states to keep output manageable
        if n_qubits <= 3:
            # Test all possible states for small systems
            test_states = [format(i, f"0{n_qubits}b") for i in range(2**n_qubits)]
        elif n_qubits <= 6:
            # Test a subset of states for medium systems
            test_indices = [0, 1, 2**(n_qubits-1), 2**n_qubits-1]  # |000...⟩, |000...1⟩, |100...⟩, |111...⟩
            test_states = [format(i, f"0{n_qubits}b") for i in test_indices]
        else:
            # Test just a few representative states for large systems
            test_indices = [0, 1, 2**n_qubits-1]  # |000...⟩, |000...1⟩, |111...⟩
            test_states = [format(i, f"0{n_qubits}b") for i in test_indices]
        
        for state in test_states:
            probs = circuit(state)
            print(f"Input: |{state}⟩")
            
            # For larger systems, only show the most significant probabilities
            threshold = 0.01 if n_qubits <= 5 else 0.05
            significant_probs = [(i, p) for i, p in enumerate(probs) if p > threshold]
            
            if significant_probs:
                for i, p in significant_probs[:5]:  # Limit to top 5 probabilities
                    binary = format(i, f"0{n_qubits}b")
                    print(f"  |{binary}⟩: {p:.4f}")
            else:
                # Show the highest probability state even if below threshold
                max_idx = np.argmax(probs)
                binary = format(max_idx, f"0{n_qubits}b")
                print(f"  |{binary}⟩: {probs[max_idx]:.4f} (highest)")
            print()
        
        # Test QFT followed by inverse QFT for verification
        @qml.qnode(dev)
        def qft_inverse_demo(input_state):
            # Prepare input state
            for i, bit in enumerate(input_state):
                if bit == '1':
                    qml.PauliX(wires=i)
            
            # Apply QFT
            qft_crz(range(n_qubits))
            
            # Apply inverse QFT
            qft_inverse_crz(range(n_qubits))
            
            # Return probabilities
            return qml.probs(wires=range(n_qubits))
        
        # Test with a simple state for verification
        test_state = "1" + "0" * (n_qubits - 1)  # |100...⟩
        probs = qft_inverse_demo(test_state)
        
        # Check if we get back the original state (should have probability ≈ 1)
        original_idx = int(test_state, 2)
        recovery_prob = probs[original_idx]
        
        print(f"QFT→IQFT verification for |{test_state}⟩:")
        print(f"  Recovery probability: {recovery_prob:.6f}")
        if recovery_prob > 0.99:
            print("  ✓ Verification passed")
        else:
            print("  ✗ Verification failed")
        print("-" * 40)

def visualize_circuit():
    """Visualize the QFT circuit structure for different qubit counts"""
    
    print("\nQFT Circuit Visualizations:")
    print("=" * 60)
    
    # Show QFT circuits for 1-5 qubits (more than 5 becomes unwieldy to display)
    for n_qubits in range(1, 6):
        print(f"\n--- {n_qubits} Qubit QFT Circuit ---")
        
        # Create a simulator device
        dev = qml.device("default.qubit", wires=n_qubits)
        
        @qml.qnode(dev)
        def qft_circuit():
            # Prepare a simple input state (first qubit in |1⟩)
            qml.PauliX(wires=0)
            
            # Apply QFT
            qft_crz(range(n_qubits))
            
            return qml.probs(wires=range(n_qubits))
        
        # Execute to build the circuit
        qft_circuit()
        
        # Print the circuit diagram
        print(qml.draw(qft_circuit)())
        
        # Show gate count information
        tape = qft_circuit._tape
        gate_counts = {}
        for op in tape.operations:
            gate_name = op.name
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
        
        print(f"\nGate count summary:")
        for gate, count in sorted(gate_counts.items()):
            print(f"  {gate}: {count}")
        
        total_gates = sum(gate_counts.values())
        print(f"  Total gates: {total_gates}")
        
        # Show circuit depth calculation
        circuit_depth = len(qft_circuit._tape.operations)
        theoretical_depth = n_qubits + (n_qubits // 2)  # H gates + SWAP gates (simplified)
        print(f"  Circuit depth: {circuit_depth}")
        print(f"  Theoretical minimum depth: {theoretical_depth}")
        print("-" * 50)
    
    # Show a comparison of QFT vs IQFT for 3 qubits
    print(f"\n--- QFT vs Inverse QFT Comparison (3 qubits) ---")
    
    dev_3q = qml.device("default.qubit", wires=3)
    
    @qml.qnode(dev_3q)
    def qft_only():
        qml.PauliX(wires=0)  # |001⟩ input
        qft_crz(range(3))
        return qml.probs(wires=range(3))
    
    @qml.qnode(dev_3q)
    def qft_then_iqft():
        qml.PauliX(wires=0)  # |001⟩ input
        qft_crz(range(3))
        qft_inverse_crz(range(3))
        return qml.probs(wires=range(3))
    
    print("QFT only:")
    qft_only()
    print(qml.draw(qft_only)())
    
    print("\nQFT + Inverse QFT:")
    qft_then_iqft()
    print(qml.draw(qft_then_iqft)())

if __name__ == "__main__":
    # Check if PennyLane is installed
    try:
        run_qft_example()
        visualize_circuit()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install PennyLane with: pip install pennylane")