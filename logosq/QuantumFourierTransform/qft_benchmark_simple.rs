use logosq::algorithms::qft;
use logosq::circuits::Circuit;
use logosq::vis::Visualizable;
use logosq::State;
use std::collections::HashMap;
use std::fs::File;
use std::io::Write;
use std::time::{Duration, Instant};
use std::process::Command;
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
struct BenchmarkResult {
    n_qubits: usize,
    execution_time_ms: f64,
    std_deviation_ms: f64,
    memory_mb: f64,
    gate_count: usize,
    state_size: usize,
    fidelity: Option<f64>,
}

struct QFTBenchmark {
    results: Vec<BenchmarkResult>,
}

impl QFTBenchmark {
    fn new() -> Self {
        Self {
            results: Vec::new(),
        }
    }

    fn get_system_info() -> String {
        let cpu_count = match Command::new("nproc").output() {
            Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_string(),
            Err(_) => "Unknown".to_string()
        };

        let memory = match Command::new("grep").args(&["MemTotal", "/proc/meminfo"]).output() {
            Ok(output) => {
                let meminfo = String::from_utf8_lossy(&output.stdout);
                if let Some(mem_kb) = meminfo.split_whitespace().nth(1) {
                    let mem_mb = mem_kb.parse::<f64>().unwrap_or(0.0) / 1024.0;
                    format!("{:.0} MB", mem_mb)
                } else {
                    "Unknown".to_string()
                }
            },
            Err(_) => "Unknown".to_string()
        };

        format!("CPUs: {}, Memory: {}, OS: Ubuntu 22.04.5 LTS", cpu_count, memory)
    }

    fn measure_memory_usage() -> f64 {
        let output = Command::new("ps")
            .args(&["--no-headers", "-o", "rss", "-p", &format!("{}", std::process::id())])
            .output()
            .expect("Failed to execute ps command");
        
        let mem_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let mem_kb = mem_str.parse::<f64>().unwrap_or(0.0);
        
        mem_kb / 1024.0 // Convert KB to MB
    }

    fn benchmark_qft_circuit(&self, n_qubits: usize, num_trials: usize) -> BenchmarkResult {
        println!("\n🔬 Benchmarking {}-qubit QFT circuit...", n_qubits);
        
        // Theoretical gate count for QFT
        let gate_count = n_qubits + (n_qubits * (n_qubits - 1)) / 2 + n_qubits / 2;
        
        // Memory before
        let mem_before = Self::measure_memory_usage();
        
        // Prepare for measurements
        let mut execution_times = Vec::with_capacity(num_trials);
        let mut fidelity = None;
        
        // Initial warm-up run
        println!("  ⚡ Warm-up run...");
        let mut state = State::zero_state(n_qubits);
        let mut circuit = Circuit::new(n_qubits);
        circuit.x(0);
        circuit.execute(&mut state);
        qft::apply(&mut state);
        
        // Run benchmark trials
        println!("  🏃 Running {} trials...", num_trials);
        for i in 0..num_trials {
            // Reset state for this trial
            let mut state = State::zero_state(n_qubits);
            let mut circuit = Circuit::new(n_qubits);
            circuit.x(0);
            circuit.execute(&mut state);
            
            // Time the QFT application
            let start = Instant::now();
            qft::apply(&mut state);
            let duration = start.elapsed();
            
            let execution_time_ms = duration.as_secs_f64() * 1000.0;
            execution_times.push(execution_time_ms);
            
            print!("  Trial {:2}/{}: {:7.3} ms\r", i+1, num_trials, execution_time_ms);
        }
        println!();
        
        // Test round-trip fidelity if appropriate
        if n_qubits <= 15 {
            println!("  🔄 Testing round-trip fidelity...");
            
            let mut state = State::zero_state(n_qubits);
            let mut circuit = Circuit::new(n_qubits);
            circuit.x(0);
            circuit.execute(&mut state);
            
            qft::apply(&mut state);
            qft::apply_inverse(&mut state);
            
            fidelity = Some(state.probability(1)); // |1⟩ = |00...01⟩
        }
        
        // Calculate statistics
        let mean_time = execution_times.iter().sum::<f64>() / num_trials as f64;
        let variance = execution_times.iter()
            .map(|x| (*x - mean_time).powi(2))
            .sum::<f64>() / num_trials as f64;
        let std_dev = variance.sqrt();
        
        // Memory after
        let mem_after = Self::measure_memory_usage();
        let mem_delta = mem_after - mem_before;
        
        // Print summary for this qubit count
        println!("  ✅ Results:");
        println!("    ⏱️  Execution time: {:.3} ± {:.3} ms", mean_time, std_dev);
        println!("    💾 Memory usage:   {:.2} MB", mem_delta);
        println!("    🔧 Gate count:     {}", gate_count);
        println!("    🌌 State size:     {}", 1 << n_qubits);
        
        if let Some(f) = fidelity {
            println!("    🎯 Fidelity:      {:.6}", f);
        }
        
        BenchmarkResult {
            n_qubits,
            execution_time_ms: mean_time,
            std_deviation_ms: std_dev,
            memory_mb: mem_delta,
            gate_count,
            state_size: 1 << n_qubits,
            fidelity,
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
                },
                Err(_) => {
                    println!("❌ Error benchmarking {} qubits - benchmark failed", n_qubits);
                    println!("  (This may be due to memory limitations or other system constraints)");
                    break;
                }
            }
        }
        
        // Save JSON results
        if !self.results.is_empty() {
            let output_file = "/app/rust/qft_benchmark_results.json";
            match File::create(output_file) {
                Ok(mut file) => {
                    let json = serde_json::to_string_pretty(&self.results).unwrap();
                    if let Err(e) = file.write_all(json.as_bytes()) {
                        println!("❌ Error writing benchmark results: {}", e);
                    } else {
                        println!("\n💾 Results saved to: {}", output_file);
                    }
                },
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
        println!("{:<6} | {:<14} | {:<10} | {:<12} | {:<10}", 
                 "Qubits", "Time (ms)", "Gates", "Memory (MB)", "State Size");
        println!("{}", "-".repeat(60));
        
        for result in &self.results {
            println!("{:<6} | {:<14.3} | {:<10} | {:<12.2} | {:<10}", 
                     result.n_qubits, 
                     format!("{:.3} ± {:.3}", result.execution_time_ms, result.std_deviation_ms),
                     result.gate_count,
                     result.memory_mb, 
                     result.state_size);
        }
        
        // Calculate scaling factors
        if self.results.len() >= 2 {
            let first = &self.results[0];
            let last = &self.results[self.results.len() - 1];
            
            let qubit_factor = last.n_qubits as f64 / first.n_qubits as f64;
            let time_factor = last.execution_time_ms / first.execution_time_ms;
            let gate_factor = last.gate_count as f64 / first.gate_count as f64;
            let memory_factor = last.memory_mb / first.memory_mb;
            
            println!("\n📊 Scaling from {} to {} qubits:", first.n_qubits, last.n_qubits);
            println!("• 🎯 Qubit factor:      {:.1}x", qubit_factor);
            println!("• ⏱️  Time factor:       {:.1}x", time_factor);
            println!("• 🔧 Gate factor:       {:.1}x", gate_factor);
            println!("• 💾 Memory factor:     {:.1}x", memory_factor);
            println!("• 📐 Theoretical O(n²): {:.1}x", qubit_factor.powi(2));
        }
    }
}

