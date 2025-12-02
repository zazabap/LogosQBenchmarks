#!/usr/bin/env julia

# Activate project environment if not already activated
try
    using Pkg
    project_path = joinpath(@__DIR__, "..")
    if isfile(joinpath(project_path, "Project.toml"))
        Pkg.activate(project_path)
        # Ensure manifest is up to date
        Pkg.resolve()
        Pkg.instantiate()
    end
catch e
    println("Warning: Could not activate project: ", e)
    # If Pkg is not available, try to continue
end

# Install missing dependencies if needed (but don't add to Project.toml)
try
    using Pkg
    deps = Pkg.project().dependencies
    if !haskey(deps, "BenchmarkTools")
        try
            Pkg.add("BenchmarkTools")
            Pkg.resolve()
        catch
            # Continue if installation fails
        end
    end
    if !haskey(deps, "JSON")
        try
            Pkg.add("JSON")
            Pkg.resolve()
        catch
            # Continue if installation fails
        end
    end
    # Ensure everything is instantiated
    Pkg.instantiate()
catch e
    println("Warning: Package installation issue: ", e)
    # Continue even if package installation fails
end

# Try to load Yao with better error handling
# Work around circular dependency issue (Yao <-> YaoPlots)
# Load dependencies in order to avoid circular dependency
yao_loaded = false
try
    # Load core dependencies first, in order
    using YaoBlocks  # Must load first - defines AbstractBlock
    using YaoArrayRegister  # Provides state operations
    # Now try to load Yao (which depends on YaoPlots, but we'll handle that)
    using Yao
    global yao_loaded = true
    println("Yao loaded successfully")
catch e
    println(stderr, "Error loading Yao: ", e)
    println(stderr, "Attempting to work around circular dependency...")
    try
        using Pkg
        # Clear precompilation cache for problematic packages
        println("Clearing precompilation cache...")
        cache_dir = joinpath(homedir(), ".julia", "compiled", "v$(VERSION.major).$(VERSION.minor)")
        for pkg in ["Yao", "YaoPlots", "YaoToEinsum"]
            pkg_cache = joinpath(cache_dir, pkg)
            if ispath(pkg_cache)
                rm(pkg_cache, recursive=true, force=true)
            end
        end
        
        # Try loading again in correct order
        println("Attempting to load dependencies in order...")
        using YaoBlocks
        using YaoArrayRegister
        using Yao
        global yao_loaded = true
        println("Yao loaded successfully after cache clearing")
    catch e2
        println(stderr, "Failed to load Yao: ", e2)
        println(stderr, "Attempting to rebuild Yao...")
        try
            using Pkg
            Pkg.resolve()
            Pkg.instantiate()
            Pkg.build("Yao")
            # Try loading again in order
            using YaoBlocks
            using YaoArrayRegister
            using Yao
            global yao_loaded = true
            println("Yao rebuilt and loaded successfully")
        catch e3
            println(stderr, "Failed to rebuild Yao: ", e3)
            println(stderr, "")
            println(stderr, "The issue is likely due to a circular dependency between Yao and YaoPlots.")
            println(stderr, "This is a known issue with Yao.jl v0.8.14.")
            println(stderr, "Try running with: julia --compiled-modules=no yao_qft_benchmark.jl")
            println(stderr, "")
            exit(1)  # Exit gracefully rather than crashing
        end
    end
end

if !yao_loaded
    println(stderr, "Fatal: Could not load Yao.jl")
    exit(1)
end

using BenchmarkTools
using JSON

# Structure to match other benchmark formats
struct QFTBenchmarkResult
    n_qubits::Int
    execution_time_ms::Float64
    std_deviation_ms::Float64
    memory_mb::Float64
    gate_count::Int
    state_size::Int
    fidelity::Union{Float64, Nothing}
end

function get_memory_usage()
    """Get current memory usage in MB"""
    return Base.Sys.maxrss() / 1024 / 1024  # Convert bytes to MB
end

function qft_circuit(n::Int)
    """Create QFT circuit using Yao.jl"""
    # Try to use built-in QFT if available
    try
        return qft(n)
    catch
        # Fall back to custom implementation
        # Use gates directly - they should be available after loading YaoBlocks
        gates = []
        for i in 1:n
            push!(gates, put(i=>H))
            for j in (i+1):n
                angle = π / (2^(j-i))
                push!(gates, control(j, i=>shift(angle)))
            end
        end
        # Add SWAP gates to reverse order
        for i in 1:div(n, 2)
            push!(gates, put(n, (i, n-i+1)=>SWAP))
        end
        return chain(n, gates...)
    end
