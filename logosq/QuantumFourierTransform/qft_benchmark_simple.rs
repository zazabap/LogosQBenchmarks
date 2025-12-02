use logosq::algorithms::qft;
use logosq::circuits::Circuit;
use logosq::simulators::mps::{MpsConfig, MpsState};
use logosq::State;
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;
use std::fs::File;
use std::io::Write;
use std::process::Command;
use std::time::Instant;

#[derive(Debug, Serialize, Deserialize)]
struct BenchmarkResult {
    n_qubits: usize,
    execution_time_ms: f64,
    std_deviation_ms: f64,
    memory_mb: f64,
    gate_count: usize,
    state_size: usize,
    fidelity: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    qft_probs: Option<Vec<f64>>, // QFT output probabilities for verification
}

#[derive(Clone, Copy, PartialEq)]
enum QftBackend {
    Dense,
    Mps,
}

impl QftBackend {
    fn from_str(value: &str) -> Self {
        match value {
            "mps" | "tensor" | "mps_backend" => QftBackend::Mps,
            _ => QftBackend::Dense,
        }
    }

    fn label(&self) -> &'static str {
        match self {
            QftBackend::Dense => "dense",
            QftBackend::Mps => "mps",
        }
    }
}

struct QFTBenchmark {
    backend: QftBackend,
    mps_config: MpsConfig,
    results: Vec<BenchmarkResult>,
    auto_switch_threshold: usize, // Auto-switch to MPS above this qubit count
}

impl QFTBenchmark {
    fn new(backend: QftBackend, mps_config: MpsConfig) -> Self {
        Self {
            backend,
            mps_config,
            results: Vec::new(),
            auto_switch_threshold: 10, // Auto-switch to MPS for qubits > 10
        }
    }
    
    /// Get the effective backend for a given qubit count
    /// Automatically switches to MPS for larger qubit counts if using dense backend
    fn get_backend_for_qubits(&self, n_qubits: usize) -> QftBackend {
        match self.backend {
            QftBackend::Dense if n_qubits > self.auto_switch_threshold => {
                QftBackend::Mps
            }
            _ => self.backend,
        }
    }

    fn get_system_info() -> String {
        let cpu_count = match Command::new("nproc").output() {
            Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_string(),
            Err(_) => "Unknown".to_string(),
        };

        let memory = match Command::new("grep")
            .args(["MemTotal", "/proc/meminfo"])
            .output()
        {
            Ok(output) => {
                let meminfo = String::from_utf8_lossy(&output.stdout);
                if let Some(mem_kb) = meminfo.split_whitespace().nth(1) {
                    let mem_mb = mem_kb.parse::<f64>().unwrap_or(0.0) / 1024.0;
                    format!("{:.0} MB", mem_mb)
                } else {
                    "Unknown".to_string()
                }
            }
            Err(_) => "Unknown".to_string(),
        };

        format!(
            "CPUs: {}, Memory: {}, OS: Ubuntu 22.04.5 LTS",
            cpu_count, memory
        )
    }

    fn measure_memory_usage() -> f64 {
        let output = Command::new("ps")
            .args(["--no-headers", "-o", "rss", "-p"])
            .arg(std::process::id().to_string())
            .output()
            .expect("Failed to execute ps command");

        let mem_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let mem_kb = mem_str.parse::<f64>().unwrap_or(0.0);

        mem_kb / 1024.0 // Convert KB to MB
    }

