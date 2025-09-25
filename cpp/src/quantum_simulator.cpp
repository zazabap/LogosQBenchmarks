#include "quantum_simulator.hpp"
#include <cmath>
#include <random>
#include <fstream>
#include <sstream>

const double PI = M_PI;

// QuantumState implementation
QuantumState::QuantumState(size_t num_qubits) 
    : num_qubits_(num_qubits) {
    size_t size = 1ULL << num_qubits;
    amplitudes_ = StateVector::Zero(size);
    amplitudes_(0) = Complex(1.0, 0.0);
}

void QuantumState::apply_single_gate(const Gate& gate, size_t qubit) {
    size_t size = amplitudes_.size();
    StateVector new_amplitudes = amplitudes_;
    
    for (size_t i = 0; i < size; ++i) {
        if (((i >> qubit) & 1) == 0) {
            size_t j = i | (1ULL << qubit);
            if (j < size) {
                Complex amp0 = amplitudes_(i);
                Complex amp1 = amplitudes_(j);
                
                new_amplitudes(i) = gate(0, 0) * amp0 + gate(0, 1) * amp1;
                new_amplitudes(j) = gate(1, 0) * amp0 + gate(1, 1) * amp1;
            }
        }
    }
    
    amplitudes_ = new_amplitudes;
}

void QuantumState::apply_controlled_gate(const Gate& gate, size_t control, size_t target) {
    size_t size = amplitudes_.size();
    StateVector new_amplitudes = amplitudes_;
    
    for (size_t i = 0; i < size; ++i) {
        if (((i >> control) & 1) == 1) {
            if (((i >> target) & 1) == 0) {
                size_t j = i | (1ULL << target);
                if (j < size) {
                    Complex amp0 = amplitudes_(i);
                    Complex amp1 = amplitudes_(j);
                    
                    new_amplitudes(i) = gate(0, 0) * amp0 + gate(0, 1) * amp1;
                    new_amplitudes(j) = gate(1, 0) * amp0 + gate(1, 1) * amp1;
                }
            }
        }
    }
    
    amplitudes_ = new_amplitudes;
}

double QuantumState::get_probability(size_t state) const {
    if (state < amplitudes_.size()) {
        return std::norm(amplitudes_(state));
    }
    return 0.0;
}

// Gates implementation
Gate Gates::pauli_x() {
    Gate gate;
    gate << 0, 1,
            1, 0;
    return gate;
}

Gate Gates::pauli_y() {
    Gate gate;
    gate << 0, Complex(0, -1),
            Complex(0, 1), 0;
    return gate;
}

Gate Gates::pauli_z() {
    Gate gate;
    gate << 1, 0,
            0, -1;
    return gate;
}

Gate Gates::hadamard() {
    double inv_sqrt2 = 1.0 / std::sqrt(2.0);
    Gate gate;
    gate << inv_sqrt2, inv_sqrt2,
            inv_sqrt2, -inv_sqrt2;
    return gate;
}

Gate Gates::rx(double theta) {
    double cos_half = std::cos(theta / 2.0);
    double sin_half = std::sin(theta / 2.0);
    
    Gate gate;
    gate << cos_half, Complex(0, -sin_half),
            Complex(0, -sin_half), cos_half;
    return gate;
}

Gate Gates::ry(double theta) {
    double cos_half = std::cos(theta / 2.0);
    double sin_half = std::sin(theta / 2.0);
    
    Gate gate;
    gate << cos_half, -sin_half,
            sin_half, cos_half;
    return gate;
}

Gate Gates::rz(double theta) {
    Complex exp_neg = std::exp(Complex(0, -theta / 2.0));
    Complex exp_pos = std::exp(Complex(0, theta / 2.0));
    
    Gate gate;
    gate << exp_neg, 0,
            0, exp_pos;
    return gate;
}

// QuantumCircuit implementation
QuantumCircuit::QuantumCircuit(size_t num_qubits) : num_qubits_(num_qubits) {}

QuantumCircuit& QuantumCircuit::h(size_t qubit) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::hadamard(), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::x(size_t qubit) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::pauli_x(), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::y(size_t qubit) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::pauli_y(), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::z(size_t qubit) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::pauli_z(), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::rx(size_t qubit, double theta) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::rx(theta), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::ry(size_t qubit, double theta) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::ry(theta), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::rz(size_t qubit, double theta) {
    operations_.push_back({Operation::SINGLE_GATE, Gates::rz(theta), qubit, 0, 0});
    return *this;
}

