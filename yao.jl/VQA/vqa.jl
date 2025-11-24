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

# Load only the Yao components we need (avoids YaoPlots circular dependency issues)
using YaoBlocks
using YaoArrayRegister
import YaoBlocks: chain, control, put, Ry, X

const NUM_QUBITS = 4
const LAYERS = 3

const PAULI_MATRICES = Dict(
    'I' => Matrix{ComplexF64}(I, 2, 2),
    'X' => ComplexF64[0 1; 1 0],
    'Y' => ComplexF64[0 -im; im 0],
    'Z' => ComplexF64[1 0; 0 -1],
)

struct FrameworkPerformanceRow
    name::String
    energy::Float64
    iterations::Int
    runtime_ms::Float64
end

"""
Generate the STO-3G hydrogen Hamiltonian coefficients (Jordan–Wigner mapped).
Returns a vector of (label, coefficient) pairs where label is a 4-character Pauli string.
"""
function create_h2_hamiltonian_terms()
    terms = Vector{Tuple{String, Float64}}()
    push!(terms, ("IIII", -0.810_547_980_537_324))

    for (idx, coeff) in enumerate([
        0.172_183_932_619_155,
        0.172_183_932_619_155,
        -0.225_753_492_224_023,
        -0.225_753_492_224_023,
    ])
        label = ["I", "I", "I", "I"]
        label[idx] = "Z"
        push!(terms, (join(label), coeff))
    end

    for ((q1, q2), coeff) in [
        ((1, 2), 0.120_912_632_617_766),
        ((1, 3), 0.168_927_538_700_879),
        ((1, 4), 0.045_232_799_946_057),
        ((2, 3), 0.045_232_799_946_057),
        ((2, 4), 0.168_927_538_700_879),
        ((3, 4), 0.120_912_632_617_766),
    ]
        label = ["I", "I", "I", "I"]
        label[q1] = "Z"
        label[q2] = "Z"
        push!(terms, (join(label), coeff))
    end

    for ((q1, q2), coeff) in [
        ((1, 2), 0.166_145_432_563_824),
        ((3, 4), 0.174_643_430_683_004),
    ]
        for axis in ("X", "Y")
            label = ["I", "I", "I", "I"]
            label[q1] = axis
            label[q2] = axis
            push!(terms, (join(label), coeff))
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

function build_hamiltonian_matrix(terms)
    dim = 2^NUM_QUBITS
    matrix = zeros(ComplexF64, dim, dim)
    for (label, coeff) in terms
        matrix .+= coeff * pauli_matrix(label)
    end
    return matrix
end

function compute_exact_ground_state_energy(matrix::Matrix{ComplexF64})
    eigenvalues = eigvals(Hermitian(matrix))
    return minimum(real.(eigenvalues))
end

function hardware_efficient_ansatz(params::AbstractVector{<:Real})
    expected_length = NUM_QUBITS * LAYERS
    @assert length(params) == expected_length "Expected $expected_length params, got $(length(params))"

    ops = Any[]
    idx = 1
    for _ in 1:LAYERS
        for wire in 1:NUM_QUBITS
            push!(ops, put(NUM_QUBITS, wire => Ry(params[idx])))
            idx += 1
        end
        for (control_wire, target_wire) in zip(1:NUM_QUBITS-1, 2:NUM_QUBITS)
            push!(ops, control(control_wire, target_wire => X))
        end
    end
    return chain(NUM_QUBITS, ops...)
end

function statevector(params::AbstractVector{<:Real})
    circuit = hardware_efficient_ansatz(params)
    reg = zero_state(NUM_QUBITS)
    reg = apply!(reg, circuit)
    return vec(reg.state)
end

function expectation_energy(params::AbstractVector{<:Real}, h_matrix::Matrix{ComplexF64})
    ψ = statevector(params)
    return real(dot(ψ, h_matrix * ψ))
end

function parameter_shift_gradient(cost_fn::Function, params::Vector{Float64})
    shift = π / 2
    grad = similar(params)
    temp = copy(params)
    for i in eachindex(params)
        temp[i] = params[i] + shift
        forward = cost_fn(temp)
        temp[i] = params[i] - shift
        backward = cost_fn(temp)
        grad[i] = 0.5 * (forward - backward)
        temp[i] = params[i]
    end
    return grad
end

function run_yao_vqe(h_matrix::Matrix{ComplexF64}, exact_energy::Float64)
    Random.seed!(1337)
    param_count = NUM_QUBITS * LAYERS
    params = 2π .* rand(param_count)
    cost_fn = θ -> expectation_energy(θ, h_matrix)

    lr = 0.01
    β1, β2 = 0.9, 0.999
    ε = 1e-8
    max_iters = 350
    tolerance = 1e-6

    m = zeros(param_count)
    v = zeros(param_count)
    iter = 0
    converged = false
    start_time = time()

    for t in 1:max_iters
        grad = parameter_shift_gradient(cost_fn, params)
        m = β1 .* m .+ (1 - β1) .* grad
        v = β2 .* v .+ (1 - β2) .* (grad .^ 2)
        m_hat = m ./ (1 - β1^t)
        v_hat = v ./ (1 - β2^t)
        params .-= lr .* m_hat ./ (sqrt.(v_hat) .+ ε)
        energy = cost_fn(params)
        iter = t

        if norm(grad) < tolerance
            converged = true
            break
        end
    end

    runtime_ms = (time() - start_time) * 1000
    final_energy = cost_fn(params)
    delta = abs(final_energy - exact_energy)

    return Dict(
        "framework" => "Yao.jl (Julia)",
        "exact_energy" => exact_energy,
        "vqe_energy" => final_energy,
        "energy_error" => delta,
        "iterations" => iter,
        "runtime_ms" => round(runtime_ms, digits=2),
        "parameters" => param_count,
        "converged" => converged,
    )
end

function print_framework_comparison(rows::Vector{FrameworkPerformanceRow}, exact_energy::Float64)
    println("\n" * "="^70)
    println("Cross-Framework VQE Comparison (H₂, STO-3G)")
    println("="^70)
    println(@sprintf("%-22s | %13s | %10s | %13s", "Framework", "Energy (Ha)", "Iterations", "Runtime (ms)"))
    println("-"^70)
    for row in rows
        println(@sprintf("%-22s | %13.6f | %10d | %13.2f", row.name, row.energy, row.iterations, row.runtime_ms))
    end
    best_row = rows[1]
    for row in rows[2:end]
        if row.energy < best_row.energy
            best_row = row
        end
    end
    println(@sprintf(
        "\nBest energy: %s (%.6f Ha, Δ vs exact = %.6f Ha)",
        best_row.name,
        best_row.energy,
        abs(best_row.energy - exact_energy),
    ))
end

function main()
    terms = create_h2_hamiltonian_terms()
    h_matrix = build_hamiltonian_matrix(terms)
    exact_energy = compute_exact_ground_state_energy(h_matrix)
    result = run_yao_vqe(h_matrix, exact_energy)
    
    # Write to JSON file
    output_file = get(ENV, "VQA_OUTPUT_FILE", "yao_vqa_result.json")
    open(output_file, "w") do f
        JSON.print(f, result, 2)
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
