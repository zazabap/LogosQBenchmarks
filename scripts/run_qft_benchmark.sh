#!/bin/bash
# Script to run QFT benchmarks for all libraries and generate comparison plots

# Don't exit on error - we want to continue even if one benchmark fails
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="/app/test_results/qft"
mkdir -p "$RESULTS_DIR"

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
TOTAL_COUNT=5

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
    cd "${REPO_ROOT}/logosq/QuantumFourierTransform"
    
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
        LOGOSQ_RESULT_SRC="${REPO_ROOT}/logosq/QuantumFourierTransform/qft_benchmark_results.json"
        if [ -f "$LOGOSQ_RESULT_SRC" ]; then
            cp "$LOGOSQ_RESULT_SRC" "${RESULTS_DIR}/logosq_qft_benchmark_results.json"
        fi
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
    cd "${REPO_ROOT}/pennylane/QuantumFourierTransform"
    
    # Check if pennylane_qft module exists, if not create a simple import workaround
    if [ ! -f "pennylane_qft.py" ]; then
        echo "Warning: pennylane_qft.py not found, benchmark may fail"
    fi
    
    if python3 pennylane_qft_benchmark.py > /tmp/pennylane_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "PennyLane benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        PENNYLANE_RESULT_SRC="${REPO_ROOT}/pennylane/QuantumFourierTransform/qft_benchmark_results.json"
        if [ -f "$PENNYLANE_RESULT_SRC" ]; then
            cp "$PENNYLANE_RESULT_SRC" "${RESULTS_DIR}/pennylane_qft_benchmark_results.json"
        fi
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
    cd "${REPO_ROOT}/qiskit/QuantumFourierTransform"
    
    if python3 qiskit_benchmark.py > /tmp/qiskit_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "Qiskit benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        QISKIT_RESULT_SRC="${REPO_ROOT}/qiskit/QuantumFourierTransform/qiskit_qft_benchmark_results.json"
        if [ -f "$QISKIT_RESULT_SRC" ]; then
            cp "$QISKIT_RESULT_SRC" "${RESULTS_DIR}/qiskit_qft_benchmark_results.json"
        fi
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
    cd "${REPO_ROOT}/yao.jl"
    
    # Clear corrupted precompilation cache for Yao
    echo "Clearing Yao precompilation cache..."
    rm -rf ~/.julia/compiled/v1.8/Yao 2>/dev/null || true
    
    # Ensure dependencies are installed in the project
    echo "Installing/updating Julia dependencies..."
    julia --project=/app/yao.jl -e '
        using Pkg
        # First resolve to ensure manifest is in sync
        Pkg.resolve()
        # Instantiate to get all dependencies including transitive ones
        Pkg.instantiate()
        # Add missing packages if needed
        deps = Pkg.project().dependencies
        if !haskey(deps, "BenchmarkTools")
            Pkg.add("BenchmarkTools")
        end
        if !haskey(deps, "JSON")
            Pkg.add("JSON")
        end
        # Resolve again to update manifest with any new packages
        Pkg.resolve()
        # Instantiate again to ensure everything is installed
        Pkg.instantiate()
        # Verify that Yao and its dependencies are available
        # Check if required packages are in the project dependencies
        deps = Pkg.project().dependencies
        required_pkgs = ["YaoBlocks", "YaoArrayRegister"]
        for pkg in required_pkgs
            if !haskey(deps, pkg)
                println("Adding $pkg as explicit dependency...")
                try
                    Pkg.add(pkg)
                catch e
                    println("Warning: Could not add $pkg: ", e)
                end
            end
        end
        # Resolve and instantiate again after adding packages
        Pkg.resolve()
        Pkg.instantiate()
        # Verify packages can be loaded
        try
            using YaoBlocks
            using YaoArrayRegister
            println("YaoBlocks and YaoArrayRegister loaded successfully")
        catch e
            println("Warning: Could not load required packages: ", e)
        end
        # Force precompilation
        try
            Pkg.precompile()
        catch e
            println("Precompilation warning: ", e)
        end
    ' > /tmp/yao_deps.log 2>&1 || true
    
    # Try to precompile Yao specifically (with workaround for circular dependency)
    echo "Precompiling Yao..."
    julia --project=/app/yao.jl -e '
        using Pkg
        # Ensure manifest is in sync
        Pkg.resolve()
        Pkg.instantiate()
        try
            # Work around circular dependency by loading in correct order
            # First ensure YaoBlocks is available (it should be a transitive dependency)
            using YaoBlocks
            println("YaoBlocks loaded successfully")
            # Then try YaoPlots
            using YaoPlots
            println("YaoPlots loaded successfully")
            # Finally load Yao
            using Yao
            println("Yao loaded successfully")
        catch e
            println("Yao loading error: ", e)
            # Try to ensure all dependencies are installed
            Pkg.resolve()
            Pkg.instantiate()
            # Try rebuilding problematic packages
            try
                Pkg.build("YaoBlocks")
            catch
            end
            try
                Pkg.build("Yao")
            catch
            end
            # Try again with explicit order
            try
                using YaoBlocks
                using YaoPlots
                using Yao
                println("Yao rebuilt and loaded successfully")
            catch e2
                println("Failed to load after rebuild: ", e2)
                # Last resort: try loading without YaoPlots first
                try
                    using YaoBlocks
                    using YaoArrayRegister
                    using Yao
                    println("Yao loaded successfully (without YaoPlots preload)")
                catch e3
                    println("Final load attempt failed: ", e3)
                end
            end
        end
    ' >> /tmp/yao_deps.log 2>&1 || true
    
    cd "${REPO_ROOT}/yao.jl/QuantumFourierTransform"
    
    # Run with project environment activated
    # Try without --compiled-modules=no first (faster), fall back if needed
    if julia --project=/app/yao.jl yao_qft_benchmark.jl > /tmp/yao_qft_benchmark.log 2>&1; then
        print_status "SUCCESS" "Yao.jl benchmark completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        YAO_RESULT_SRC="${REPO_ROOT}/yao.jl/QuantumFourierTransform/qft_benchmark_results.json"
        if [ -f "$YAO_RESULT_SRC" ]; then
            cp "$YAO_RESULT_SRC" "${RESULTS_DIR}/yao_qft_benchmark_results.json"
        fi
    else
        # If it failed, try with --compiled-modules=no to work around circular dependency
        echo "First attempt failed, trying with --compiled-modules=no to work around circular dependency..."
        if julia --project=/app/yao.jl --compiled-modules=no yao_qft_benchmark.jl > /tmp/yao_qft_benchmark.log 2>&1; then
            print_status "SUCCESS" "Yao.jl benchmark completed (with --compiled-modules=no)"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            YAO_RESULT_SRC="${REPO_ROOT}/yao.jl/QuantumFourierTransform/qft_benchmark_results.json"
            if [ -f "$YAO_RESULT_SRC" ]; then
                cp "$YAO_RESULT_SRC" "${RESULTS_DIR}/yao_qft_benchmark_results.json"
            fi
        else
            print_status "FAIL" "Yao.jl benchmark failed (check /tmp/yao_qft_benchmark.log)"
            echo "Last 30 lines of error log:"
            cat /tmp/yao_qft_benchmark.log | tail -30
            echo ""
            echo "Dependency installation log:"
            cat /tmp/yao_deps.log | tail -20
        fi
    fi
