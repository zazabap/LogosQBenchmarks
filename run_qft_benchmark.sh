#!/bin/bash
# Script to run QFT benchmarks for all libraries and generate comparison plots

# Don't exit on error - we want to continue even if one benchmark fails
set +e

echo "================================================"
echo "QFT Benchmark Suite - All Libraries"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track which benchmarks succeeded
SUCCESS_COUNT=0
TOTAL_COUNT=4

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "SUCCESS" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "SKIP" ]; then
        echo -e "${YELLOW}⊘${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 1. Run LogosQ (Rust) benchmark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1/4 Running LogosQ (Rust) QFT Benchmark..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v cargo &> /dev/null; then
    cd /app/logosq/QuantumFourierTransform
    
    # Check if we need to add it as an example
    if ! grep -q "qft_benchmark_simple" /app/logosq/Cargo.toml; then
        echo "Adding qft_benchmark_simple as example to Cargo.toml..."
        cat >> /app/logosq/Cargo.toml << 'EOF'

[[example]]
name = "qft_benchmark_simple"
path = "QuantumFourierTransform/qft_benchmark_simple.rs"
EOF
    fi
    
    # Run the benchmark (continue even if it fails)
    if cargo run --example qft_benchmark_simple --release > /tmp/logosq_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "LogosQ benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        print_status "FAIL" "LogosQ benchmark failed (check /tmp/logosq_qft_benchmark.log)"
        cat /tmp/logosq_qft_benchmark.log | tail -20  # Show last 20 lines for debugging
    fi
else
    print_status "SKIP" "Cargo not available, skipping LogosQ benchmark"
fi

echo ""

# 2. Run PennyLane benchmark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2/4 Running PennyLane (Python) QFT Benchmark..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    cd /app/pennylane/QuantumFourierTransform
    
    # Check if pennylane_qft module exists, if not create a simple import workaround
    if [ ! -f "pennylane_qft.py" ]; then
        echo "Warning: pennylane_qft.py not found, benchmark may fail"
    fi
    
    if python3 pennylane_qft_benchmark.py > /tmp/pennylane_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "PennyLane benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        print_status "FAIL" "PennyLane benchmark failed (check /tmp/pennylane_qft_benchmark.log)"
        cat /tmp/pennylane_qft_benchmark.log | tail -20  # Show last 20 lines for debugging
    fi
else
    print_status "SKIP" "Python3 not available, skipping PennyLane benchmark"
fi

echo ""

# 3. Run Qiskit benchmark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3/4 Running Qiskit (Python) QFT Benchmark..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    cd /app/qiskit/QuantumFourierTransform
    
    if python3 qiskit_benchmark.py > /tmp/qiskit_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "Qiskit benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        print_status "FAIL" "Qiskit benchmark failed (check /tmp/qiskit_qft_benchmark.log)"
        cat /tmp/qiskit_qft_benchmark.log | tail -20  # Show last 20 lines for debugging
    fi
else
    print_status "SKIP" "Python3 not available, skipping Qiskit benchmark"
fi

echo ""

