#!/usr/bin/env julia

# Activate the local Yao.jl environment if available
try
    using Pkg
    project_root = joinpath(@__DIR__, "..")
    if isfile(joinpath(project_root, "Project.toml"))
        Pkg.activate(project_root)
        Pkg.instantiate()
    end
catch e
    @warn "Unable to activate Yao.jl project environment" error=e
end

using JSON
using LinearAlgebra
using Printf
using Random
using Base.MathConstants

# Load only the Yao components we need
using YaoBlocks
using YaoArrayRegister
import YaoBlocks: chain, control, put, X, Y, Z, Rx, Ry, Rz

"""
XYZ-Heisenberg Model Benchmark for Yao.jl.

This benchmark measures the performance of simulating the XYZ-Heisenberg model
using Yao.jl. The Hamiltonian is:
H = -Σᵢⱼ [Jₓ XᵢXⱼ + Jᵧ YᵢYⱼ + Jᵧ ZᵢZⱼ] - h Σᵢ Zᵢ

This benchmark measures:
- Circuit execution time
- Energy expectation values
- Resource usage
"""

const PAULI_MATRICES = Dict(
    'I' => Matrix{ComplexF64}(I, 2, 2),
    'X' => ComplexF64[0 1; 1 0],
    'Y' => ComplexF64[0 -im; im 0],
    'Z' => ComplexF64[1 0; 0 -1],
)

"""
Create the XYZ Heisenberg Hamiltonian terms for a 1D chain with nearest-neighbor interactions.
H = -Σᵢ [Jₓ XᵢXᵢ₊₁ + Jᵧ YᵢYᵢ₊₁ + Jᵧ ZᵢZᵢ₊₁] - h Σᵢ Zᵢ
"""
function create_xyz_heisenberg_hamiltonian_terms(
    num_qubits::Int,
    jx::Float64,
    jy::Float64,
    jz::Float64,
    external_field::Float64,
)
    terms = Vector{Tuple{String, Float64}}()
    
    # Nearest-neighbor interactions (chain topology)
    for i in 1:(num_qubits - 1)
        # XX interaction
        if abs(jx) > 1e-10
            label = ["I" for _ in 1:num_qubits]
            label[i] = "X"
            label[i + 1] = "X"
            push!(terms, (join(label), -jx))
        end
        
        # YY interaction
        if abs(jy) > 1e-10
            label = ["I" for _ in 1:num_qubits]
            label[i] = "Y"
            label[i + 1] = "Y"
            push!(terms, (join(label), -jy))
        end
        
        # ZZ interaction
        if abs(jz) > 1e-10
            label = ["I" for _ in 1:num_qubits]
            label[i] = "Z"
            label[i + 1] = "Z"
            push!(terms, (join(label), -jz))
        end
    end
    
    # External magnetic field (Z direction)
    if abs(external_field) > 1e-10
        for i in 1:num_qubits
            label = ["I" for _ in 1:num_qubits]
            label[i] = "Z"
            push!(terms, (join(label), external_field))  # Negate to match other frameworks
        end
    end
    
    return terms
end

function pauli_matrix(label::String)
    mat = PAULI_MATRICES[label[1]]
    for idx in 2:length(label)
        mat = kron(mat, PAULI_MATRICES[label[idx]])
    end
    return mat
end

function build_hamiltonian_matrix(terms, num_qubits::Int)
    dim = 2^num_qubits
    matrix = zeros(ComplexF64, dim, dim)
    for (label, coeff) in terms
        matrix .+= coeff * pauli_matrix(label)
    end
    return matrix
end

function calculate_energy(state::Vector{ComplexF64}, h_matrix::Matrix{ComplexF64})
    """Calculate the expectation value of the Hamiltonian for a given state."""
    return real(dot(state, h_matrix * state))
end

