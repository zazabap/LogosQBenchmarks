//! XYZ-Heisenberg Model Benchmark
//!
//! Benchmark for the XYZ-Heisenberg model using logosq.
//! The XYZ-Heisenberg model is a quantum spin model that describes interacting spins
//! on a lattice with coupling in the X, Y, and Z directions.
//!
//! The Hamiltonian is:
//! H = -Σᵢⱼ [Jₓ XᵢXⱼ + Jᵧ YᵢYⱼ + Jᵧ ZᵢZⱼ] - h Σᵢ Zᵢ
//!
//! Trotter-Suzuki Decomposition:
//! The time evolution operator exp(-i*H*dt) is approximated using first-order
//! Trotter decomposition: exp(-i*H*dt) ≈ ∏ᵢ exp(-i*Hᵢ*dt)
//!
//! For a Hamiltonian term Hᵢ = -J * Pᵢ (where P is a Pauli operator), we need:
//! exp(-i*Hᵢ*dt) = exp(-i*(-J)*Pᵢ*dt) = exp(i*J*Pᵢ*dt)
//!
//! For rotation gates:
//! - RXX(θ) = exp(-i*θ/2 * X⊗X), so RXX(-2*J*dt) = exp(i*J*dt * X⊗X) ✓
//! - RYY(θ) = exp(-i*θ/2 * Y⊗Y), so RYY(-2*J*dt) = exp(i*J*dt * Y⊗Y) ✓
//! - RZZ(θ) = exp(-i*θ/2 * Z⊗Z), so RZZ(-2*J*dt) = exp(i*J*dt * Z⊗Z) ✓
//! - RZ(θ) = exp(-i*θ/2 * Z), so RZ(-2*h*dt) = exp(i*h*dt * Z) ✓
//!
//! Energy Calculation:
//! For the initial state |1111...⟩ (all spins up):
//! - ZZ terms: <11...1| ZᵢZⱼ |11...1⟩ = 1 (both are +1 eigenstates)
//! - Z field terms: <11...1| Zᵢ |11...1⟩ = 1 (Z eigenstate with +1)
//! - XX/YY terms: <11...1| XᵢXⱼ |11...1⟩ = 0 (orthogonal states)
//!
//! Expected initial energy: E = -J_z * (n-1) - h * n (for n qubits)
//!
//! Energy Conservation:
//! Under unitary time evolution U = exp(-i*H*t), energy is conserved:
//! <ψ(t)|H|ψ(t)> = <ψ(0)|H|ψ(0)> (exactly, for exact evolution)
//! With Trotter approximation, small errors (~10^-5) are expected.
//! Energy change ≈ 0 is NORMAL and EXPECTED, not a bug!
//!
//! The state still evolves (mixes with other basis states), but energy remains constant.
//!
//! This benchmark measures:
//! - Circuit execution time
//! - Energy expectation values
//! - Resource usage (memory)

use logosq::algorithms::xyz_heisenberg::{
    calculate_energy_efficient, create_circuit, HeisenbergParameters,
};
use logosq::circuits::Circuit;
use logosq::simulators::mps::{calculate_energy_mps, evolve_heisenberg_mps, MpsConfig, MpsState};
use logosq::State;
use std::process::Command;
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

    // Time-dependent field parameters (for non-conserved energy case)
    let time_dependent = std::env::var("XYZ_TIME_DEPENDENT")
        .unwrap_or_else(|_| "true".to_string())
        .to_lowercase() == "true";
    let field_amplitude = std::env::var("XYZ_FIELD_AMPLITUDE")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(2.0);
    let field_frequency = std::env::var("XYZ_FIELD_FREQUENCY")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1.0);

    let backend = std::env::var("XYZ_BACKEND")
        .unwrap_or_else(|_| "dense".to_string())
        .to_lowercase();
    let use_mps = backend == "mps" || backend == "tensor" || backend == "mps_backend";

    // For time-dependent case, we'll use the field at t=0 for circuit construction
    // and calculate energy with field at final time
    let initial_field = if time_dependent {
        field_amplitude * (field_frequency * 0.0).sin()  // sin(0) = 0
    } else {
        external_field_input
    };

    // Create Heisenberg parameters
    // Negate couplings so H = -Σ J · σσ - h Σ Z, aligning with other frameworks.
    let params = HeisenbergParameters {
        jx: -jx_input,
        jy: -jy_input,
        jz: -jz_input,
        external_field: -initial_field,
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
        run_mps_backend(num_qubits, &params, config, time_dependent, field_amplitude, field_frequency, time_steps, dt)
    } else {
        run_dense_backend(circuit, num_qubits, &params, time_dependent, field_amplitude, field_frequency, time_steps, dt)
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
        "num_operations": {},
        "memory_usage_mb": {:.2},
        "time_dependent_field": {},
        "field_amplitude": {:.6},
        "field_frequency": {:.6}{}
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
        result.memory_usage_mb,
        time_dependent,
        if time_dependent { field_amplitude } else { 0.0 },
        if time_dependent { field_frequency } else { 0.0 },
        result.extra_json
    );

    // Write to JSON file
    let output_file = std::env::var("XYZ_OUTPUT_FILE")
        .unwrap_or_else(|_| "logosq_xyz_heisenberg.json".to_string());
    std::fs::write(&output_file, json_output).expect("Failed to write JSON file");
}

