using Yao
using BenchmarkTools
using JSON
using Random

struct BenchmarkResult
    name::String
    num_qubits::Int
    num_gates::Int
    execution_time_ms::Float64
    memory_usage_mb::Float64
    circuit_depth::Int
end

struct BenchmarkSuite
    library::String
    version::String
    results::Vector{BenchmarkResult}
    total_time_ms::Float64
end

function get_memory_usage()
    # Get current memory usage in MB
    return Base.Sys.maxrss() / 1024 / 1024  # Convert bytes to MB
end

function benchmark_ghz_state(num_qubits::Int)
    start_memory = get_memory_usage()
    
    # Create GHZ state circuit
    circuit = chain(num_qubits, put(1=>H), [control(1, i=>X) for i in 2:num_qubits]...)
    
    # Benchmark execution
    result = @benchmark apply!(zero_state($num_qubits), $circuit)
    
    end_memory = get_memory_usage()
    
    BenchmarkResult(
        "GHZ-$num_qubits",
        num_qubits,
        num_qubits,  # 1 H + (n-1) CNOT
        minimum(result.times) / 1e6,  # Convert to ms
        end_memory - start_memory,
        2  # Circuit depth
    )
end

function benchmark_random_circuit(num_qubits::Int, num_gates::Int)
    start_memory = get_memory_usage()
    Random.seed!(42)  # For reproducibility
    
    # Create random circuit
    gates = []
    for _ in 1:num_gates
        gate_type = rand(1:6)
        qubit = rand(1:num_qubits)
        angle = rand() * 2π
        
        if gate_type == 1
            push!(gates, put(qubit=>H))
        elseif gate_type == 2
            push!(gates, put(qubit=>X))
        elseif gate_type == 3
            push!(gates, put(qubit=>Y))
        elseif gate_type == 4
            push!(gates, put(qubit=>Z))
        elseif gate_type == 5
            push!(gates, put(qubit=>Rx(angle)))
        else
            push!(gates, put(qubit=>Ry(angle)))
        end
    end
    
    # Add some CNOT gates
    num_cnots = div(num_gates, 4)
    for _ in 1:num_cnots
        control = rand(1:num_qubits)
        target = rand(1:num_qubits)
        while target == control
            target = rand(1:num_qubits)
        end
        push!(gates, control(control, target=>X))
    end
    
    circuit = chain(num_qubits, gates...)
    
    # Benchmark execution
    result = @benchmark apply!(zero_state($num_qubits), $circuit)
    
    end_memory = get_memory_usage()
    
    BenchmarkResult(
        "Random-$num_qubits-$num_gates",
        num_qubits,
        num_gates + num_cnots,
        minimum(result.times) / 1e6,  # Convert to ms
        end_memory - start_memory,
        num_gates + num_cnots  # Simplified depth calculation
    )
end

function benchmark_qft_circuit(num_qubits::Int)
    start_memory = get_memory_usage()
    
    # Create QFT circuit
    circuit = qft_circuit(num_qubits)
    
    # Benchmark execution
    result = @benchmark apply!(zero_state($num_qubits), $circuit)
    
    end_memory = get_memory_usage()
    
    num_gates = num_qubits + div(num_qubits * (num_qubits - 1), 2) * 2  # Estimate
    
    BenchmarkResult(
        "QFT-$num_qubits",
        num_qubits,
        num_gates,
        minimum(result.times) / 1e6,  # Convert to ms
        end_memory - start_memory,
        num_qubits
    )
end

function qft_circuit(n::Int)
    circuit = chain(n)
    for i in 1:n
        push!(circuit, put(i=>H))
        for j in (i+1):n
            angle = π / (2^(j-i))
            push!(circuit, control([j], i=>shift(angle)))
        end
    end
    return circuit
end

function main()
    suite_start = time()
    results = BenchmarkResult[]
    
    @info "Starting Yao.jl benchmarks..."
    
    # Test different qubit sizes
    qubit_sizes = [4, 6, 8, 10, 12]
    
    for num_qubits in qubit_sizes
        if num_qubits <= 14  # Limit for exponential memory growth
            @info "Benchmarking $num_qubits qubits..."
            
            # GHZ state benchmark
            push!(results, benchmark_ghz_state(num_qubits))
            
            # Random circuit benchmark
            gate_count = num_qubits * 10
            push!(results, benchmark_random_circuit(num_qubits, gate_count))
            
            # QFT benchmark (only for smaller systems)
            if num_qubits <= 10
                push!(results, benchmark_qft_circuit(num_qubits))
            end
        end
    end
    
    total_time = (time() - suite_start) * 1000  # Convert to ms
    
    benchmark_suite = BenchmarkSuite(
        "Yao.jl",
        "0.8.0",  # Default version if package info not available
        results,
        total_time
    )
    
    # Convert to JSON-compatible format
    json_results = []
    for result in benchmark_suite.results
        push!(json_results, Dict(
            "name" => result.name,
            "num_qubits" => result.num_qubits,
            "num_gates" => result.num_gates,
            "execution_time_ms" => result.execution_time_ms,
            "memory_usage_mb" => result.memory_usage_mb,
            "circuit_depth" => result.circuit_depth
        ))
    end
    
    json_output = Dict(
        "library" => benchmark_suite.library,
        "version" => benchmark_suite.version,
        "results" => json_results,
        "total_time_ms" => benchmark_suite.total_time_ms
    )
    
    println(JSON.json(json_output, 2))
    @info "Yao.jl benchmarks completed in $(total_time)ms"
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end