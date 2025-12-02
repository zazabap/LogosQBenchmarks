#!/bin/bash
# Parameter sweep benchmark: VQE performance vs number of parameters
# Usage: ./run_vqa_parameter_sweep.sh [start_params] [end_params] [step]
#   start_params: Starting parameter count (default: 12, corresponds to 3 layers for 4 qubits)
#   end_params: Ending parameter count (default: 28, corresponds to 7 layers for 4 qubits)
#   step: Step size between parameter counts (default: 4)
# Example: ./run_vqa_parameter_sweep.sh 12 40 4  # Runs for 12, 16, 20, 24, 28, 32, 36, 40 params

set -e

# Ensure PATH includes common tool locations
export PATH="${HOME}/.cargo/bin:${PATH}"
export PATH="/opt/julia/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_BASE_DIR="/app/test_results/vqa_parameter_sweep"
OUTPUT_DIR="${RESULTS_BASE_DIR}/individual"
mkdir -p "$RESULTS_BASE_DIR" "$OUTPUT_DIR"

# Parse command-line arguments for parameter range
START_PARAMS=${1:-12}
END_PARAMS=${2:-28}
STEP=${3:-4}

# Validate arguments
if ! [[ "$START_PARAMS" =~ ^[0-9]+$ ]] || ! [[ "$END_PARAMS" =~ ^[0-9]+$ ]] || ! [[ "$STEP" =~ ^[0-9]+$ ]]; then
    echo "Error: All arguments must be positive integers"
    echo "Usage: $0 [start_params] [end_params] [step]"
    echo "  start_params: Starting parameter count (default: 12)"
    echo "  end_params: Ending parameter count (default: 28)"
    echo "  step: Step size between parameter counts (default: 4)"
    exit 1
fi

if [ "$START_PARAMS" -le 0 ] || [ "$END_PARAMS" -lt "$START_PARAMS" ] || [ "$STEP" -le 0 ]; then
    echo "Error: Invalid parameter range. Ensure: start > 0, end >= start, step > 0"
    exit 1
fi

# Number of qubits (fixed for H2 molecule benchmark)
NUM_QUBITS=4

# Generate parameter counts and corresponding layers
PARAM_COUNTS=()
LAYERS=()
for ((params=START_PARAMS; params<=END_PARAMS; params+=STEP)); do
    # Calculate layers: layers = params / num_qubits
    layers=$((params / NUM_QUBITS))
    # Only add if layers is a valid integer (params must be divisible by num_qubits)
    if [ $((params % NUM_QUBITS)) -eq 0 ]; then
        PARAM_COUNTS+=($params)
        LAYERS+=($layers)
    else
        echo "Warning: Skipping $params parameters (not divisible by $NUM_QUBITS qubits)"
    fi
done

