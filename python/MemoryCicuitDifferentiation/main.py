"""
Main entry point for demonstrating PennyLane gradient bugs.
Run the comprehensive demonstration by importing the bug demo module.
"""

from pennylane_gradient_bugs import PennyLaneGradientBugDemo

if __name__ == "__main__":
    demo = PennyLaneGradientBugDemo()
    # demo.run_all_demos()
    demo.bug_2_state_reuse_no_cloning()