namespace XYZHeisenberg {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Diagnostics;

    operation RunTimeEvolution(
        numQubits : Int,
        jx : Double,
        jy : Double,
        jz : Double,
        h : Double,
        timeSteps : Int,
        dt : Double
    ) : Unit {
        use qubits = Qubit[numQubits];
        
        // Initialize to |11...1>
        ApplyToEach(X, qubits);
        
        // Trotter evolution
        for step in 1..timeSteps {
            // Nearest neighbor interactions
            for i in 0..numQubits-2 {
                if (AbsD(jx) > 1e-9) {
                    Rxx(-2.0 * jx * dt, qubits[i], qubits[i+1]);
                }
                if (AbsD(jy) > 1e-9) {
                    Ryy(-2.0 * jy * dt, qubits[i], qubits[i+1]);
                }
                if (AbsD(jz) > 1e-9) {
                    Rzz(-2.0 * jz * dt, qubits[i], qubits[i+1]);
                }
            }
            
            // External field
            if (AbsD(h) > 1e-9) {
                for i in 0..numQubits-1 {
                    Rz(-2.0 * h * dt, qubits[i]);
                }
            }
        }
        
        // Dump the machine state to be read by the driver
        // Using a specific filename that the C# driver will look for
        DumpMachine("state_dump.txt");
        
        // Reset qubits before releasing
        ResetAll(qubits);
    }
}

