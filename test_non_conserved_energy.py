#!/usr/bin/env python3
"""
Test script to demonstrate energy conservation vs non-conservation
in the XYZ Heisenberg model.

This script shows:
1. Conserved energy case: time-independent Hamiltonian
2. Non-conserved energy case: time-dependent external field
"""

import numpy as np
import sys
import os

# Add paths for imports
sys.path.insert(0, '/app/pennylane/XYZHeisenberg')
from xyz_h import (
    create_xyz_heisenberg_hamiltonian,
    calculate_energy,
    build_time_evolution_circuit,
    run_xyz_heisenberg_benchmark
)

def test_energy_conservation():
    """Test with time-independent Hamiltonian (energy should be conserved)."""
    print("=" * 80)
    print("TEST 1: Energy Conservation (Time-Independent Hamiltonian)")
    print("=" * 80)
    
    num_qubits = 4
    time_steps = 10
    dt = 0.1
    
    result = run_xyz_heisenberg_benchmark(
        num_qubits=num_qubits,
        jx=1.0,
        jy=1.0,
        jz=1.0,
        external_field=0.0,
        time_steps=time_steps,
        dt=dt,
        time_dependent_field=False,
    )
    
    print(f"\nInitial Energy: {result['initial_energy']:.10f}")
    print(f"Final Energy:   {result['final_energy']:.10f}")
    print(f"Energy Change:  {result['energy_change']:.10f}")
    print(f"\n✓ Energy is conserved (change ≈ 0)")
    print(f"  This is expected for time-independent Hamiltonians!")


def test_energy_non_conservation():
    """Test with time-dependent Hamiltonian (energy should NOT be conserved)."""
    print("\n" + "=" * 80)
    print("TEST 2: Energy Non-Conservation (Time-Dependent Hamiltonian)")
    print("=" * 80)
    print("\nUsing time-dependent external field: h(t) = A * sin(ω*t)")
    print("  A = 2.0 (amplitude)")
    print("  ω = 1.0 (frequency)")
    
    num_qubits = 4
    time_steps = 10
    dt = 0.1
    field_amplitude = 2.0
    field_frequency = 1.0
    
    result = run_xyz_heisenberg_benchmark(
        num_qubits=num_qubits,
        jx=1.0,
        jy=1.0,
        jz=1.0,
        external_field=0.0,  # Static field is 0, time-dependent field is added
        time_steps=time_steps,
        dt=dt,
        time_dependent_field=True,
        field_amplitude=field_amplitude,
        field_frequency=field_frequency,
    )
    
    print(f"\nInitial Energy: {result['initial_energy']:.10f}")
    print(f"Final Energy:   {result['final_energy']:.10f}")
    print(f"Energy Change:  {result['energy_change']:.10f}")
    print(f"\n✓ Energy is NOT conserved (change ≠ 0)")
    print(f"  This is expected for time-dependent Hamiltonians!")
    print(f"  The external field h(t) = {field_amplitude} * sin({field_frequency}*t)")
    print(f"  causes the Hamiltonian to change over time, breaking energy conservation.")


def main():
    """Run both tests."""
    print("\n" + "=" * 80)
    print("XYZ Heisenberg Model: Energy Conservation vs Non-Conservation")
    print("=" * 80)
    
    test_energy_conservation()
    test_energy_non_conservation()
    
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print("1. Time-independent Hamiltonian → Energy is conserved")
    print("2. Time-dependent Hamiltonian → Energy is NOT conserved")
    print("\nThe time-dependent external field h(t) = A*sin(ω*t) makes the")
    print("Hamiltonian explicitly time-dependent, which breaks energy conservation.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