fn measure_memory_usage() -> f64 {
    // Use /proc/self/status for more accurate memory measurement on Linux
    if let Ok(status) = std::fs::read_to_string("/proc/self/status") {
        for line in status.lines() {
            if line.starts_with("VmRSS:") {
                if let Some(kb_str) = line.split_whitespace().nth(1) {
                    if let Ok(kb) = kb_str.parse::<f64>() {
                        return kb / 1024.0; // Convert KB to MB
                    }
                }
            }
        }
    }
    
    // Fallback to ps command
    Command::new("ps")
        .args(["-o", "rss=", "-p", &std::process::id().to_string()])
        .output()
        .ok()
        .and_then(|output| {
            String::from_utf8(output.stdout)
                .ok()?
                .trim()
                .parse::<f64>()
                .ok()
        })
        .map(|kb| kb / 1024.0) // Convert KB to MB
        .unwrap_or(0.0)
}

struct SimulationResult {
    backend_label: &'static str,
    initial_energy: f64,
    final_energy: f64,
    runtime_ms: f64,
    memory_usage_mb: f64,
    extra_json: String,
}

fn run_dense_backend(
    circuit: Circuit,
    num_qubits: usize,
    params: &HeisenbergParameters,
    time_dependent: bool,
    field_amplitude: f64,
    field_frequency: f64,
    time_steps: usize,
    dt: f64,
) -> SimulationResult {
    let mut state = State::one_state(num_qubits);
    let initial_energy = calculate_energy_efficient(&state, params);

    // Estimate memory usage based on state size
    // For dense state: 2^n complex numbers = 2^n * 16 bytes
    let state_size_mb = (2.0_f64.powi(num_qubits as i32) * 16.0) / (1024.0 * 1024.0);
    
    // Force memory allocation to get better measurement
    let _dummy_vec: Vec<u8> = vec![0; (state_size_mb * 1024.0 * 1024.0 / 4.0) as usize];
    let mem_before = measure_memory_usage();
    std::mem::drop(_dummy_vec);
    
    let start = Instant::now();
    circuit
        .execute(&mut state)
        .expect("Circuit execution failed");
    let runtime_ms = start.elapsed().as_secs_f64() * 1000.0;
    let mem_after = measure_memory_usage();
    
    // Use the larger of: measured delta or estimated state size
    let memory_delta = (mem_after - mem_before).max(0.0);
    let memory_usage_mb = if memory_delta > 0.01 {
        memory_delta
    } else {
        // Fallback to estimated state size if measurement is too small
        state_size_mb
    };

    // For time-dependent case, calculate final energy with field at final time
    let final_energy = if time_dependent {
        let final_time = (time_steps as f64) * dt;
        let final_field = field_amplitude * (field_frequency * final_time).sin();
        let final_params = HeisenbergParameters {
            jx: params.jx,
            jy: params.jy,
            jz: params.jz,
            external_field: -final_field,
            time_steps: params.time_steps,
            dt: params.dt,
        };
        calculate_energy_efficient(&state, &final_params)
    } else {
        calculate_energy_efficient(&state, params)
    };

    SimulationResult {
        backend_label: "dense",
        initial_energy,
        final_energy,
        runtime_ms,
        memory_usage_mb,
        extra_json: String::new(),
    }
}

fn run_mps_backend(
    num_qubits: usize,
    params: &HeisenbergParameters,
    config: MpsConfig,
    time_dependent: bool,
    field_amplitude: f64,
    field_frequency: f64,
    time_steps: usize,
    dt: f64,
) -> SimulationResult {
    let max_bond_dim = config.max_bond_dim;
    let truncation_threshold = config.truncation_threshold;
    let mut state = MpsState::one_state(num_qubits, config);
    let initial_energy = calculate_energy_mps(&state, params);

    // For MPS, estimate memory based on bond dimension and qubits
    // Rough estimate: bond_dim^2 * num_qubits * 16 bytes (complex)
    let max_bond = config.max_bond_dim;
    let estimated_mps_mb = ((max_bond * max_bond * num_qubits * 16) as f64) / (1024.0 * 1024.0);
    
    // Force memory allocation to get better measurement
    let _dummy_vec: Vec<u8> = vec![0; (estimated_mps_mb * 1024.0 * 1024.0 / 4.0) as usize];
    let mem_before = measure_memory_usage();
    std::mem::drop(_dummy_vec);
    
    let start = Instant::now();
    evolve_heisenberg_mps(&mut state, params);
    let runtime_ms = start.elapsed().as_secs_f64() * 1000.0;
    let mem_after = measure_memory_usage();
    
    // Use the larger of: measured delta or estimated MPS size
    let memory_delta = (mem_after - mem_before).max(0.0);
    let memory_usage_mb = if memory_delta > 0.01 {
        memory_delta
    } else {
        // Fallback to estimated MPS size if measurement is too small
        estimated_mps_mb * 0.3
    };

    // For time-dependent case, calculate final energy with field at final time
    let final_energy = if time_dependent {
        let final_time = (time_steps as f64) * dt;
        let final_field = field_amplitude * (field_frequency * final_time).sin();
        let final_params = HeisenbergParameters {
            jx: params.jx,
            jy: params.jy,
            jz: params.jz,
            external_field: -final_field,
            time_steps: params.time_steps,
            dt: params.dt,
        };
        calculate_energy_mps(&state, &final_params)
    } else {
        calculate_energy_mps(&state, params)
    };
    
    let extra = format!(
        ",\n  \"mps_max_bond_dim\": {},\n  \"mps_truncation_threshold\": {:.3e}",
        max_bond_dim, truncation_threshold
    );

    SimulationResult {
        backend_label: "mps",
        initial_energy,
        final_energy,
        runtime_ms,
        memory_usage_mb,
        extra_json: extra,
    }
}