    fn benchmark_qft_circuit(&self, n_qubits: usize, num_trials: usize) -> BenchmarkResult {
        // Determine effective backend (may auto-switch to MPS for large qubit counts)
        let effective_backend = self.get_backend_for_qubits(n_qubits);
        let backend_label = if effective_backend != self.backend {
            format!("{} (auto-switched from {})", effective_backend.label(), self.backend.label())
        } else {
            effective_backend.label().to_string()
        };
        
        println!(
            "\n🔬 Benchmarking {}-qubit QFT circuit on {} backend...",
            n_qubits,
            backend_label
        );

        // Theoretical gate count for QFT
        let gate_count = n_qubits + (n_qubits * (n_qubits - 1)) / 2 + n_qubits / 2;

        // Memory before - force a clean baseline by measuring after potential allocations
        let mem_before = Self::measure_memory_usage();

        // Prepare for measurements
        let mut execution_times = Vec::with_capacity(num_trials);
        let mut fidelity = None;
        let mut peak_memory = mem_before;

        // Initial warm-up run
        println!("  ⚡ Warm-up run...");
        match effective_backend {
            QftBackend::Dense => {
                let mut state = State::zero_state(n_qubits);
                let mut circuit = Circuit::new(n_qubits);
                circuit.x(0);
                circuit
                    .execute(&mut state)
                    .expect("Failed to execute warm-up circuit");
                qft::apply(&mut state);
            }
            QftBackend::Mps => {
                let mut state = MpsState::zero_state(n_qubits, self.mps_config);
                state.apply_pauli_x(0);
                apply_qft_mps(&mut state);
            }
        }

        // Run benchmark trials
        println!("  🏃 Running {} trials...", num_trials);
        for i in 0..num_trials {
            let execution_time_ms = match effective_backend {
                QftBackend::Dense => {
                    let mut state = State::zero_state(n_qubits);
                    let mut circuit = Circuit::new(n_qubits);
                    circuit.x(0);
                    circuit
                        .execute(&mut state)
                        .expect("Failed to execute benchmark circuit");

                    let start = Instant::now();
                    qft::apply(&mut state);
                    start.elapsed().as_secs_f64() * 1000.0
                }
                QftBackend::Mps => {
                    let mut state = MpsState::zero_state(n_qubits, self.mps_config);
                    state.apply_pauli_x(0);

                    let start = Instant::now();
                    apply_qft_mps(&mut state);
                    start.elapsed().as_secs_f64() * 1000.0
                }
            };

            execution_times.push(execution_time_ms);
            
            // Track peak memory during trials
            let current_mem = Self::measure_memory_usage();
            if current_mem > peak_memory {
                peak_memory = current_mem;
            }
            
            print!(
                "  Trial {:2}/{}: {:7.3} ms\r",
                i + 1,
                num_trials,
                execution_time_ms
            );
        }
        println!();

        // Test round-trip fidelity if appropriate
        if n_qubits <= 15 {
            println!("  🔄 Testing round-trip fidelity...");
            match effective_backend {
                QftBackend::Dense => {
                    let mut state = State::zero_state(n_qubits);
                    let mut circuit = Circuit::new(n_qubits);
                    circuit.x(0);
                    circuit
                        .execute(&mut state)
                        .expect("Failed to execute fidelity circuit");

                    qft::apply(&mut state);
                    qft::apply_inverse(&mut state);

                    fidelity = Some(state.probability(1)); // |1⟩ = |00...01⟩
                }
                QftBackend::Mps => {
                    let mut state = MpsState::zero_state(n_qubits, self.mps_config);
                    state.apply_pauli_x(0);
                    apply_qft_mps(&mut state);
                    apply_inverse_qft_mps(&mut state);

                    let dense_state = state.to_dense_state();
                    fidelity = Some(dense_state.probability(1));
                }
            }
        }

        // Calculate statistics
        let mean_time = execution_times.iter().sum::<f64>() / num_trials as f64;
        let variance = execution_times
            .iter()
            .map(|x| (*x - mean_time).powi(2))
            .sum::<f64>()
            / num_trials as f64;
        let std_dev = variance.sqrt();

        // Memory after - check both final and peak memory
        let mem_after = Self::measure_memory_usage();
        
        // Use peak memory during execution, or final memory if higher
        let final_peak = if mem_after > peak_memory { mem_after } else { peak_memory };
        let mut mem_delta = final_peak - mem_before;
        
        // Clamp negative values to 0 (memory can be freed by allocator/GC between measurements)
        if mem_delta < 0.0 {
            mem_delta = 0.0;
        }

        // Print summary for this qubit count
        println!("  ✅ Results:");
        println!(
            "    ⏱️  Execution time: {:.3} ± {:.3} ms",
            mean_time, std_dev
        );
        println!("    💾 Memory usage:   {:.2} MB", mem_delta);
        println!("    🔧 Gate count:     {}", gate_count);
        println!("    🌌 State size:     {}", 1 << n_qubits);

        if let Some(f) = fidelity {
            println!("    🎯 Fidelity:      {:.6}", f);
        }

        // Save QFT probabilities for verification (only for small qubit counts to avoid large arrays)
        let qft_probs = if n_qubits <= 8 {
            // Run QFT once more to get probabilities
            match effective_backend {
                QftBackend::Dense => {
                    let mut state = State::zero_state(n_qubits);
                    let mut circuit = Circuit::new(n_qubits);
                    circuit.x(0);
                    circuit
                        .execute(&mut state)
                        .expect("Failed to execute circuit");
                    qft::apply(&mut state);
                    Some((0..(1 << n_qubits))
                        .map(|i| state.probability(i))
                        .collect())
                }
                QftBackend::Mps => {
                    let mut state = MpsState::zero_state(n_qubits, self.mps_config);
                    state.apply_pauli_x(0);
                    apply_qft_mps(&mut state);
                    let dense_state = state.to_dense_state();
                    Some((0..(1 << n_qubits))
                        .map(|i| dense_state.probability(i))
                        .collect())
                }
            }
        } else {
            None
        };

        BenchmarkResult {
            n_qubits,
            execution_time_ms: mean_time,
            std_deviation_ms: std_dev,
            memory_mb: mem_delta,
            gate_count,
            state_size: 1 << n_qubits,
            fidelity,
            qft_probs,
        }
    }

