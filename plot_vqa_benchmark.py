"""
Plot comparison between LogosQ (Rust), PennyLane (Python), Qiskit (Python), and Yao.jl (Julia) VQE benchmarks.
Generates plots for energy error, runtime, and iterations comparing all available libraries.
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
}

FRAMEWORK_MARKERS = {
    'LogosQ (Rust)': 'o',
    'Qiskit (Python)': 's',
    'PennyLane (Python)': '^',
    'Yao.jl (Julia)': 'D',
}


def load_results(json_path: Path) -> List[Dict]:
    """Load benchmark results from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_energy_comparison(results: List[Dict], output_dir: Path):
    """Plot energy error comparison."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    frameworks = [r['framework'] for r in results]
    energies = [r['vqe_energy'] for r in results]
    exact_energy = results[0]['exact_energy']  # All should have same exact energy
    energy_errors = [r['energy_error'] for r in results]

    # Plot 1: VQE Energy vs Exact Energy
    x_pos = np.arange(len(frameworks))
    colors = [FRAMEWORK_COLORS.get(f, '#666666') for f in frameworks]
    
    bars1 = ax1.bar(x_pos, energies, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=exact_energy, color='red', linestyle='--', linewidth=2, label=f'Exact Energy ({exact_energy:.6f} Ha)')
    ax1.set_xlabel('Framework', fontweight='bold')
    ax1.set_ylabel('Energy (Ha)', fontweight='bold')
    ax1.set_title('VQE Ground State Energy', fontweight='bold', fontsize=15)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(frameworks, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for i, (bar, energy) in enumerate(zip(bars1, energies)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{energy:.6f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 2: Energy Error (log scale)
    bars2 = ax2.bar(x_pos, energy_errors, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_xlabel('Framework', fontweight='bold')
    ax2.set_ylabel('Energy Error |E - E_exact| (Ha)', fontweight='bold')
    ax2.set_title('Energy Error (Lower is Better)', fontweight='bold', fontsize=15)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(frameworks, rotation=15, ha='right')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, linestyle='--', which='both')
    
    # Add value labels on bars
    for i, (bar, error) in enumerate(zip(bars2, energy_errors)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{error:.2e}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / 'vqa_energy_comparison.png'
    plt.savefig(output_path)
    print(f"Saved energy comparison plot to: {output_path}")
    plt.close()


def plot_runtime_comparison(results: List[Dict], output_dir: Path):
    """Plot runtime comparison."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    frameworks = [r['framework'] for r in results]
    runtimes = [r['runtime_ms'] for r in results]
    x_pos = np.arange(len(frameworks))
    colors = [FRAMEWORK_COLORS.get(f, '#666666') for f in frameworks]

    bars = ax.bar(x_pos, runtimes, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_xlabel('Framework', fontweight='bold')
    ax.set_ylabel('Runtime (ms)', fontweight='bold')
    ax.set_title('VQE Runtime Comparison (Lower is Better)', fontweight='bold', fontsize=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(frameworks, rotation=15, ha='right')
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # Add value labels on bars
    for bar, runtime in zip(bars, runtimes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{runtime:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / 'vqa_runtime_comparison.png'
    plt.savefig(output_path)
    print(f"Saved runtime comparison plot to: {output_path}")
    plt.close()


def plot_iterations_comparison(results: List[Dict], output_dir: Path):
    """Plot iterations comparison."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    frameworks = [r['framework'] for r in results]
    iterations = [r['iterations'] for r in results]
    x_pos = np.arange(len(frameworks))
    colors = [FRAMEWORK_COLORS.get(f, '#666666') for f in frameworks]

    bars = ax.bar(x_pos, iterations, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_xlabel('Framework', fontweight='bold')
    ax.set_ylabel('Number of Iterations', fontweight='bold')
    ax.set_title('VQE Convergence Iterations', fontweight='bold', fontsize=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(frameworks, rotation=15, ha='right')
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # Add value labels on bars
    for bar, iters in zip(bars, iterations):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{iters}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / 'vqa_iterations_comparison.png'
    plt.savefig(output_path)
    print(f"Saved iterations comparison plot to: {output_path}")
    plt.close()


def plot_comprehensive_comparison(results: List[Dict], output_dir: Path):
    """Create a comprehensive comparison plot with all metrics."""
    fig = plt.figure(figsize=(18, 6))
    gs = fig.add_gridspec(1, 3, hspace=0.3, wspace=0.3)

    frameworks = [r['framework'] for r in results]
    x_pos = np.arange(len(frameworks))
    colors = [FRAMEWORK_COLORS.get(f, '#666666') for f in frameworks]

    # Energy Error
    ax1 = fig.add_subplot(gs[0, 0])
    energy_errors = [r['energy_error'] for r in results]
    bars1 = ax1.bar(x_pos, energy_errors, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Energy Error (Ha)', fontweight='bold')
    ax1.set_title('Energy Error', fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(frameworks, rotation=15, ha='right')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3, linestyle='--', which='both')
    for bar, error in zip(bars1, energy_errors):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{error:.2e}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Runtime
    ax2 = fig.add_subplot(gs[0, 1])
    runtimes = [r['runtime_ms'] for r in results]
    bars2 = ax2.bar(x_pos, runtimes, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Runtime (ms)', fontweight='bold')
    ax2.set_title('Runtime', fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(frameworks, rotation=15, ha='right')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    for bar, runtime in zip(bars2, runtimes):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{runtime:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Iterations
    ax3 = fig.add_subplot(gs[0, 2])
    iterations = [r['iterations'] for r in results]
    bars3 = ax3.bar(x_pos, iterations, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Iterations', fontweight='bold')
    ax3.set_title('Convergence Iterations', fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(frameworks, rotation=15, ha='right')
    ax3.grid(True, alpha=0.3, linestyle='--', axis='y')
    for bar, iters in zip(bars3, iterations):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{iters}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    fig.suptitle('H₂ VQE Cross-Framework Benchmark Comparison', fontsize=18, fontweight='bold', y=1.02)
    plt.savefig(output_dir / 'vqa_comprehensive_comparison.png', bbox_inches='tight')
    print(f"Saved comprehensive comparison plot to: {output_dir / 'vqa_comprehensive_comparison.png'}")
    plt.close()


def main():
    script_dir = Path(__file__).parent
    json_path = script_dir / 'vqa_benchmark_results.json'
    output_dir = script_dir

    if not json_path.exists():
        print(f"Error: Results file not found: {json_path}")
        print("Please run ./run_vqa_benchmark.sh first to generate benchmark results.")
        return

    print("Loading benchmark results...")
    results = load_results(json_path)

    print(f"Found {len(results)} benchmark results:")
    for r in results:
        print(f"  - {r['framework']}: Energy={r['vqe_energy']:.6f} Ha, Runtime={r['runtime_ms']:.2f} ms, Iterations={r['iterations']}")

    print("\nGenerating plots...")
    plot_energy_comparison(results, output_dir)
    plot_runtime_comparison(results, output_dir)
    plot_iterations_comparison(results, output_dir)
    plot_comprehensive_comparison(results, output_dir)

    print("\nAll plots generated successfully!")


if __name__ == "__main__":
    main()

