"""
dqft: Distributed Quantum Fourier Transform circuits and hardware experiments.

This package implements a distributed Quantum Fourier Transform (QFT) that
spans multiple "devices" (partitions of qubits with no direct native
coupling), using cat-entangler / cat-disentangler gadgets built on shared
e-bit (entangled) pairs to teleport controlled-phase operations across
device boundaries. It also includes the tooling used to benchmark that
circuit on IBM Qiskit fake backends and real IBM Quantum hardware.

Reference: distributed QFT construction based on Vernec (2025).
"""

from .ebit import cat_entangler, cat_disentangler
from .circuit import qft_circuit_dist
from .benchmarks import generate_compute_uncompute_circuits, generate_default_benchmark_suite

__all__ = [
    "cat_entangler",
    "cat_disentangler",
    "qft_circuit_dist",
    "generate_compute_uncompute_circuits",
    "generate_default_benchmark_suite",
]
