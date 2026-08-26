"""
Plotting helpers for the layout-search and fidelity analyses.

Each function takes the data to plot as arguments rather than reading
global state, so the same helpers can be reused across the demo scripts
and for reproducing the write-up figures with different datasets.
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_layout_depth_histogram(results: dict, title: str = "Circuit Depth vs. Qubit Layout"):
    """
    Bar chart of transpiled circuit depth for each random layout trial.

    Args:
        results: dict {layout description string: transpiled circuit depth},
            as returned by `layout.run_random_layout_experiments`.
    """
    plt.figure(figsize=(14, 6))
    labels = list(results.keys())
    depths = list(results.values())

    plt.bar(range(len(labels)), depths, tick_label=range(len(labels)))
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=8)
    plt.ylabel("Transpiled Circuit Depth")
    plt.xlabel("Qubit Layout")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_fidelity_vs_size(fidelities_by_size: dict, title: str = "Fidelity vs QFT Size"):
    """Line plot of fidelity (%) against qubit count."""
    sizes = sorted(fidelities_by_size.keys())
    plt.figure(figsize=(4, 5))
    plt.plot(sizes, [fidelities_by_size[s] for s in sizes], marker="o", linestyle="-")
    plt.ylim(0, 100)
    plt.xlabel("Qubit Size")
    plt.ylabel("Fidelity (%)")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_fidelity_vs_size_with_error(
    sizes: list, fidelities: list, yerr: list, title: str = "Fidelity vs. QFT Size"
):
    """Errorbar plot of fidelity (%) against qubit count."""
    plt.figure(figsize=(5, 5))
    plt.errorbar(sizes, fidelities, np.array(yerr), ecolor="red")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Fidelity (%)")
    plt.title(title)
    plt.grid(True)
    plt.show()


def plot_runtime_comparison(
    sizes: list,
    naive_runtime: list,
    gate_packing_runtime: list,
    title: str = "Circuit Runtime vs. QFT Size",
):
    """Compare device runtime (s) between the naive and gate-packing methods."""
    plt.figure()
    plt.plot(sizes, naive_runtime, label="Naive Method")
    plt.plot(sizes, gate_packing_runtime, label="Gate Packing Method")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Quantum Device Runtime (s)")
    plt.legend()
    plt.grid(True)
    plt.title(title)
    plt.show()


def plot_fidelity_method_comparison(
    sizes: list,
    naive_fidelity: list,
    gate_packing_fidelity: list,
    title: str = "Fidelity vs. QFT Size",
):
    """Compare fidelity (%) between the naive and gate-packing methods."""
    plt.figure(figsize=(5, 5))
    plt.plot(sizes, naive_fidelity, label="Naive Method")
    plt.plot(sizes, gate_packing_fidelity, label="Gate Packing")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Fidelity (%)")
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.show()



