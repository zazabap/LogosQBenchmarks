use logosq::QuantumCircuit;
use serde::{Deserialize, Serialize};
use std::time::Instant;
use std::f64::consts::PI;
use rand::Rng;

#[derive(Serialize, Deserialize)]
struct BenchmarkResult {
    name: String,
    num_qubits: usize,
    num_gates: usize,
    execution_time_ms: f64,
    memory_usage_mb: f64,
    circuit_depth: usize,
}

#[derive(Serialize, Deserialize)]
struct BenchmarkSuite {
    library: String,
    version: String,
    results: Vec<BenchmarkResult>,
    total_time_ms: f64,
}

fn get_memory_usage() -> f64 {
    // Simple memory estimation - in a real implementation you'd use more sophisticated monitoring
    std::process::Command::new("ps")
        .args(&["-o", "rss=", "-p", &std::process::id().to_string()])
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

fn benchmark_ghz_state(num_qubits: usize) -> BenchmarkResult {
    let start_memory = get_memory_usage();
    let start_time = Instant::now();
    
    // Create GHZ state: |000...0⟩ + |111...1⟩
    let mut circuit = QuantumCircuit::new(num_qubits);
    
    // Apply Hadamard to first qubit
    circuit.h(0);
    
    // Apply CNOT gates to create entanglement
    for i in 1..num_qubits {
        circuit.cnot(0, i);
    }
    
    let _final_state = circuit.execute();
    
    let execution_time = start_time.elapsed();
    let end_memory = get_memory_usage();
    
    BenchmarkResult {
        name: format!("GHZ-{}", num_qubits),
        num_qubits,
        num_gates: num_qubits, // 1 H + (n-1) CNOT
        execution_time_ms: execution_time.as_secs_f64() * 1000.0,
        memory_usage_mb: end_memory - start_memory,
        circuit_depth: 2, // H gate depth + CNOT depth
    }
}

fn benchmark_random_circuit(num_qubits: usize, num_gates: usize) -> BenchmarkResult {
    let start_memory = get_memory_usage();
    let start_time = Instant::now();
    
    let mut circuit = QuantumCircuit::new(num_qubits);
    let mut rng = rand::thread_rng();
    
    for _ in 0..num_gates {
        let gate_type = rng.gen_range(0..6);
        let qubit = rng.gen_range(0..num_qubits);
        let angle = rng.gen::<f64>() * 2.0 * PI;
        
        match gate_type {
            0 => { circuit.h(qubit); }
            1 => { circuit.x(qubit); }
            2 => { circuit.y(qubit); }
            3 => { circuit.z(qubit); }
            4 => { circuit.rx(qubit, angle); }
            5 => { circuit.ry(qubit, angle); }
            _ => { circuit.rz(qubit, angle); }
        }
    }
    
    // Add some CNOT gates for entanglement
    let num_cnots = num_gates / 4;
    for _ in 0..num_cnots {
        let control = rng.gen_range(0..num_qubits);
        let mut target = rng.gen_range(0..num_qubits);
        while target == control {
            target = rng.gen_range(0..num_qubits);
        }
        circuit.cnot(control, target);
    }
    
    let _final_state = circuit.execute();
    
    let execution_time = start_time.elapsed();
    let end_memory = get_memory_usage();
    
    BenchmarkResult {
        name: format!("Random-{}-{}", num_qubits, num_gates),
        num_qubits,
        num_gates: num_gates + num_cnots,
        execution_time_ms: execution_time.as_secs_f64() * 1000.0,
        memory_usage_mb: end_memory - start_memory,
        circuit_depth: num_gates + num_cnots, // Simplified depth calculation
    }
}

fn benchmark_qft_circuit(num_qubits: usize) -> BenchmarkResult {
    let start_memory = get_memory_usage();
    let start_time = Instant::now();
    
    let mut circuit = QuantumCircuit::new(num_qubits);
    
    // Implement simplified QFT
    for i in 0..num_qubits {
        circuit.h(i);
        for j in (i + 1)..num_qubits {
            let angle = PI / (1 << (j - i)) as f64;
            circuit.rz(j, angle);
            circuit.cnot(j, i);
            circuit.rz(j, -angle);
            circuit.cnot(j, i);
        }
    }
    
    let _final_state = circuit.execute();
    
    let execution_time = start_time.elapsed();
    let end_memory = get_memory_usage();
    
    let num_gates = num_qubits + (num_qubits * (num_qubits - 1)) * 2; // H gates + controlled rotations
    
    BenchmarkResult {
        name: format!("QFT-{}", num_qubits),
        num_qubits,
        num_gates,
        execution_time_ms: execution_time.as_secs_f64() * 1000.0,
        memory_usage_mb: end_memory - start_memory,
        circuit_depth: num_qubits * 2,
    }
}

fn main() {
    let suite_start = Instant::now();
    let mut results = Vec::new();
    
    eprintln!("Starting LogosQ Rust benchmarks...");
    
    // Test different qubit sizes
    let qubit_sizes = vec![4, 6, 8, 10, 12];
    
    for &num_qubits in &qubit_sizes {
        if num_qubits <= 14 { // Limit for exponential memory growth
            eprintln!("Benchmarking {} qubits...", num_qubits);
            
            // GHZ state benchmark
            results.push(benchmark_ghz_state(num_qubits));
            
            // Random circuit benchmark
            let gate_count = num_qubits * 10;
            results.push(benchmark_random_circuit(num_qubits, gate_count));
            
            // QFT benchmark (only for smaller systems due to complexity)
            if num_qubits <= 10 {
                results.push(benchmark_qft_circuit(num_qubits));
            }
        }
    }
    
    let total_time = suite_start.elapsed();
    
    let benchmark_suite = BenchmarkSuite {
        library: "LogosQ".to_string(),
        version: "0.1.0".to_string(),
        results,
        total_time_ms: total_time.as_secs_f64() * 1000.0,
    };
    
    let json_output = serde_json::to_string_pretty(&benchmark_suite)
        .expect("Failed to serialize benchmark results");
    
    println!("{}", json_output);
    eprintln!("LogosQ benchmarks completed in {:.2}ms", total_time.as_secs_f64() * 1000.0);
}