end

function qft_inverse_circuit(n::Int)
    """Create inverse QFT circuit"""
    try
        return qft(n)'  # Adjoint of QFT
    catch
        # Custom inverse QFT
        gates = []
        # SWAP gates first
        for i in 1:div(n, 2)
            push!(gates, put(n, (i, n-i+1)=>SWAP))
        end
        # Then gates in reverse order with negative phases
        for i in n:-1:1
            for j in n:-1:(i+1)
                angle = -π / (2^(j-i))
                push!(gates, control(j, i=>shift(angle)))
            end
            push!(gates, put(i=>H))
        end
        return chain(n, gates...)
    end
end

function benchmark_qft_circuit(n_qubits::Int, num_trials::Int=5)
    """Benchmark QFT circuit for given number of qubits"""
    println("\n🔬 Benchmarking $n_qubits-qubit QFT circuit...")
    
    # Theoretical gate count for QFT
    gate_count = n_qubits + div(n_qubits * (n_qubits - 1), 2) + div(n_qubits, 2)
    
    # Memory before
    mem_before = get_memory_usage()
    
    # Create circuit
    circuit = qft_circuit(n_qubits)
    
    # Prepare for measurements
    execution_times = Float64[]
    fidelity = nothing
    
    # Warm-up run
    println("  ⚡ Warm-up run...")
    state = zero_state(n_qubits)
    state = apply!(state, put(n_qubits, 1=>X))
    state = apply!(state, circuit)
    
    # Run benchmark trials
    println("  🏃 Running $num_trials trials...")
    for i in 1:num_trials
        # Reset state for this trial
        state = zero_state(n_qubits)
        state = apply!(state, put(n_qubits, 1=>X))
        
        # Time the QFT application using @elapsed for simple timing
        elapsed_time = @elapsed begin
            state = apply!(state, circuit)
        end
        execution_time_ms = elapsed_time * 1000  # Convert seconds to ms
        push!(execution_times, execution_time_ms)
        
        print("  Trial $i/$num_trials: $(round(execution_time_ms, digits=3)) ms\r")
    end
    println()
    
    # Test round-trip fidelity if appropriate (optional, non-fatal)
    if n_qubits <= 15
        try
            println("  🔄 Testing round-trip fidelity...")
            state = zero_state(n_qubits)
            state = apply!(state, put(n_qubits, 1=>X))
            state = apply!(state, circuit)
            state = apply!(state, qft_inverse_circuit(n_qubits))
            
            # Try to get probabilities - use different methods depending on what's available
            try
                # Try using probs from YaoArrayRegister
                prob_vec = YaoArrayRegister.probs(state)
                fidelity = prob_vec[2]  # Index 2 = binary 1
            catch
                try
                    # Try using measure! or other methods
                    # For now, skip fidelity if not available
                    fidelity = nothing
                catch
                    fidelity = nothing
                end
            end
        catch e
            # Fidelity check failed, but that's okay - continue without it
            println("  ⚠️  Fidelity check skipped: $e")
            fidelity = nothing
        end
    end
    
    # Calculate statistics
    mean_time = sum(execution_times) / num_trials
    variance = sum((t - mean_time)^2 for t in execution_times) / num_trials
    std_dev = sqrt(variance)
    
    # Memory after
    mem_after = get_memory_usage()
    mem_delta = mem_after - mem_before
    
    # Print summary for this qubit count
    println("  ✅ Results:")
    println("    ⏱️  Execution time: $(round(mean_time, digits=3)) ± $(round(std_dev, digits=3)) ms")
    println("    💾 Memory usage:   $(round(mem_delta, digits=2)) MB")
    println("    🔧 Gate count:     $gate_count")
    println("    🌌 State size:     $(1 << n_qubits)")
    
    if fidelity !== nothing
        println("    🎯 Fidelity:      $(round(fidelity, digits=6))")
    end
    
    return QFTBenchmarkResult(
        n_qubits,
        mean_time,
        std_dev,
        mem_delta,
        gate_count,
        1 << n_qubits,
        fidelity
    )
end