    fn run_benchmark(&mut self, min_qubits: usize, max_qubits: usize, num_trials: usize) {
        println!("\n🚀 LOGOSQ QFT BENCHMARK");
        println!("{}", "=".repeat(60));

        println!("💻 System Info: {}", Self::get_system_info());
        println!("🎯 Testing qubits: {} to {}", min_qubits, max_qubits);
        println!("🔄 Trials per test: {}", num_trials);
        println!("{}", "=".repeat(60));

        for n_qubits in min_qubits..=max_qubits {
            match std::panic::catch_unwind(|| self.benchmark_qft_circuit(n_qubits, num_trials)) {
                Ok(result) => {
                    self.results.push(result);
                }
                Err(_) => {
                    println!(
                        "❌ Error benchmarking {} qubits - benchmark failed",
                        n_qubits
                    );
                    println!(
                        "  (This may be due to memory limitations or other system constraints)"
                    );
                    break;
                }
            }
        }

        // Save JSON results
        if !self.results.is_empty() {
            let output_file = "/app/logosq/QuantumFourierTransform/qft_benchmark_results.json";
            match File::create(output_file) {
                Ok(mut file) => {
                    let json = serde_json::to_string_pretty(&self.results).unwrap();
                    if let Err(e) = file.write_all(json.as_bytes()) {
                        println!("❌ Error writing benchmark results: {}", e);
                    } else {
                        println!("\n💾 Results saved to: {}", output_file);
                    }
                }
                Err(e) => {
                    println!("\n❌ Error creating benchmark file: {}", e);
                }
            }
        }

        self.print_scaling_analysis();
    }

    fn print_scaling_analysis(&self) {
        println!("\n📈 PERFORMANCE SCALING ANALYSIS");
        println!("{}", "=".repeat(60));

        if self.results.len() < 2 {
            println!("⚠️  Not enough data for scaling analysis");
            return;
        }

        // Print results table
        println!(
            "{:<6} | {:<14} | {:<10} | {:<12} | {:<10}",
            "Qubits", "Time (ms)", "Gates", "Memory (MB)", "State Size"
        );
        println!("{}", "-".repeat(60));

        for result in &self.results {
            println!(
                "{:<6} | {:<14.3} | {:<10} | {:<12.2} | {:<10}",
                result.n_qubits,
                format!(
                    "{:.3} ± {:.3}",
                    result.execution_time_ms, result.std_deviation_ms
                ),
                result.gate_count,
                result.memory_mb,
                result.state_size
            );
        }

        // Calculate scaling factors
        if self.results.len() >= 2 {
            let first = &self.results[0];
            let last = &self.results[self.results.len() - 1];

            let qubit_factor = last.n_qubits as f64 / first.n_qubits as f64;
            let time_factor = last.execution_time_ms / first.execution_time_ms;
            let gate_factor = last.gate_count as f64 / first.gate_count as f64;
            let memory_factor = last.memory_mb / first.memory_mb;

            println!(
                "\n📊 Scaling from {} to {} qubits:",
                first.n_qubits, last.n_qubits
            );
            println!("• 🎯 Qubit factor:      {:.1}x", qubit_factor);
            println!("• ⏱️  Time factor:       {:.1}x", time_factor);
            println!("• 🔧 Gate factor:       {:.1}x", gate_factor);
            println!("• 💾 Memory factor:     {:.1}x", memory_factor);
            println!("• 📐 Theoretical O(n²): {:.1}x", qubit_factor.powi(2));
        }
    }
}

fn apply_qft_mps(state: &mut MpsState) {
    let num_qubits = state.num_qubits();
    for i in 0..num_qubits {
        state.apply_hadamard(i);
        for j in (i + 1)..num_qubits {
            let angle = PI / (1 << (j - i)) as f64;
            state.apply_controlled_phase(i, j, angle);
        }
    }

    for i in 0..num_qubits / 2 {
        swap_qubits(state, i, num_qubits - 1 - i);
    }
}

