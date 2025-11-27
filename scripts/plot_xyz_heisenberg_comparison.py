"""
Plot comparison between LogosQ (Rust), PennyLane (Python), Qiskit (Python), and Yao.jl (Julia) 
XYZ Heisenberg Model benchmarks.
Generates plots for execution time, energy evolution, and scaling analysis comparing all available libraries.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List

# Configure matplotlib for high-quality plots
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans'],
    'axes.labelsize': 13,
    'axes.titlesize': 15,
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold',
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'legend.framealpha': 0.95,
    'legend.fancybox': True,
    'legend.shadow': True,
    'figure.titlesize': 16,
    'figure.titleweight': 'bold',
    'grid.alpha': 0.3,
    'grid.linewidth': 0.8,
    'lines.linewidth': 2.5,
    'lines.markersize': 10,
    'patch.linewidth': 1.5,
    'axes.linewidth': 1.2,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.axisbelow': True,
    'figure.facecolor': 'white',
    'axes.facecolor': '#FAFAFA',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Color scheme for frameworks
FRAMEWORK_COLORS = {
    'LogosQ (Rust)': '#E63946',
    'Qiskit (Python)': '#457B9D',
    'PennyLane (Python)': '#F77F00',
    'Yao.jl (Julia)': '#2A9D8F',
    'Q# (.NET)': '#884dff',
}

FRAMEWORK_MARKERS = {
    'LogosQ (Rust)': 'o',
    'Qiskit (Python)': 's',
    'PennyLane (Python)': '^',
    'Yao.jl (Julia)': 'D',
    'Q# (.NET)': 'X',
}

RESULTS_DIR = Path("/app/test_results/xyz_heisenberg")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_JSON = RESULTS_DIR / "xyz_heisenberg_results.json"


def load_results(json_path: Path) -> List[Dict]:
    """Load benchmark results from JSON file."""
    if not json_path.exists():
        print(f"Error: Results file not found: {json_path}")
        return []
    
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_runtime_comparison(results: List[Dict], output_dir: Path):
    """Plot runtime vs number of qubits for all frameworks."""
    # Group results by framework
    frameworks = {}
    for r in results:
        fw = r['framework']
        if fw not in frameworks:
            frameworks[fw] = []
        frameworks[fw].append(r)
    
    # Sort by qubit count for each framework
    for fw in frameworks:
        frameworks[fw].sort(key=lambda x: x['qubits'])
    
    plt.figure(figsize=(10, 6))
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        runtimes = [r['runtime_ms'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(qubits, runtimes, marker=marker, linewidth=2.5, markersize=10,
                label=fw, color=color, alpha=0.8)
    
    plt.xlabel('Number of Qubits', fontweight='bold')
    plt.ylabel('Runtime (ms)', fontweight='bold')
    plt.title('XYZ Heisenberg Model: Runtime vs Number of Qubits', fontweight='bold', fontsize=14)
    plt.yscale('log')
    plt.grid(True, alpha=0.3, linestyle='--', which='both')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks(range(4, 13))
    plt.tight_layout()
    output_path = output_dir / 'xyz_heisenberg_runtime_comparison.png'
    plt.savefig(output_path)
    print(f"Saved runtime comparison plot to: {output_path}")
    plt.close()


def plot_energy_evolution(results: List[Dict], output_dir: Path):
    """Plot energy evolution (initial, final, and change) vs number of qubits."""
    # Group results by framework
    frameworks = {}
    for r in results:
        fw = r['framework']
        if fw not in frameworks:
            frameworks[fw] = []
        frameworks[fw].append(r)
    
    # Sort by qubit count for each framework
    for fw in frameworks:
        frameworks[fw].sort(key=lambda x: x['qubits'])
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot 1: Initial Energy
    ax = axes[0]
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        energies = [r['initial_energy'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        ax.plot(qubits, energies, marker=marker, linewidth=2.5, markersize=8,
               label=fw, color=color, alpha=0.8)
    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Initial Energy', fontweight='bold')
    ax.set_title('Initial Energy vs Qubits', fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.95, fontsize=9)
    ax.set_xticks(range(4, 13))
    
    # Plot 2: Final Energy
    ax = axes[1]
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        energies = [r['final_energy'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        ax.plot(qubits, energies, marker=marker, linewidth=2.5, markersize=8,
               label=fw, color=color, alpha=0.8)
    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Final Energy', fontweight='bold')
    ax.set_title('Final Energy vs Qubits', fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.95, fontsize=9)
    ax.set_xticks(range(4, 13))
    
    # Plot 3: Energy Change
    ax = axes[2]
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        energy_changes = [r['energy_change'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        ax.plot(qubits, energy_changes, marker=marker, linewidth=2.5, markersize=8,
               label=fw, color=color, alpha=0.8)
    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Energy Change', fontweight='bold')
    ax.set_title('Energy Change vs Qubits', fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.legend(loc='best', framealpha=0.95, fontsize=9)
    ax.set_xticks(range(4, 13))
    
    plt.suptitle('XYZ Heisenberg Model: Energy Evolution', fontweight='bold', fontsize=16, y=1.02)
    plt.tight_layout()
    output_path = output_dir / 'xyz_heisenberg_energy_evolution.png'
    plt.savefig(output_path)
    print(f"Saved energy evolution plot to: {output_path}")
    plt.close()


def plot_scaling_analysis(results: List[Dict], output_dir: Path):
    """Plot scaling analysis showing exponential growth in runtime."""
    # Group results by framework
    frameworks = {}
    for r in results:
        fw = r['framework']
        if fw not in frameworks:
            frameworks[fw] = []
        frameworks[fw].append(r)
    
    # Sort by qubit count for each framework
    for fw in frameworks:
        frameworks[fw].sort(key=lambda x: x['qubits'])
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Runtime on linear scale
    ax = axes[0]
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        runtimes = [r['runtime_ms'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        ax.plot(qubits, runtimes, marker=marker, linewidth=2.5, markersize=10,
               label=fw, color=color, alpha=0.8)
    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Runtime (ms)', fontweight='bold')
    ax.set_title('Runtime Scaling (Linear Scale)', fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.95)
    ax.set_xticks(range(4, 13))
    
    # Plot 2: Runtime on log scale with theoretical exponential
    ax = axes[1]
    for fw, fw_results in frameworks.items():
        qubits = np.array([r['qubits'] for r in fw_results])
        runtimes = np.array([r['runtime_ms'] for r in fw_results])
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        ax.plot(qubits, runtimes, marker=marker, linewidth=2.5, markersize=10,
               label=fw, color=color, alpha=0.8)
        
        # Fit exponential: runtime = a * 2^(b * qubits)
        if len(qubits) >= 3:
            # Use log-linear fit: log(runtime) = log(a) + b * qubits
            log_runtimes = np.log(runtimes + 1e-10)  # Add small value to avoid log(0)
            coeffs = np.polyfit(qubits, log_runtimes, 1)
            fit_runtimes = np.exp(coeffs[0] * qubits + coeffs[1])
            ax.plot(qubits, fit_runtimes, '--', color=color, alpha=0.5, linewidth=1.5,
                   label=f'{fw} (exp fit)')
    
    # Theoretical exponential reference: 2^n scaling
    qubits_ref = np.array(range(4, 13))
    # Normalize to first data point for visualization
    if results:
        first_runtime = min([r['runtime_ms'] for r in results if r['qubits'] == 4])
        theoretical = first_runtime * (2.0 ** (qubits_ref - 4))
        ax.plot(qubits_ref, theoretical, 'k--', linewidth=2, alpha=0.6,
               label='Theoretical 2^n scaling', linestyle=':')
    
    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Runtime (ms)', fontweight='bold')
    ax.set_title('Runtime Scaling (Log Scale)', fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, linestyle='--', which='both')
    ax.legend(loc='best', framealpha=0.95, fontsize=9)
    ax.set_xticks(range(4, 13))
    
    plt.suptitle('XYZ Heisenberg Model: Scaling Analysis', fontweight='bold', fontsize=16, y=1.02)
    plt.tight_layout()
    output_path = output_dir / 'xyz_heisenberg_scaling_analysis.png'
    plt.savefig(output_path)
    print(f"Saved scaling analysis plot to: {output_path}")
    plt.close()


def plot_operations_comparison(results: List[Dict], output_dir: Path):
    """Plot number of operations vs qubits."""
    # Group results by framework
    frameworks = {}
    for r in results:
        fw = r['framework']
        if fw not in frameworks:
            frameworks[fw] = []
        frameworks[fw].append(r)
    
    # Sort by qubit count for each framework
    for fw in frameworks:
        frameworks[fw].sort(key=lambda x: x['qubits'])
    
    plt.figure(figsize=(10, 6))
    for fw, fw_results in frameworks.items():
        qubits = [r['qubits'] for r in fw_results]
        operations = [r['num_operations'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(qubits, operations, marker=marker, linewidth=2.5, markersize=10,
                label=fw, color=color, alpha=0.8)
    
    plt.xlabel('Number of Qubits', fontweight='bold')
    plt.ylabel('Number of Operations', fontweight='bold')
    plt.title('XYZ Heisenberg Model: Circuit Operations vs Number of Qubits', fontweight='bold', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks(range(4, 13))
    plt.tight_layout()
    output_path = output_dir / 'xyz_heisenberg_operations_comparison.png'
    plt.savefig(output_path)
    print(f"Saved operations comparison plot to: {output_path}")
    plt.close()


def main():
    """Main entry point for plotting."""
    output_dir = RESULTS_DIR

    if not RESULTS_JSON.exists():
        print(f"Error: XYZ Heisenberg results not found: {RESULTS_JSON}")
        print("Please run ./run_xyz_heisenberg_benchmark.sh first to generate results.")
        return

    print("Loading XYZ Heisenberg benchmark results...")
    results = load_results(RESULTS_JSON)

    if not results:
        print("No XYZ Heisenberg benchmark entries found in the results file.")
        return

    print(f"Found {len(results)} benchmark entries:")
    frameworks_seen = set()
    for r in results:
        fw = r['framework']
        if fw not in frameworks_seen:
            print(f"  - {fw}: {r['qubits']} qubits, runtime={r['runtime_ms']:.2f} ms")
            frameworks_seen.add(fw)

    print("\nGenerating comparison plots...")
    
    # Generate all plots
    plot_runtime_comparison(results, output_dir)
    plot_energy_evolution(results, output_dir)
    plot_scaling_analysis(results, output_dir)
    plot_operations_comparison(results, output_dir)

    print("\n✓ All XYZ Heisenberg comparison plots generated successfully!")
    print(f"Plots saved to: {output_dir}")


if __name__ == "__main__":
    main()