function run_benchmark(min_qubits::Int, max_qubits::Int, num_trials::Int)
    """Run comprehensive benchmark across qubit range"""
    println("\n🚀 YAO.JL QFT BENCHMARK")
    println("=" ^ 60)
    
    # Get Yao version
    yao_version = "latest"
    try
        deps = Pkg.dependencies()
        for (uuid, dep) in deps
            if dep.name == "Yao" && dep.version !== nothing
                yao_version = string(dep.version)
                break
            end
        end
    catch
    end
    
    println("💻 Library: Yao.jl v$yao_version")
    println("🎯 Testing qubits: $min_qubits to $max_qubits")
    println("🔄 Trials per test: $num_trials")
    println("=" ^ 60)
    
    results = QFTBenchmarkResult[]
    
    for n_qubits in min_qubits:max_qubits
        try
            result = benchmark_qft_circuit(n_qubits, num_trials)
            push!(results, result)
        catch e
            println("❌ Error benchmarking $n_qubits qubits - skipping this qubit count")
            println("  Error: $e")
            println("  (This may be due to memory limitations or other system constraints)")
            # Continue to next qubit count instead of breaking
            # This allows us to save results from successful qubit counts
            continue
        end
    end
    
    # Save JSON results
    output_file = "/app/yao.jl/QuantumFourierTransform/qft_benchmark_results.json"
    
    if !isempty(results)
        # Convert to JSON-compatible format
        json_results = []
        for result in results
            push!(json_results, Dict(
                "n_qubits" => result.n_qubits,
                "execution_time_ms" => result.execution_time_ms,
                "std_deviation_ms" => result.std_deviation_ms,
                "memory_mb" => result.memory_mb,
                "gate_count" => result.gate_count,
                "state_size" => result.state_size,
                "fidelity" => result.fidelity
            ))
        end
        
        open(output_file, "w") do f
            JSON.print(f, json_results, 2)
        end
        
        println("\n💾 Results saved to: $output_file")
        println("   Saved $(length(results)) benchmark result(s)")
    else
        println("\n⚠️  No results to save - benchmark failed for all qubit counts")
        println("   Expected output file: $output_file")
    end
    
    print_scaling_analysis(results)
end

function print_scaling_analysis(results)
    """Print performance scaling analysis"""
    println("\n📈 PERFORMANCE SCALING ANALYSIS")
    println("=" ^ 60)
    
    if length(results) < 2
        println("⚠️  Not enough data for scaling analysis")
        return
    end
    
    # Print results table
    println(lpad("Qubits", 6), " | ", lpad("Time (ms)", 14), " | ", 
            lpad("Gates", 10), " | ", lpad("Memory (MB)", 12), " | ", 
            lpad("State Size", 10))
    println("-" ^ 60)
    
    for result in results
        time_str = "$(round(result.execution_time_ms, digits=3)) ± $(round(result.std_deviation_ms, digits=3))"
        println(lpad(result.n_qubits, 6), " | ", lpad(time_str, 14), " | ", 
                lpad(result.gate_count, 10), " | ", 
                lpad(round(result.memory_mb, digits=2), 12), " | ", 
                lpad(result.state_size, 10))
    end
    
    # Calculate scaling factors
    if length(results) >= 2
        first = results[1]
        last = results[end]
        
        qubit_factor = last.n_qubits / first.n_qubits
        time_factor = last.execution_time_ms / first.execution_time_ms
        gate_factor = last.gate_count / first.gate_count
        memory_factor = last.memory_mb / first.memory_mb
        
        println("\n📊 Scaling from $(first.n_qubits) to $(last.n_qubits) qubits:")
        println("• 🎯 Qubit factor:      $(round(qubit_factor, digits=1))x")
        println("• ⏱️  Time factor:       $(round(time_factor, digits=1))x")
        println("• 🔧 Gate factor:       $(round(gate_factor, digits=1))x")
        println("• 💾 Memory factor:     $(round(memory_factor, digits=1))x")
        println("• 📐 Theoretical O(n²): $(round(qubit_factor^2, digits=1))x")
    end
end

function main()
    # Standardized benchmark: 1-12 qubits, 5 trials each
    min_qubits = 1
    max_qubits = 12
    trials = 5
    
    println("🎯 Running standardized QFT benchmark: $min_qubits to $max_qubits qubits, $trials trials each")
    
    # Run benchmark
    run_benchmark(min_qubits, max_qubits, trials)
    
    println("\n🎉 Benchmark completed!")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