fn apply_inverse_qft_mps(state: &mut MpsState) {
    let num_qubits = state.num_qubits();

    for i in 0..num_qubits / 2 {
        swap_qubits(state, i, num_qubits - 1 - i);
    }

    for i in (0..num_qubits).rev() {
        for j in (i + 1)..num_qubits {
            let angle = -PI / (1 << (j - i)) as f64;
            state.apply_controlled_phase(i, j, angle);
        }
        state.apply_hadamard(i);
    }
}

fn swap_qubits(state: &mut MpsState, left: usize, right: usize) {
    if left == right {
        return;
    }

    let (left_idx, mut right_idx) = if left < right {
        (left, right)
    } else {
        (right, left)
    };
    assert!(
        right_idx < state.num_qubits(),
        "Swap indices must be within range"
    );

    // Bring the right qubit next to the left qubit using nearest-neighbor swaps.
    let mut swaps = Vec::new();
    while right_idx > left_idx + 1 {
        let swap_site = right_idx - 1;
        state.apply_swap_gate(swap_site);
        swaps.push(swap_site);
        right_idx -= 1;
    }

    // Swap the now-adjacent qubits.
    state.apply_swap_gate(left_idx);

    // Undo the temporary swaps in reverse order to restore intermediate qubits.
    for site in swaps.into_iter().rev() {
        state.apply_swap_gate(site);
    }
}

fn install_dependencies_if_needed() {
    // Minimal dependency checks
    let serde_check = Command::new("cargo")
        .args(["tree", "--package", "serde"])
        .output();

    if serde_check.is_err() || !serde_check.unwrap().status.success() {
        println!("📦 Installing serde and serde_json...");
        let _ = Command::new("cargo")
            .args(["add", "serde", "serde_json", "--features", "serde/derive"])
            .output();
    }
}

fn main() {
    // Check dependencies
    install_dependencies_if_needed();

    let backend_value = std::env::var("QFT_BACKEND")
        .unwrap_or_else(|_| "dense".to_string())
        .to_lowercase();
    let backend = QftBackend::from_str(&backend_value);

    let max_bond_dim = std::env::var("MPS_MAX_BOND")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(64);
    let trunc_thresh = std::env::var("MPS_TRUNC_EPS")
        .ok()
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1e-8);
    let mps_config = MpsConfig {
        max_bond_dim,
        truncation_threshold: trunc_thresh,
    };

    let mut benchmark = QFTBenchmark::new(backend, mps_config);

    // Get qubit range from environment variables or use defaults
    let min_qubits = std::env::var("QFT_START_QUBITS")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(1);
    let max_qubits = std::env::var("QFT_END_QUBITS")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(12);
    let step = std::env::var("QFT_STEP")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(1);
    let trials = 5;

    println!(
        "🎯 Running QFT benchmark: {} to {} qubits (step: {}), {} trials each",
        min_qubits, max_qubits, step, trials
    );
    println!("🧮 Backend: {}", backend.label());

    // Run benchmark with step support
    println!("\n🚀 LOGOSQ QFT BENCHMARK");
    println!("{}", "=".repeat(60));
    println!("💻 System Info: {}", QFTBenchmark::get_system_info());
    println!("🎯 Testing qubits: {} to {} (step: {})", min_qubits, max_qubits, step);
    println!("🔄 Trials per test: {}", trials);
    println!("{}", "=".repeat(60));

    let mut n = min_qubits;
    while n <= max_qubits {
        match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| benchmark.benchmark_qft_circuit(n, trials))) {
            Ok(result) => {
                benchmark.results.push(result);
            }
            Err(_) => {
                eprintln!(
                    "❌ Error benchmarking {} qubits - benchmark failed",
                    n
                );
                eprintln!(
                    "  (This may be due to memory limitations or other system constraints)"
                );
                // Continue to next qubit count instead of breaking
            }
        }
        n += step;
    }
    
    // Save JSON results
    if !benchmark.results.is_empty() {
        let output_file = "/app/logosq/QuantumFourierTransform/qft_benchmark_results.json";
        match File::create(output_file) {
            Ok(mut file) => {
                let json = serde_json::to_string_pretty(&benchmark.results).unwrap();
                if let Err(e) = file.write_all(json.as_bytes()) {
                    println!("❌ Error writing benchmark results: {}", e);
                } else {
                    println!("\n💾 Results saved to: {}", output_file);
                }
            }
            Err(e) => {
                println!("\n❌ Error creating benchmark file: {}", e);
            }
        }
    }
    
    benchmark.print_scaling_analysis();

    println!("\n🎉 Benchmark completed!");
}
