#!/bin/bash
# Cross-framework VQE benchmark runner for H₂ molecule
# Runs benchmarks for LogosQ (Rust), Qiskit (Python), PennyLane (Python), and Yao.jl (Julia)
# Outputs JSON results to vqa_benchmark_results.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${SCRIPT_DIR}/vqa_benchmark_results.json"
RESULTS_DIR="${SCRIPT_DIR}/test_results"
mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "H₂ VQE Cross-Framework Benchmark Suite"
echo "=========================================="
echo ""

# Run LogosQ (Rust)
echo "[1/4] Running LogosQ (Rust) benchmark..."
logosq_json="${RESULTS_DIR}/logosq_vqa_result.json"
if cd "${SCRIPT_DIR}/logosq" && VQA_OUTPUT_FILE="$logosq_json" cargo run --example vqa > /dev/null 2>&1; then
    if [ -f "$logosq_json" ]; then
        echo "✓ LogosQ completed - JSON saved to $logosq_json"
    else
        echo "✗ LogosQ: JSON file not found"
        exit 1
    fi
else
    echo "✗ LogosQ failed"
    exit 1
fi
echo ""

# Run Qiskit (Python)
echo "[2/4] Running Qiskit (Python) benchmark..."
qiskit_json="${RESULTS_DIR}/qiskit_vqa_result.json"
if VQA_OUTPUT_FILE="$qiskit_json" python3 "${SCRIPT_DIR}/qiskit/VQA/vqa.py" > /dev/null 2>&1; then
    if [ -f "$qiskit_json" ]; then
        echo "✓ Qiskit completed - JSON saved to $qiskit_json"
    else
        echo "✗ Qiskit: JSON file not found"
        exit 1
    fi
else
    echo "✗ Qiskit failed"
    exit 1
fi
echo ""

# Run PennyLane (Python)
echo "[3/4] Running PennyLane (Python) benchmark..."
pennylane_json="${RESULTS_DIR}/pennylane_vqa_result.json"
if VQA_OUTPUT_FILE="$pennylane_json" python3 "${SCRIPT_DIR}/pennylane/VQA/vqa.py" > /dev/null 2>&1; then
    if [ -f "$pennylane_json" ]; then
        echo "✓ PennyLane completed - JSON saved to $pennylane_json"
    else
        echo "✗ PennyLane: JSON file not found"
        exit 1
    fi
else
    echo "✗ PennyLane failed"
    exit 1
fi
echo ""

# Run Yao.jl (Julia)
echo "[4/4] Running Yao.jl (Julia) benchmark..."
yao_json="${RESULTS_DIR}/yao_vqa_result.json"
if VQA_OUTPUT_FILE="$yao_json" julia "${SCRIPT_DIR}/yao.jl/VQA/vqa.jl" > /dev/null 2>&1; then
    if [ -f "$yao_json" ]; then
        echo "✓ Yao.jl completed - JSON saved to $yao_json"
    else
        echo "✗ Yao.jl: JSON file not found"
        exit 1
    fi
else
    echo "✗ Yao.jl failed"
    exit 1
fi
echo ""

# Combine all JSON files into a single array
echo "Combining results..."
python3 << EOF
import json
import sys
from pathlib import Path

results = []
json_files = [
    "$logosq_json",
    "$qiskit_json",
    "$pennylane_json",
    "$yao_json",
]

for json_file in json_files:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            results.append(data)
    except Exception as e:
        print(f"Error reading {json_file}: {e}", file=sys.stderr)
        sys.exit(1)

# Write combined results
with open("$OUTPUT_FILE", 'w') as f:
    json.dump(results, f, indent=2)

print(f"✓ Combined {len(results)} results into $OUTPUT_FILE")
EOF

echo ""
echo "=========================================="
echo "Benchmark complete!"
echo "Results saved to: $OUTPUT_FILE"
echo "=========================================="
echo ""
echo "To visualize results, run:"
echo "  python3 ${SCRIPT_DIR}/plot_vqa_benchmark.py"
