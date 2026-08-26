"""
Reproduce the layout-search experiment: partition a fake IBM backend's
coupling map into two disconnected "devices", then transpile a distributed
QFT circuit under many random qubit layouts to see how transpiled circuit
depth varies.

Requires Graphviz to be installed at the OS level to draw coupling maps
(see README.md) -- drawing is optional and can be skipped with --no-draw.

Run with:
    python scripts/run_layout_experiment.py
    python scripts/run_layout_experiment.py --backend torino --no-draw
"""

import argparse

from qiskit_ibm_runtime.fake_provider import FakeBrisbane, FakeTorino

from dqft import qft_circuit_dist
from dqft.layout import build_disconnected_coupling_map, run_random_layout_experiments
from dqft.plotting import plot_layout_depth_histogram

# Physical-qubit sets whose direct coupling is removed to simulate two
# independent devices, tuned per backend topology.
_DEV_PARTITIONS = {
    "brisbane": (FakeBrisbane, {58, 62, 70}, {71, 72, 74}),
    "torino": (FakeTorino, {61, 65, 73}, {76, 77, 79}),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend", choices=_DEV_PARTITIONS.keys(), default="brisbane",
        help="Which fake backend topology to partition (default: brisbane).",
    )
    parser.add_argument(
        "--n-qubits", type=int, default=4, help="Logical qubits in the distributed QFT."
    )
    parser.add_argument(
        "--device-size", type=int, default=2, help="Data qubits per device."
    )
    parser.add_argument(
        "--num-trials", type=int, default=20, help="Number of random layouts to try."
    )
    parser.add_argument(
        "--no-draw", action="store_true", help="Skip drawing the coupling map (needs Graphviz)."
    )
    args = parser.parse_args()

    backend_cls, dev_a, dev_b = _DEV_PARTITIONS[args.backend]
    backend = backend_cls()

    cloned_map = build_disconnected_coupling_map(backend, dev_a, dev_b)
    if not args.no_draw:
        cloned_map.draw()

    dist_qft = qft_circuit_dist(args.n_qubits, n_devices=2, device_size=args.device_size)

    results, final_layout = run_random_layout_experiments(
        dist_qft, backend, cloned_map, num_trials=args.num_trials
    )

    best_layout = min(results, key=results.get)
    print(f"Best transpiled depth: {results[best_layout]} for layout:\n  {best_layout}")

    plot_layout_depth_histogram(results)


if __name__ == "__main__":
    main()