"""
Build a circuit that implements time evolution using Trotterization.
Manually implements first-order Trotter decomposition.
"""
function build_time_evolution_circuit(
    num_qubits::Int,
    terms::Vector{Tuple{String, Float64}},
    time_steps::Int,
    dt::Float64,
    jx::Float64,
    jy::Float64,
    jz::Float64,
    time_dependent_field::Bool = false,
    field_amplitude::Float64 = 0.0,
    field_frequency::Float64 = 1.0,
)
    ops = Any[]
    
    # Prepare initial state: |1111...⟩ (all spins up)
    for i in 1:num_qubits
        push!(ops, put(num_qubits, i => X))
    end
    
    # Apply time evolution using Trotterization
    current_time = 0.0
    for step in 1:time_steps
        # Get Hamiltonian terms (may be time-dependent)
        if time_dependent_field
            # Create time-dependent Hamiltonian with oscillating field
            h_t = field_amplitude * sin(field_frequency * current_time)
            # Note: jx, jy, jz are captured from outer scope
            terms = create_xyz_heisenberg_hamiltonian_terms(
                num_qubits, jx, jy, jz, h_t
            )
        end
        
        # For each Hamiltonian term, apply exp(-i*H_i*dt)
        for (label, coeff) in terms
            # Find non-identity Pauli operators
            non_id_indices = Int[]
            pauli_labels = Char[]
            for (idx, char) in enumerate(collect(label))
                if char != 'I'
                    push!(non_id_indices, idx)
                    push!(pauli_labels, char)
                end
            end
            
            if length(non_id_indices) == 0
                continue
            end
            
            angle = 2.0 * coeff * dt
            
            if length(non_id_indices) == 1
                # Single-qubit rotation
                qubit = non_id_indices[1]
                if pauli_labels[1] == 'X'
                    push!(ops, put(num_qubits, qubit => Rx(angle)))
                elseif pauli_labels[1] == 'Y'
                    push!(ops, put(num_qubits, qubit => Ry(angle)))
                elseif pauli_labels[1] == 'Z'
                    push!(ops, put(num_qubits, qubit => Rz(angle)))
                end
            elseif length(non_id_indices) == 2
                # Two-qubit rotation (XX, YY, or ZZ)
                q1, q2 = non_id_indices[1], non_id_indices[2]
                if pauli_labels[1] == 'X' && pauli_labels[2] == 'X'
                    # RXX gate: exp(-i*θ/2 * X⊗X) = CNOT * RY(θ) on target * CNOT
                    push!(ops, put(num_qubits, q2 => Ry(angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                    push!(ops, put(num_qubits, q2 => Ry(-angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                elseif pauli_labels[1] == 'Y' && pauli_labels[2] == 'Y'
                    # RYY gate: exp(-i*θ/2 * Y⊗Y) = CNOT * RX(θ) on target * CNOT
                    push!(ops, put(num_qubits, q2 => Rx(angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                    push!(ops, put(num_qubits, q2 => Rx(-angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                elseif pauli_labels[1] == 'Z' && pauli_labels[2] == 'Z'
                    # RZZ gate: exp(-i*θ/2 * Z⊗Z) = CNOT * RZ(θ) on target * CNOT
                    push!(ops, put(num_qubits, q2 => Rz(angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                    push!(ops, put(num_qubits, q2 => Rz(-angle)))
                    push!(ops, control(num_qubits, q1, q2 => X))
                end
            end
        end
        
        current_time += dt
    end
    
    return chain(num_qubits, ops...)
end

"""
Run the XYZ Heisenberg model benchmark.

Returns a dictionary with benchmark results.
"""
function run_xyz_heisenberg_benchmark(
    num_qubits::Int,
    jx::Float64 = 1.0,
    jy::Float64 = 1.0,
    jz::Float64 = 1.0,
    external_field::Float64 = 0.0,
    time_steps::Int = 10,
    dt::Float64 = 0.1,
    time_dependent_field::Bool = false,
    field_amplitude::Float64 = 0.0,
    field_frequency::Float64 = 1.0,
)
    # Create Hamiltonian terms
    terms = create_xyz_heisenberg_hamiltonian_terms(
        num_qubits, jx, jy, jz, external_field
    )
    
    # Build Hamiltonian matrix
    h_matrix = build_hamiltonian_matrix(terms, num_qubits)
    
    # Prepare initial state: |1111...⟩
    initial_state = zero_state(num_qubits)
    # Set to |1111...⟩ by applying X to all qubits
    for i in 1:num_qubits
        initial_state = apply!(initial_state, put(num_qubits, i => X))
    end
    
    # Calculate initial energy
    initial_state_vec = vec(initial_state.state)
    initial_energy = calculate_energy(initial_state_vec, h_matrix)
    
    # Build circuit
    circuit = build_time_evolution_circuit(
        num_qubits, terms, time_steps, dt, jx, jy, jz,
        time_dependent_field, field_amplitude, field_frequency
    )
    
    # Measure memory before
    mem_before = Base.Sys.maxrss() / 1024 / 1024  # MB
    
    # Measure execution time
    start_time = time()
    final_state = apply!(initial_state, circuit)
    runtime_ms = (time() - start_time) * 1000
    
    # Measure memory after
    mem_after = Base.Sys.maxrss() / 1024 / 1024  # MB
    memory_usage_mb = max(0.0, mem_after - mem_before)
    
    # Calculate final energy
    # For time-dependent case, use the Hamiltonian at final time
    final_state_vec = vec(final_state.state)
    if time_dependent_field
        final_time = time_steps * dt
        h_final = field_amplitude * sin(field_frequency * final_time)
        final_terms = create_xyz_heisenberg_hamiltonian_terms(
            num_qubits, jx, jy, jz, h_final
        )
        final_h_matrix = build_hamiltonian_matrix(final_terms, num_qubits)
        final_energy = calculate_energy(final_state_vec, final_h_matrix)
    else
        final_energy = calculate_energy(final_state_vec, h_matrix)
    end
    energy_change = final_energy - initial_energy
    
    # Count operations (approximate: each time step has Trotter steps)
    # For nearest-neighbor interactions: 3*(n-1) terms per time step
    num_interactions = num_qubits > 1 ? 3 * (num_qubits - 1) : 0
    num_field_terms = abs(external_field) > 1e-10 ? num_qubits : 0
    num_operations = time_steps * (num_interactions + num_field_terms) + num_qubits  # +num_qubits for initial X gates
    
    return Dict(
        "framework" => "Yao.jl (Julia)",
        "qubits" => num_qubits,
        "time_steps" => time_steps,
        "dt" => round(dt, digits=6),
        "jx" => round(jx, digits=6),
        "jy" => round(jy, digits=6),
        "jz" => round(jz, digits=6),
        "external_field" => round(external_field, digits=6),
        "initial_energy" => round(initial_energy, digits=10),
        "final_energy" => round(final_energy, digits=10),
        "energy_change" => round(energy_change, digits=10),
        "runtime_ms" => round(runtime_ms, digits=2),
        "num_operations" => num_operations,
        "memory_usage_mb" => round(memory_usage_mb, digits=2),
        "time_dependent_field" => time_dependent_field,
        "field_amplitude" => time_dependent_field ? round(field_amplitude, digits=6) : 0.0,
        "field_frequency" => time_dependent_field ? round(field_frequency, digits=6) : 0.0,
    )
end

"""
Main entry point for the benchmark.
"""
function main()
    # Parse configuration from environment variables
    num_qubits = parse(Int, get(ENV, "XYZ_QUBITS", "4"))
    time_steps = parse(Int, get(ENV, "XYZ_STEPS", "10"))
    dt = parse(Float64, get(ENV, "XYZ_DT", "0.1"))
    jx = parse(Float64, get(ENV, "XYZ_JX", "1.0"))
    jy = parse(Float64, get(ENV, "XYZ_JY", "1.0"))
    jz = parse(Float64, get(ENV, "XYZ_JZ", "1.0"))
    external_field = parse(Float64, get(ENV, "XYZ_FIELD", "0.0"))
    
    # Time-dependent field parameters (for non-conserved energy case)
    time_dependent = lowercase(get(ENV, "XYZ_TIME_DEPENDENT", "true")) == "true"
    field_amplitude = parse(Float64, get(ENV, "XYZ_FIELD_AMPLITUDE", "2.0"))
    field_frequency = parse(Float64, get(ENV, "XYZ_FIELD_FREQUENCY", "1.0"))
    
    # Run benchmark
    result = run_xyz_heisenberg_benchmark(
        num_qubits,
        jx,
        jy,
        jz,
        external_field,
        time_steps,
        dt,
        time_dependent,
        field_amplitude,
        field_frequency,
    )
    
    # Write to JSON file
    output_file = get(ENV, "XYZ_OUTPUT_FILE", "yao_xyz_heisenberg.json")
    open(output_file, "w") do f
        JSON.print(f, result)
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

