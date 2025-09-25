#include "quantum_simulator.hpp"
#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>

std::string to_json(const BenchmarkSuite& suite) {
    std::ostringstream oss;
    oss << "{\n";
    oss << "  \"library\": \"" << suite.library << "\",\n";
    oss << "  \"version\": \"" << suite.version << "\",\n";
    oss << "  \"results\": [\n";
    
    for (size_t i = 0; i < suite.results.size(); ++i) {
        const auto& result = suite.results[i];
        oss << "    {\n";
        oss << "      \"name\": \"" << result.name << "\",\n";
        oss << "      \"num_qubits\": " << result.num_qubits << ",\n";
        oss << "      \"num_gates\": " << result.num_gates << ",\n";
        oss << "      \"execution_time_ms\": " << std::fixed << std::setprecision(6) << result.execution_time_ms << ",\n";
        oss << "      \"memory_usage_mb\": " << std::fixed << std::setprecision(2) << result.memory_usage_mb << ",\n";
        oss << "      \"circuit_depth\": " << result.circuit_depth << "\n";
        oss << "    }";
        if (i < suite.results.size() - 1) {
            oss << ",";
        }
        oss << "\n";
    }
    
    oss << "  ],\n";
    oss << "  \"total_time_ms\": " << std::fixed << std::setprecision(2) << suite.total_time_ms << "\n";
    oss << "}";
    
    return oss.str();
}

int main() {
    auto suite_start = std::chrono::high_resolution_clock::now();
    std::vector<BenchmarkResult> results;
    
    std::cerr << "Starting C++ quantum benchmarks..." << std::endl;
    
    std::vector<size_t> qubit_sizes = {4, 6, 8, 10, 12};
    
    for (size_t num_qubits : qubit_sizes) {
        if (num_qubits <= 14) {
            std::cerr << "Benchmarking " << num_qubits << " qubits..." << std::endl;
            
            // GHZ state benchmark
            results.push_back(BenchmarkRunner::benchmark_ghz_state(num_qubits));
            
            // Random circuit benchmark
            size_t gate_count = num_qubits * 10;
            results.push_back(BenchmarkRunner::benchmark_random_circuit(num_qubits, gate_count));
            
            // QFT benchmark (only for smaller systems)
            if (num_qubits <= 10) {
                results.push_back(BenchmarkRunner::benchmark_qft_circuit(num_qubits));
            }
        }
    }
    
    auto suite_end = std::chrono::high_resolution_clock::now();
    auto total_duration = std::chrono::duration_cast<std::chrono::milliseconds>(suite_end - suite_start);
    
    BenchmarkSuite benchmark_suite = {
        "C++",
        "1.0.0",
        results,
        static_cast<double>(total_duration.count())
    };
    
    std::cout << to_json(benchmark_suite) << std::endl;
    std::cerr << "C++ benchmarks completed in " << total_duration.count() << "ms" << std::endl;
    
    return 0;
}