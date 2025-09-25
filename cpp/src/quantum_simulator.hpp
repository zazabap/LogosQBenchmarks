#pragma once

#include <complex>
#include <vector>
#include <memory>
#include <string>
#include <chrono>
#include <Eigen/Dense>

using Complex = std::complex<double>;
using StateVector = Eigen::VectorXcd;
using Gate = Eigen::Matrix2cd;

class QuantumState {
public:
    explicit QuantumState(size_t num_qubits);
    
    void apply_single_gate(const Gate& gate, size_t qubit);
    void apply_controlled_gate(const Gate& gate, size_t control, size_t target);
    
    double get_probability(size_t state) const;
    size_t size() const { return amplitudes_.size(); }
    size_t num_qubits() const { return num_qubits_; }

private:
    StateVector amplitudes_;
    size_t num_qubits_;
};

class Gates {
public:
    static Gate pauli_x();
    static Gate pauli_y();
    static Gate pauli_z();
    static Gate hadamard();
    static Gate rx(double theta);
    static Gate ry(double theta);
    static Gate rz(double theta);
};

struct Operation {
    enum Type { SINGLE_GATE, CONTROLLED_GATE };
    
    Type type;
    Gate gate;
    size_t qubit;
    size_t control;
    size_t target;
};

class QuantumCircuit {
public:
    explicit QuantumCircuit(size_t num_qubits);
    
    QuantumCircuit& h(size_t qubit);
    QuantumCircuit& x(size_t qubit);
    QuantumCircuit& y(size_t qubit);
    QuantumCircuit& z(size_t qubit);
    QuantumCircuit& rx(size_t qubit, double theta);
    QuantumCircuit& ry(size_t qubit, double theta);
    QuantumCircuit& rz(size_t qubit, double theta);
    QuantumCircuit& cnot(size_t control, size_t target);
    
    QuantumState execute() const;
    
    size_t num_qubits() const { return num_qubits_; }
    size_t num_operations() const { return operations_.size(); }

private:
    size_t num_qubits_;
    std::vector<Operation> operations_;
};

struct BenchmarkResult {
    std::string name;
    size_t num_qubits;
    size_t num_gates;
    double execution_time_ms;
    double memory_usage_mb;
    size_t circuit_depth;
};

struct BenchmarkSuite {
    std::string library;
    std::string version;
    std::vector<BenchmarkResult> results;
    double total_time_ms;
};

class BenchmarkRunner {
public:
    static BenchmarkResult benchmark_ghz_state(size_t num_qubits);
    static BenchmarkResult benchmark_random_circuit(size_t num_qubits, size_t num_gates);
    static BenchmarkResult benchmark_qft_circuit(size_t num_qubits);
    
private:
    static double get_memory_usage();
};