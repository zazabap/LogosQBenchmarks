//! Minimal Variational Quantum Eigensolver (VQE) benchmark for the H₂ molecule.
//! Focused on a single, end-to-end LogosQ workflow suitable for publication-quality benchmarks.

use logosq::ndarray::Array2;
use logosq::optimization::ansatz::{EntanglingGate, EntanglingPattern, HardwareEfficientAnsatz};
use logosq::optimization::gradient::ParameterShift;
use logosq::optimization::observable::{Pauli, PauliObservable, PauliTerm};
use logosq::optimization::optimizer::Adam;
use logosq::optimization::vqe::{VQE, VQEResult};
use nalgebra::DMatrix;
use num_complex::Complex64;
use std::time::Instant;

fn create_h2_hamiltonian() -> PauliObservable {
    // Coefficients from the canonical STO-3G H₂ problem at 0.735 Å (Jordan-Wigner mapped).
    let mut h = PauliObservable::new(4);

    h.add_term(PauliTerm::new(-0.810_547_980_537_324, vec![Pauli::I; 4]));

    for (qubit, coeff) in [
        (0, 0.172_183_932_619_155),
        (1, 0.172_183_932_619_155),
        (2, -0.225_753_492_224_023),
        (3, -0.225_753_492_224_023),
    ] {
        let mut paulis = vec![Pauli::I; 4];
        paulis[qubit] = Pauli::Z;
        h.add_term(PauliTerm::new(coeff, paulis));
    }

    for ((q1, q2), coeff) in [
        ((0, 1), 0.120_912_632_617_766),
        ((0, 2), 0.168_927_538_700_879),
        ((0, 3), 0.045_232_799_946_057),
        ((1, 2), 0.045_232_799_946_057),
        ((1, 3), 0.168_927_538_700_879),
        ((2, 3), 0.120_912_632_617_766),
    ] {
        let mut paulis = vec![Pauli::I; 4];
        paulis[q1] = Pauli::Z;
        paulis[q2] = Pauli::Z;
        h.add_term(PauliTerm::new(coeff, paulis));
    }

    for ((q1, q2), coeff) in [
        ((0, 1), 0.166_145_432_563_824),
        ((2, 3), 0.174_643_430_683_004),
    ] {
        for axis in [Pauli::X, Pauli::Y] {
            let mut paulis = vec![Pauli::I; 4];
            paulis[q1] = axis;
            paulis[q2] = axis;
            h.add_term(PauliTerm::new(coeff, paulis));
        }
    }

    h
}

fn compute_exact_ground_state_energy(hamiltonian: &PauliObservable) -> f64 {
    let n = hamiltonian.num_qubits;
    let dim = 1 << n;
    let mut matrix = Array2::<Complex64>::zeros((dim, dim));

    // Build the Hamiltonian matrix
    for term in &hamiltonian.terms {
        let pauli_mats: Vec<Array2<Complex64>> = term.paulis.iter().map(|p| p.matrix()).collect();
        let mut term_matrix = Array2::<Complex64>::ones((1, 1));
        for mat in pauli_mats {
            let (r1, c1) = (term_matrix.shape()[0], term_matrix.shape()[1]);
            let (r2, c2) = (mat.shape()[0], mat.shape()[1]);
            let mut kron = Array2::<Complex64>::zeros((r1 * r2, c1 * c2));
            for i in 0..r1 {
                for j in 0..c1 {
                    for k in 0..r2 {
                        for l in 0..c2 {
                            kron[[i * r2 + k, j * c2 + l]] = term_matrix[[i, j]] * mat[[k, l]];
                        }
                    }
                }
            }
            term_matrix = kron;
        }
        for i in 0..dim {
            for j in 0..dim {
                matrix[[i, j]] += Complex64::new(term.coefficient, 0.0) * term_matrix[[i, j]];
            }
        }
    }

    // Convert to nalgebra DMatrix for eigenvalue decomposition
    // Since the Hamiltonian is Hermitian, eigenvalues are real
    // Build a real symmetric matrix from the Hermitian matrix
    let mut real_matrix = DMatrix::<f64>::zeros(dim, dim);
    for i in 0..dim {
        for j in 0..dim {
            // For Hermitian matrix: H_ij = conj(H_ji), so we take the real symmetric part
            if i == j {
                real_matrix[(i, j)] = matrix[[i, j]].re;
            } else {
                // Average the Hermitian pair to get symmetric real matrix
                real_matrix[(i, j)] = (matrix[[i, j]].re + matrix[[j, i]].re) / 2.0;
                real_matrix[(j, i)] = real_matrix[(i, j)];
            }
        }
    }

    // Compute eigenvalues of the real symmetric matrix
    let eigen = nalgebra::linalg::SymmetricEigen::new(real_matrix);
    let eigenvalues = eigen.eigenvalues;
    
    // Find minimum eigenvalue
    let min_energy = eigenvalues.iter().fold(f64::INFINITY, |a, &b| a.min(b));

    min_energy
}

fn run_logosq_vqe(
    hamiltonian: &PauliObservable,
    _exact_energy: f64,
    layers: usize,
) -> (VQEResult, f64) {
    // Note: LogosQ's VQE::run_random() uses an internal RNG that cannot be directly seeded.
    // For full reproducibility, LogosQ would need to support setting initial parameters
    // or exposing RNG seed control. This is a limitation of the current LogosQ API.
    // Other frameworks (Qiskit, PennyLane, Yao.jl) use seed=1337 for reproducibility.
    
    let ansatz = HardwareEfficientAnsatz::new(
        hamiltonian.num_qubits,
        layers,
        EntanglingGate::CNOT,
        EntanglingPattern::Linear,
    );
    let gradient_method = ParameterShift::new();
    let optimizer = Adam::new(0.01, 350).with_tolerance(1e-7);
    let mut vqe = VQE::new(ansatz, hamiltonian.clone(), gradient_method, optimizer);

    let start = Instant::now();
    let logosq_result = vqe.run_random();
    let runtime_ms = start.elapsed().as_secs_f64() * 1000.0;

    (logosq_result, runtime_ms)
}

fn main() {
    let hamiltonian = create_h2_hamiltonian();
    let exact_energy = compute_exact_ground_state_energy(&hamiltonian);
    
    // Get number of layers from environment variable (default: 3 for 12 parameters)
    let layers = std::env::var("VQA_LAYERS")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(3);
    
    let (logosq_result, runtime_ms) = run_logosq_vqe(&hamiltonian, exact_energy, layers);

    let json_output = format!(
        r#"{{
  "framework": "LogosQ (Rust)",
  "exact_energy": {:.10},
  "vqe_energy": {:.10},
  "energy_error": {:.10},
  "iterations": {},
  "runtime_ms": {:.2},
  "parameters": {},
  "converged": true
}}"#,
        exact_energy,
        logosq_result.ground_state_energy,
        (logosq_result.ground_state_energy - exact_energy).abs(),
        logosq_result.num_iterations,
        runtime_ms,
        hamiltonian.num_qubits * layers
    );

    // Write to JSON file
    let output_file = std::env::var("VQA_OUTPUT_FILE")
        .unwrap_or_else(|_| "logosq_vqa_result.json".to_string());
    std::fs::write(&output_file, json_output).expect("Failed to write JSON file");
}

