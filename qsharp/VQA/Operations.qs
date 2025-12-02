namespace VQA {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Diagnostics;

    operation RunAnsatz(
        numQubits : Int,
        reps : Int,
        parameters : Double[]
    ) : Unit {
        use qubits = Qubit[numQubits];
        
        // Validate parameter count
        if (Length(parameters) != numQubits * reps) {
            fail "Incorrect number of parameters.";
        }
        
        for layer in 0..reps-1 {
            // Ry rotations
            for q in 0..numQubits-1 {
                let paramIdx = layer * numQubits + q;
                Ry(parameters[paramIdx], qubits[q]);
            }
            
            // Linear CNOT entanglement
            for q in 0..numQubits-2 {
                CNOT(qubits[q], qubits[q+1]);
            }
        }
        
        // Dump state for energy calculation
        DumpMachine("vqa_state_dump.txt");
        
        ResetAll(qubits);
    }
}

