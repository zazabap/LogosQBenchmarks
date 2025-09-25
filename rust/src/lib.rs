use num_complex::Complex64;
use nalgebra::{DMatrix, DVector};
use rayon::prelude::*;
use std::f64::consts::PI;

/// Quantum state representation
pub struct QuantumState {
    pub amplitudes: DVector<Complex64>,
    pub num_qubits: usize,
}

impl QuantumState {
    /// Create a new quantum state in |0...0⟩
    pub fn new(num_qubits: usize) -> Self {
        let size = 1 << num_qubits;
        let mut amplitudes = DVector::zeros(size);
        amplitudes[0] = Complex64::new(1.0, 0.0);
        
        QuantumState {
            amplitudes,
            num_qubits,
        }
    }
    
    /// Apply a single-qubit gate
    pub fn apply_single_gate(&mut self, gate: &DMatrix<Complex64>, qubit: usize) {
        let size = self.amplitudes.len();
        let mut new_amplitudes = self.amplitudes.clone();
        
        for i in 0..size {
            if (i >> qubit) & 1 == 0 {
                let j = i | (1 << qubit);
                if j < size {
                    let amp0 = self.amplitudes[i];
                    let amp1 = self.amplitudes[j];
                    
                    new_amplitudes[i] = gate[(0, 0)] * amp0 + gate[(0, 1)] * amp1;
                    new_amplitudes[j] = gate[(1, 0)] * amp0 + gate[(1, 1)] * amp1;
                }
            }
        }
        
        self.amplitudes = new_amplitudes;
    }
    
    /// Apply a controlled gate
    pub fn apply_controlled_gate(&mut self, gate: &DMatrix<Complex64>, control: usize, target: usize) {
        let size = self.amplitudes.len();
        let mut new_amplitudes = self.amplitudes.clone();
        
        for i in 0..size {
            if (i >> control) & 1 == 1 {
                if (i >> target) & 1 == 0 {
                    let j = i | (1 << target);
                    if j < size {
                        let amp0 = self.amplitudes[i];
                        let amp1 = self.amplitudes[j];
                        
                        new_amplitudes[i] = gate[(0, 0)] * amp0 + gate[(0, 1)] * amp1;
                        new_amplitudes[j] = gate[(1, 0)] * amp0 + gate[(1, 1)] * amp1;
                    }
                }
            }
        }
        
        self.amplitudes = new_amplitudes;
    }
    
    /// Get probability of measuring a specific state
    pub fn get_probability(&self, state: usize) -> f64 {
        if state < self.amplitudes.len() {
            self.amplitudes[state].norm_sqr()
        } else {
            0.0
        }
    }
}

/// Common quantum gates
pub struct Gates;

impl Gates {
    pub fn pauli_x() -> DMatrix<Complex64> {
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(0.0, 0.0), Complex64::new(1.0, 0.0),
            Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
        ])
    }
    
    pub fn pauli_y() -> DMatrix<Complex64> {
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(0.0, 0.0), Complex64::new(0.0, -1.0),
            Complex64::new(0.0, 1.0), Complex64::new(0.0, 0.0),
        ])
    }
    
    pub fn pauli_z() -> DMatrix<Complex64> {
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
            Complex64::new(0.0, 0.0), Complex64::new(-1.0, 0.0),
        ])
    }
    
    pub fn hadamard() -> DMatrix<Complex64> {
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(inv_sqrt2, 0.0), Complex64::new(inv_sqrt2, 0.0),
            Complex64::new(inv_sqrt2, 0.0), Complex64::new(-inv_sqrt2, 0.0),
        ])
    }
    
    pub fn rx(theta: f64) -> DMatrix<Complex64> {
        let cos_half = (theta / 2.0).cos();
        let sin_half = (theta / 2.0).sin();
        
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(cos_half, 0.0), Complex64::new(0.0, -sin_half),
            Complex64::new(0.0, -sin_half), Complex64::new(cos_half, 0.0),
        ])
    }
    
    pub fn ry(theta: f64) -> DMatrix<Complex64> {
        let cos_half = (theta / 2.0).cos();
        let sin_half = (theta / 2.0).sin();
        
        DMatrix::from_row_slice(2, 2, &[
            Complex64::new(cos_half, 0.0), Complex64::new(-sin_half, 0.0),
            Complex64::new(sin_half, 0.0), Complex64::new(cos_half, 0.0),
        ])
    }
    
    pub fn rz(theta: f64) -> DMatrix<Complex64> {
        let exp_neg = Complex64::new(0.0, -theta / 2.0).exp();
        let exp_pos = Complex64::new(0.0, theta / 2.0).exp();
        
        DMatrix::from_row_slice(2, 2, &[
            exp_neg, Complex64::new(0.0, 0.0),
            Complex64::new(0.0, 0.0), exp_pos,
        ])
    }
}

/// Quantum circuit builder
pub struct QuantumCircuit {
    pub num_qubits: usize,
    pub operations: Vec<Operation>,
}

#[derive(Clone)]
pub enum Operation {
    SingleGate {
        gate: DMatrix<Complex64>,
        qubit: usize,
    },
    ControlledGate {
        gate: DMatrix<Complex64>,
        control: usize,
        target: usize,
    },
}

impl QuantumCircuit {
    pub fn new(num_qubits: usize) -> Self {
        QuantumCircuit {
            num_qubits,
            operations: Vec::new(),
        }
    }
    
    pub fn h(&mut self, qubit: usize) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::hadamard(),
            qubit,
        });
        self
    }
    
    pub fn x(&mut self, qubit: usize) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::pauli_x(),
            qubit,
        });
        self
    }
    
    pub fn y(&mut self, qubit: usize) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::pauli_y(),
            qubit,
        });
        self
    }
    
    pub fn z(&mut self, qubit: usize) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::pauli_z(),
            qubit,
        });
        self
    }
    
    pub fn rx(&mut self, qubit: usize, theta: f64) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::rx(theta),
            qubit,
        });
        self
    }
    
    pub fn ry(&mut self, qubit: usize, theta: f64) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::ry(theta),
            qubit,
        });
        self
    }
    
    pub fn rz(&mut self, qubit: usize, theta: f64) -> &mut Self {
        self.operations.push(Operation::SingleGate {
            gate: Gates::rz(theta),
            qubit,
        });
        self
    }
    
    pub fn cnot(&mut self, control: usize, target: usize) -> &mut Self {
        self.operations.push(Operation::ControlledGate {
            gate: Gates::pauli_x(),
            control,
            target,
        });
        self
    }
    
    pub fn execute(&self) -> QuantumState {
        let mut state = QuantumState::new(self.num_qubits);
        
        for op in &self.operations {
            match op {
                Operation::SingleGate { gate, qubit } => {
                    state.apply_single_gate(gate, *qubit);
                }
                Operation::ControlledGate { gate, control, target } => {
                    state.apply_controlled_gate(gate, *control, *target);
                }
            }
        }
        
        state
    }
}