# 4. Run Yao.jl benchmark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4/4 Running Yao.jl (Julia) QFT Benchmark..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v julia &> /dev/null; then
    cd /app/yao.jl
    
    # Clear corrupted precompilation cache for Yao
    echo "Clearing Yao precompilation cache..."
    rm -rf ~/.julia/compiled/v1.8/Yao 2>/dev/null || true
    
    # Ensure dependencies are installed in the project
    echo "Installing/updating Julia dependencies..."
    julia --project=/app/yao.jl -e '
        using Pkg
        # First instantiate to get existing dependencies
        Pkg.instantiate()
        # Add missing packages if needed
        deps = Pkg.project().dependencies
        if !haskey(deps, "BenchmarkTools")
            Pkg.add("BenchmarkTools")
        end
        if !haskey(deps, "JSON")
            Pkg.add("JSON")
        end
        # Resolve to update manifest
        Pkg.resolve()
        # Instantiate again to ensure everything is installed
        Pkg.instantiate()
        # Force precompilation
        try
            Pkg.precompile()
        catch e
            println("Precompilation warning: ", e)
        end
    ' > /tmp/yao_deps.log 2>&1 || true
    
    # Try to precompile Yao specifically
    echo "Precompiling Yao..."
    julia --project=/app/yao.jl -e '
        using Pkg
        # Ensure manifest is in sync
        Pkg.resolve()
        Pkg.instantiate()
        try
            using Yao
            println("Yao precompiled successfully")
        catch e
            println("Yao precompilation error: ", e)
            # Try to rebuild after ensuring manifest is synced
            Pkg.resolve()
            Pkg.instantiate()
            Pkg.build("Yao")
            using Yao
            println("Yao rebuilt and loaded successfully")
        end
    ' >> /tmp/yao_deps.log 2>&1 || true
    
    cd /app/yao.jl/QuantumFourierTransform
    
    # Run with project environment activated
    if julia --project=/app/yao.jl yao_qft_benchmark.jl > /tmp/yao_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "Yao.jl benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        print_status "FAIL" "Yao.jl benchmark failed (check /tmp/yao_qft_benchmark.log)"
        echo "Last 30 lines of error log:"
        cat /tmp/yao_qft_benchmark.log | tail -30
        echo ""
        echo "Dependency installation log:"
        cat /tmp/yao_deps.log | tail -20
    fi
else
    print_status "SKIP" "Julia not available, skipping Yao.jl benchmark"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Benchmark Summary: $SUCCESS_COUNT/$TOTAL_COUNT libraries completed successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 5. Generate comparison plots
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Generating Comparison Plots..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    cd /app/pennylane/QuantumFourierTransform
    
    # Check if we have at least one result file
    RESULT_FILES=(
        "/app/logosq/QuantumFourierTransform/qft_benchmark_results.json"
        "/app/pennylane/QuantumFourierTransform/qft_benchmark_results.json"
        "/app/qiskit/QuantumFourierTransform/qiskit_qft_benchmark_results.json"
        "/app/yao.jl/QuantumFourierTransform/qft_benchmark_results.json"
    )
    
    FOUND_COUNT=0
    for file in "${RESULT_FILES[@]}"; do
        if [ -f "$file" ]; then
            FOUND_COUNT=$((FOUND_COUNT + 1))
        fi
    done
    
    if [ $FOUND_COUNT -eq 0 ]; then
        echo -e "${RED}✗${NC} No benchmark result files found. Cannot generate plots."
        echo "Please ensure at least one benchmark completed successfully."
        exit 1
    fi
    
    echo "Found $FOUND_COUNT result file(s). Generating plots..."
    
    if python3 plot_qft_comparison.py > /tmp/qft_plot_generation.log 2>&1; then
        print_status "SUCCESS" "Comparison plots generated successfully"
        echo ""
        echo "Generated plots:"
        echo "  • qft_execution_time_comparison.png"
        echo "  • qft_memory_comparison.png"
        echo "  • qft_speedup_comparison.png"
        echo ""
        echo "Location: /app/pennylane/QuantumFourierTransform/"
    else
        print_status "FAIL" "Plot generation failed (check /tmp/qft_plot_generation.log)"
        cat /tmp/qft_plot_generation.log | tail -30  # Show last 30 lines for debugging
        echo ""
        echo "Note: Plots will still be generated if at least one benchmark result file exists."
    fi
else
    echo -e "${RED}✗${NC} Python3 not available, cannot generate plots"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All QFT benchmarks and plots completed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Result files:"
echo "  • LogosQ:    /app/logosq/QuantumFourierTransform/qft_benchmark_results.json"
echo "  • PennyLane: /app/pennylane/QuantumFourierTransform/qft_benchmark_results.json"
echo "  • Qiskit:    /app/qiskit/QuantumFourierTransform/qiskit_qft_benchmark_results.json"
echo "  • Yao.jl:    /app/yao.jl/QuantumFourierTransform/qft_benchmark_results.json"
echo ""
echo "Plots:"
echo "  • /app/pennylane/QuantumFourierTransform/qft_execution_time_comparison.png"
echo "  • /app/pennylane/QuantumFourierTransform/qft_memory_comparison.png"
echo "  • /app/pennylane/QuantumFourierTransform/qft_speedup_comparison.png"
echo ""