QuantumCircuit& QuantumCircuit::cnot(size_t control, size_t target) {
    operations_.push_back({Operation::CONTROLLED_GATE, Gates::pauli_x(), 0, control, target});
    return *this;
}

QuantumState QuantumCircuit::execute() const {
    QuantumState state(num_qubits_);
    
    for (const auto& op : operations_) {
        if (op.type == Operation::SINGLE_GATE) {
            state.apply_single_gate(op.gate, op.qubit);
        } else {
            state.apply_controlled_gate(op.gate, op.control, op.target);
        }
    }
    
    return state;
}

// BenchmarkRunner implementation
double BenchmarkRunner::get_memory_usage() {
    std::ifstream file("/proc/self/status");
    std::string line;
    while (std::getline(file, line)) {
        if (line.substr(0, 6) == "VmRSS:") {
            std::istringstream iss(line);
            std::string vmrss, value, unit;
            iss >> vmrss >> value >> unit;
            return std::stod(value) / 1024.0; // Convert KB to MB
        }
    }
    return 0.0;
}

BenchmarkResult BenchmarkRunner::benchmark_ghz_state(size_t num_qubits) {
    double start_memory = get_memory_usage();
    auto start_time = std::chrono::high_resolution_clock::now();
    
    QuantumCircuit circuit(num_qubits);
    circuit.h(0);
    for (size_t i = 1; i < num_qubits; ++i) {
        circuit.cnot(0, i);
    }
    
    auto final_state = circuit.execute();
    
    auto end_time = std::chrono::high_resolution_clock::now();
    double end_memory = get_memory_usage();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    
    return {
        "GHZ-" + std::to_string(num_qubits),
        num_qubits,
        num_qubits,
        duration.count() / 1000.0,
        end_memory - start_memory,
        2
    };
}

BenchmarkResult BenchmarkRunner::benchmark_random_circuit(size_t num_qubits, size_t num_gates) {
    double start_memory = get_memory_usage();
    auto start_time = std::chrono::high_resolution_clock::now();
    
    QuantumCircuit circuit(num_qubits);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> gate_dist(0, 5);
    std::uniform_int_distribution<> qubit_dist(0, num_qubits - 1);
    std::uniform_real_distribution<> angle_dist(0.0, 2.0 * PI);
    
    for (size_t i = 0; i < num_gates; ++i) {
        int gate_type = gate_dist(gen);
        size_t qubit = qubit_dist(gen);
        double angle = angle_dist(gen);
        
        switch (gate_type) {
            case 0: circuit.h(qubit); break;
            case 1: circuit.x(qubit); break;
            case 2: circuit.y(qubit); break;
            case 3: circuit.z(qubit); break;
            case 4: circuit.rx(qubit, angle); break;
            case 5: circuit.ry(qubit, angle); break;
            default: circuit.rz(qubit, angle); break;
        }
    }
    
    size_t num_cnots = num_gates / 4;
    for (size_t i = 0; i < num_cnots; ++i) {
        size_t control = qubit_dist(gen);
        size_t target = qubit_dist(gen);
        while (target == control) {
            target = qubit_dist(gen);
        }
        circuit.cnot(control, target);
    }
    
    auto final_state = circuit.execute();
    
    auto end_time = std::chrono::high_resolution_clock::now();
    double end_memory = get_memory_usage();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    
    return {
        "Random-" + std::to_string(num_qubits) + "-" + std::to_string(num_gates),
        num_qubits,
        num_gates + num_cnots,
        duration.count() / 1000.0,
        end_memory - start_memory,
        num_gates + num_cnots
    };
}

BenchmarkResult BenchmarkRunner::benchmark_qft_circuit(size_t num_qubits) {
    double start_memory = get_memory_usage();
    auto start_time = std::chrono::high_resolution_clock::now();
    
    QuantumCircuit circuit(num_qubits);
    
    for (size_t i = 0; i < num_qubits; ++i) {
        circuit.h(i);
        for (size_t j = i + 1; j < num_qubits; ++j) {
            double angle = PI / (1ULL << (j - i));
            circuit.rz(j, angle);
            circuit.cnot(j, i);
            circuit.rz(j, -angle);
            circuit.cnot(j, i);
        }
    }
    
    auto final_state = circuit.execute();
    
    auto end_time = std::chrono::high_resolution_clock::now();
    double end_memory = get_memory_usage();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    size_t num_gates = num_qubits + (num_qubits * (num_qubits - 1)) * 2;
    
    return {
        "QFT-" + std::to_string(num_qubits),
        num_qubits,
        num_gates,
        duration.count() / 1000.0,
        end_memory - start_memory,
        num_qubits * 2
    };
}