if [ ${#PARAM_COUNTS[@]} -eq 0 ]; then
    echo "Error: No valid parameter counts generated. Ensure parameters are multiples of $NUM_QUBITS."
    exit 1
fi

FRAMEWORKS=("logosq" "qiskit" "pennylane" "yao" "qsharp")

echo "=========================================="
echo "VQE Parameter Sweep Benchmark"
echo "=========================================="
echo "Parameter range: $START_PARAMS to $END_PARAMS (step: $STEP)"
echo "Testing parameter counts: ${PARAM_COUNTS[*]}"
echo "Corresponding layers: ${LAYERS[*]}"
echo "Number of qubits: $NUM_QUBITS"
echo "=========================================="
echo ""

for framework in "${FRAMEWORKS[@]}"; do
    echo "Running $framework parameter sweep..."
    
    for i in "${!PARAM_COUNTS[@]}"; do
        param_count="${PARAM_COUNTS[$i]}"
        layers="${LAYERS[$i]}"
        
        echo "  - Testing $param_count parameters ($layers layers)..."
        
        output_file="${OUTPUT_DIR}/${framework}_${param_count}params.json"
        
        case $framework in
            logosq)
                # Check for cargo in multiple ways
                CARGO_CMD=""
                if command -v cargo &> /dev/null; then
                    CARGO_CMD="cargo"
                elif [ -f "${HOME}/.cargo/bin/cargo" ]; then
                    CARGO_CMD="${HOME}/.cargo/bin/cargo"
                elif [ -f "/root/.cargo/bin/cargo" ]; then
                    CARGO_CMD="/root/.cargo/bin/cargo"
                fi
                
                if [ -z "$CARGO_CMD" ]; then
                    echo "    ✗ Cargo not found, skipping LogosQ"
                    continue
                fi
                
                # Use release build for faster execution
                # Redirect stderr to a temp file to capture errors
                error_log="/tmp/logosq_vqa_${param_count}params_error.log"
                if cd "${REPO_ROOT}/logosq" && VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" "$CARGO_CMD" run --example vqa --release > "$error_log" 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                        cat "$error_log" | tail -5
                    fi
                else
                    echo "    ✗ Failed"
                    cat "$error_log" | tail -10
                fi
                ;;
            qiskit)
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" python3 "${REPO_ROOT}/qiskit/VQA/vqa.py" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            pennylane)
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" python3 "${REPO_ROOT}/pennylane/VQA/vqa.py" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            yao)
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" julia "${REPO_ROOT}/yao.jl/VQA/vqa.jl" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            qsharp)
                # Check for dotnet and fix path issues if needed
                if ! command -v dotnet &> /dev/null; then
                    echo "    ✗ Dotnet not available, skipping Q#"
                    continue
                fi
                
                # Fix path issues: some .NET components may be installed in /usr/lib/dotnet instead of /usr/share/dotnet
                if [ -d /usr/lib/dotnet/host ] && [ ! -d /usr/share/dotnet/host ]; then
                    ln -sf /usr/lib/dotnet/host /usr/share/dotnet/host 2>/dev/null || true
                fi
                if [ -d /usr/lib/dotnet/shared ] && [ ! -d /usr/share/dotnet/shared ]; then
                    ln -sf /usr/lib/dotnet/shared /usr/share/dotnet/shared 2>/dev/null || true
                fi
                
                QSHARP_PROJECT="${REPO_ROOT}/qsharp/VQA/VQA.csproj"
                
                # Redirect stderr to a temp file to capture errors
                error_log="/tmp/qsharp_vqa_${param_count}params_error.log"
                if cd "${REPO_ROOT}/qsharp/VQA" && VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" dotnet run --project "$QSHARP_PROJECT" --configuration Release > "$error_log" 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                        cat "$error_log" | tail -5
                    fi
                else
                    echo "    ✗ Failed"
                    cat "$error_log" | tail -10
                fi
                ;;
        esac
    done
    echo ""
done

# Combine all results into a single JSON file
echo "Combining results..."
combined_file="${RESULTS_BASE_DIR}/vqa_parameter_sweep_results.json"

# Convert bash array to Python list format
PARAM_COUNTS_STR=$(IFS=','; echo "${PARAM_COUNTS[*]}")

python3 << PYTHON_SCRIPT
import json
import sys
import os

script_dir = "${SCRIPT_DIR}"
output_dir = "${OUTPUT_DIR}"

frameworks = ["logosq", "qiskit", "pennylane", "yao", "qsharp"]
param_counts = [${PARAM_COUNTS_STR}]

results = []
for framework in frameworks:
    for param_count in param_counts:
        result_file = os.path.join(output_dir, f"{framework}_{param_count}params.json")
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {result_file}: {e}", file=sys.stderr)

if not results:
    print("No parameter sweep results found.", file=sys.stderr)
    sys.exit(1)

output_file = "${combined_file}"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Combined {len(results)} results into {output_file}")
PYTHON_SCRIPT

echo "✓ Parameter sweep complete!"
echo "Results saved to: $combined_file"
echo "Individual results in: $OUTPUT_DIR"

