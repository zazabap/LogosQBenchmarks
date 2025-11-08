#!/bin/bash
# Script to run all gradient bug tests and collect results

set -e

RESULTS_DIR="/app/test_results"
mkdir -p "$RESULTS_DIR"

echo "Running gradient bug tests for all libraries..."
echo "================================================"

# Function to extract test results
extract_result() {
    local file=$1
    local bug_name=$2
    local library=$3
    
    if [ ! -f "$file" ]; then
        echo "ERROR: Test file not found or test failed"
        return
    fi
    
    # Check for different result patterns
    if grep -q "FAILED\|Empty gradient\|NaN detected" "$file"; then
        echo "FAIL"
    elif grep -q "PASSED\|✓.*OK\|Gradients match" "$file"; then
        echo "PASS"
    elif grep -q "WARNING\|⚠" "$file"; then
        echo "WARN"
    else
        echo "UNKNOWN"
    fi
}

# Run PennyLane tests
echo "Running PennyLane tests..."
if command -v python3 &> /dev/null; then
    cd /app/pennylane/MemoryCicuitDifferentiation
    python3 pennylane_gradient_bugs.py > "$RESULTS_DIR/pennylane_results.txt" 2>&1 || true
    echo "PennyLane tests completed"
else
    echo "Python3 not available, skipping PennyLane tests"
    echo "ERROR: Python3 not available" > "$RESULTS_DIR/pennylane_results.txt"
fi

# Run Qiskit tests
echo "Running Qiskit tests..."
if command -v python3 &> /dev/null; then
    cd /app/qiskit/MemoryDifferentiation
    python3 qiskit_gradient_bugs.py > "$RESULTS_DIR/qiskit_results.txt" 2>&1 || true
    echo "Qiskit tests completed"
else
    echo "Python3 not available, skipping Qiskit tests"
    echo "ERROR: Python3 not available" > "$RESULTS_DIR/qiskit_results.txt"
fi

# Run Yao.jl tests
echo "Running Yao.jl tests..."
if command -v julia &> /dev/null; then
    cd /app/yao.jl/MemoryCircuitDifferentiation
    julia yao_gradient_bugs.jl > "$RESULTS_DIR/yao_results.txt" 2>&1 || true
    echo "Yao.jl tests completed"
else
    echo "Julia not available, skipping Yao.jl tests"
    echo "ERROR: Julia not available" > "$RESULTS_DIR/yao_results.txt"
fi

# Run LogosQ tests
echo "Running LogosQ tests..."
if command -v cargo &> /dev/null; then
    cd /app/logosq
    # Check if we need to add it as an example
    if ! grep -q "logosq_gradient_bugs" Cargo.toml; then
        # Add as example
        cat >> Cargo.toml << 'EOF'

[[example]]
name = "gradient_bugs"
path = "MemoryCircuitDifferentiation/logosq_gradient_bugs.rs"
EOF
    fi
    cargo run --example gradient_bugs > "$RESULTS_DIR/logosq_results.txt" 2>&1 || true
    echo "LogosQ tests completed"
else
    echo "Cargo not available, skipping LogosQ tests"
    echo "ERROR: Cargo not available" > "$RESULTS_DIR/logosq_results.txt"
fi

echo ""
echo "All tests completed. Results saved to $RESULTS_DIR/"
echo "================================================"
echo ""
echo "Updating gradient bug comparison table in dashboard..."
if command -v python3 &> /dev/null; then
    python3 /app/update_gradient_table.py
    echo "Dashboard updated successfully!"
else
    echo "Warning: Python3 not available, skipping dashboard update"
fi