fn install_dependencies_if_needed() {
    // Minimal dependency checks
    let serde_check = Command::new("cargo")
        .args(&["tree", "--package", "serde"])
        .output();
    
    if serde_check.is_err() || !serde_check.unwrap().status.success() {
        println!("📦 Installing serde and serde_json...");
        let _ = Command::new("cargo")
            .args(&["add", "serde", "serde_json", "--features", "serde/derive"])
            .output();
    }
}

fn main() {
    // Check dependencies
    install_dependencies_if_needed();
    
    let mut benchmark = QFTBenchmark::new();
    
    // Menu for benchmark options
    println!("🎯 Select benchmark range:");
    println!("1. Small (1-8 qubits) - Fast test");
    println!("2. Medium (1-12 qubits) - Moderate test");
    println!("3. Large (1-16 qubits) - Comprehensive test");
    println!("4. Custom range");
    
    let mut input = String::new();
    std::io::stdin().read_line(&mut input).expect("Failed to read input");
    
    let (min_qubits, max_qubits, trials) = match input.trim() {
        "1" => {
            println!("Selected: Small benchmark (1-8 qubits, 5 trials each)");
            (1, 8, 5)
        },
        "2" => {
            println!("Selected: Medium benchmark (1-12 qubits, 3 trials each)");
            (1, 12, 3)
        },
        "3" => {
            println!("Selected: Large benchmark (1-16 qubits, 1 trial each)");
            (1, 16, 1)
        },
        "4" => {
            println!("Enter minimum qubits:");
            let mut min_input = String::new();
            std::io::stdin().read_line(&mut min_input).expect("Failed to read input");
            let min = min_input.trim().parse().unwrap_or(1);
            
            println!("Enter maximum qubits:");
            let mut max_input = String::new();
            std::io::stdin().read_line(&mut max_input).expect("Failed to read input");
            let max = max_input.trim().parse().unwrap_or(8);
            
            println!("Enter trials per test:");
            let mut trials_input = String::new();
            std::io::stdin().read_line(&mut trials_input).expect("Failed to read input");
            let trials = trials_input.trim().parse().unwrap_or(3);
            
            (min, max, trials)
        },
        _ => {
            println!("Invalid choice, using default small range");
            (1, 8, 3)
        }
    };
    
    // Run benchmark
    benchmark.run_benchmark(min_qubits, max_qubits, trials);
    
    println!("\n🎉 Benchmark completed!");
}