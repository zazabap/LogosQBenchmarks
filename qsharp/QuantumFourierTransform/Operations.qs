namespace QuantumFourierTransform {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    
    operation RunQFT(numQubits : Int) : Unit {
        use qubits = Qubit[numQubits];
        
        // Apply QFT
        ApplyQFT(qubits);
        
        // Measure (just to complete the circuit, though mostly we care about runtime of QFT itself)
        // For benchmarking, we often just run the circuit.
        // To ensure the compiler doesn't optimize it away, we might measure.
        // But for pure runtime, we can just Reset.
        ResetAll(qubits);
    }
    
    operation ApplyQFT(qubits : Qubit[]) : Unit {
        let n = Length(qubits);
        for i in 0..n-1 {
            H(qubits[i]);
            for j in i+1..n-1 {
                let k = j - i + 1;
                let angle = 2.0 * PI() / IntAsDouble(1 <<< k);
                Controlled R1([qubits[j]], (angle, qubits[i]));
            }
        }
        // Swap qubits to match standard QFT definition
        for i in 0..n/2-1 {
            SWAP(qubits[i], qubits[n-1-i]);
        }
    }
}

