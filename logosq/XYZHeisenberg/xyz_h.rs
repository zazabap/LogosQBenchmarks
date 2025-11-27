//! XYZ-Heisenberg Model Benchmark
//!
//! Benchmark for the XYZ-Heisenberg model using logosq.
//! The XYZ-Heisenberg model is a quantum spin model that describes interacting spins
//! on a lattice with coupling in the X, Y, and Z directions.
//!
//! The Hamiltonian is:
//! H = -Σᵢⱼ [Jₓ XᵢXⱼ + Jᵧ YᵢYⱼ + Jᵧ ZᵢZⱼ] - h Σᵢ Zᵢ
//!
//! This benchmark measures:
//! - Circuit execution time
//! - Energy expectation values
//! - Resource usage

use logosq::algorithms::xyz_heisenberg::{
    calculate_energy_efficient, create_circuit, HeisenbergParameters,
};
use logosq::circuits::Circuit;
use logosq::simulators::mps::{calculate_energy_mps, evolve_heisenberg_mps, MpsConfig, MpsState};
use logosq::State;
use std::time::Instant;

fn main() {
    // Parse configuration from environment variables
    let num_qubits = std::env::var("XYZ_QUBITS")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(8);

    let time_steps = std::env::var("XYZ_STEPS")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(10);

    let dt = std::env::var("XYZ_DT")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(0.1);

    let jx_input = std::env::var("XYZ_JX")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1.0);

    let jy_input = std::env::var("XYZ_JY")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1.0);

    let jz_input = std::env::var("XYZ_JZ")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1.0);

    let external_field_input = std::env::var("XYZ_FIELD")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(0.0);

    let backend = std::env::var("XYZ_BACKEND")
        .unwrap_or_else(|_| "dense".to_string())
        .to_lowercase();
    let use_mps = backend == "mps" || backend == "tensor" || backend == "mps_backend";

    // Create Heisenberg parameters
    // Negate couplings so H = -Σ J · σσ - h Σ Z, aligning with other frameworks.
    let params = HeisenbergParameters {
        jx: -jx_input,
        jy: -jy_input,
        jz: -jz_input,
        external_field: -external_field_input,
        time_steps,
        dt,
    };

    // Pre-build the circuit to report gate counts for dense runs
    let circuit = create_circuit(num_qubits, &params);
    let num_operations = circuit.num_operations();

    let result = if use_mps {
        let max_bond_dim = std::env::var("MPS_MAX_BOND")
            .ok()
            .and_then(|s| s.parse::<usize>().ok())
            .unwrap_or(128);
        let trunc_thresh = std::env::var("MPS_TRUNC_EPS")
            .ok()
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(1e-6);
        let config = MpsConfig {
            max_bond_dim,
            truncation_threshold: trunc_thresh,
        };
        run_mps_backend(num_qubits, &params, config)
    } else {
        run_dense_backend(circuit, num_qubits, &params)
    };

    let energy_change = result.final_energy - result.initial_energy;

    // Output JSON result
    let json_output = format!(
        r#"{{
  "framework": "LogosQ (Rust)",
  "backend": "{}",
  "qubits": {},
  "time_steps": {},
  "dt": {:.6},
  "jx": {:.6},
  "jy": {:.6},
  "jz": {:.6},
  "external_field": {:.6},
  "initial_energy": {:.10},
  "final_energy": {:.10},
  "energy_change": {:.10},
  "runtime_ms": {:.2},
  "num_operations": {}{}
}}"#,
        result.backend_label,
        num_qubits,
        time_steps,
        dt,
        jx_input,
        jy_input,
        jz_input,
        external_field_input,
        result.initial_energy,
        result.final_energy,
        energy_change,
        result.runtime_ms,
        num_operations,
        result.extra_json
    );

    // Write to JSON file
    let output_file = std::env::var("XYZ_OUTPUT_FILE")
        .unwrap_or_else(|_| "logosq_xyz_heisenberg.json".to_string());
    std::fs::write(&output_file, json_output).expect("Failed to write JSON file");
}

struct SimulationResult {
    backend_label: &'static str,
    initial_energy: f64,
    final_energy: f64,
    runtime_ms: f64,
    extra_json: String,
}

fn run_dense_backend(
    circuit: Circuit,
    num_qubits: usize,
    params: &HeisenbergParameters,
) -> SimulationResult {
    let mut state = State::one_state(num_qubits);
    let initial_energy = calculate_energy_efficient(&state, params);

    let start = Instant::now();
    circuit
        .execute(&mut state)
        .expect("Circuit execution failed");
    let runtime_ms = start.elapsed().as_secs_f64() * 1000.0;

    let final_energy = calculate_energy_efficient(&state, params);

    SimulationResult {
        backend_label: "dense",
        initial_energy,
        final_energy,
        runtime_ms,
        extra_json: String::new(),
    }
}

fn run_mps_backend(
    num_qubits: usize,
    params: &HeisenbergParameters,
    config: MpsConfig,
) -> SimulationResult {
    let max_bond_dim = config.max_bond_dim;
    let truncation_threshold = config.truncation_threshold;
    let mut state = MpsState::one_state(num_qubits, config);
    let initial_energy = calculate_energy_mps(&state, params);

    let start = Instant::now();
    evolve_heisenberg_mps(&mut state, params);
    let runtime_ms = start.elapsed().as_secs_f64() * 1000.0;

    let final_energy = calculate_energy_mps(&state, params);
    let extra = format!(
        ",\n  \"mps_max_bond_dim\": {},\n  \"mps_truncation_threshold\": {:.3e}",
        max_bond_dim, truncation_threshold
    );

    SimulationResult {
        backend_label: "mps",
        initial_energy,
        final_energy,
        runtime_ms,
        extra_json: extra,
    }
}
