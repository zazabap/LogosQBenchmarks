use logosq::algorithms::qft;
use logosq::circuits::Circuit;
use logosq::vis::Visualizable;
use logosq::State;

fn main() {
    let num_qubits = 5; // Example with 5 qubits
    let results = quantum_fourier_transform_example(num_qubits);
    println!("Measurement results after QFT: {:?}", results);
}
// how to combine algorithms
pub fn quantum_fourier_transform_example(num_qubits: usize) -> Vec<usize> {

    let mut state = State::zero_state(num_qubits);
    // Create a circuit that demonstrates QFT
    let mut circuit = Circuit::new(num_qubits);
    circuit.x(0);
    circuit.execute(&mut state);

    // Apply QFT
    qft::apply(&mut state);
    println!("State after QFT: {}\n", state.visualize());
    qft::apply_inverse(&mut state);
    println!("State after inverse QFT: {}\n", state.visualize());
    circuit.execute_and_measure()
}