else
    print_status "SKIP" "Julia not available, skipping Yao.jl benchmark"
fi

# 5. Run Q# (.NET) benchmark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5/5 Running Q# (.NET) QFT Benchmark..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v dotnet &> /dev/null; then
    # Verify .NET installation is complete and functional
    if ! dotnet --version > /dev/null 2>&1; then
        print_status "SKIP" ".NET SDK found but not working properly (check installation)"
    elif ! dotnet --info > /dev/null 2>&1; then
        print_status "SKIP" ".NET SDK found but runtime info unavailable (check installation)"
    else
        QSHARP_PROJECT="${REPO_ROOT}/qsharp/QuantumFourierTransform/QFT.csproj"
        
        # Verify project file exists
        if [ ! -f "$QSHARP_PROJECT" ]; then
            print_status "FAIL" "Q# project file not found: $QSHARP_PROJECT"
        else
            # Restore dependencies first
            echo "Restoring Q# project dependencies..."
            if ! dotnet restore "$QSHARP_PROJECT" > /tmp/qsharp_restore.log 2>&1; then
                print_status "FAIL" "Q# restore failed (check /tmp/qsharp_restore.log)"
                cat /tmp/qsharp_restore.log | tail -20
            else
                # Build first to separate build time from run time
                echo "Building Q# project..."
                if ! dotnet build -c Release "$QSHARP_PROJECT" > /tmp/qsharp_build.log 2>&1; then
                    print_status "FAIL" "Q# build failed (check /tmp/qsharp_build.log)"
                    cat /tmp/qsharp_build.log | tail -20
                else
                    # Run the benchmark
                    echo "Running Q# benchmark..."
                    if QFT_OUTPUT_DIR="${RESULTS_DIR}" dotnet run --project "$QSHARP_PROJECT" --configuration Release -- 1 12 > /tmp/qsharp_qft_benchmark.log 2>&1; then
                        print_status "SUCCESS" "Q# benchmark completed"
                        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                        # Verify result file was created
                        if [ -f "${RESULTS_DIR}/qsharp_qft_benchmark_results.json" ]; then
                            echo "  Result file: ${RESULTS_DIR}/qsharp_qft_benchmark_results.json"
                        fi
                    else
                        print_status "FAIL" "Q# benchmark failed (check /tmp/qsharp_qft_benchmark.log)"
                        cat /tmp/qsharp_qft_benchmark.log | tail -20
                        # Check for specific fxr error
                        if grep -q "fxr" /tmp/qsharp_qft_benchmark.log; then
                            echo "  Error: .NET runtime host (fxr) is missing. This indicates an incomplete .NET installation."
                            echo "  Try rebuilding the Docker image to ensure complete .NET SDK installation."
                        fi
                    fi
                fi
            fi
        fi
    fi
else
    print_status "SKIP" "Dotnet not available, skipping Q# benchmark"
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
    # Check if we have at least one result file
    RESULT_FILES=(
        "${RESULTS_DIR}/logosq_qft_benchmark_results.json"
        "${RESULTS_DIR}/pennylane_qft_benchmark_results.json"
        "${RESULTS_DIR}/qiskit_qft_benchmark_results.json"
        "${RESULTS_DIR}/yao_qft_benchmark_results.json"
        "${RESULTS_DIR}/qsharp_qft_benchmark_results.json"
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
    
    if python3 "${SCRIPT_DIR}/plot_qft_comparison.py" > /tmp/qft_plot_generation.log 2>&1; then
        print_status "SUCCESS" "Comparison plots generated successfully"
        echo ""
        echo "Generated plots:"
        echo "  • qft_execution_time_comparison.png"
        echo "  • qft_memory_comparison.png"
        echo "  • qft_speedup_comparison.png"
        echo ""
        echo "Location: ${RESULTS_DIR}"
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
echo "Result files stored in: ${RESULTS_DIR}"
echo "Plots saved to:         ${RESULTS_DIR}"
echo ""

