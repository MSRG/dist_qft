"""
End-to-end pipeline: build the compute-uncompute benchmark suite, find a
low-depth layout for each qubit-count group, transpile every circuit in
that group against the shared layout, and submit the whole batch to real
IBM Quantum hardware as a single job.

Requires IBM_QUANTUM_TOKEN / IBM_QUANTUM_INSTANCE to be set (see
.env.example) -- credentials are never read from source code.

Note on the original notebook: the equivalent cell re-ran the random
layout search once per circuit within a qubit-size group (2**n times for
an n-qubit group), even though every circuit in the group shares the same
`dist_qft` structure and the search is deterministic given a fixed seed.
That repetition didn't change the result, just the runtime -- this script
runs the layout search once per group instead.

Run with:
    python scripts/submit_hardware_job.py --backend ibm_brisbane --shots 200
"""

import argparse

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBrisbane

from dqft import qft_circuit_dist, generate_default_benchmark_suite
from dqft.layout import build_disconnected_coupling_map, run_random_layout_experiments
from dqft.hardware import get_runtime_service, get_sampler, submit_circuits

# Same Heron-processor partition used in run_layout_experiment.py, reused
# here so the coupling map used for transpilation matches the topology of
# the real ibm_brisbane backend (which is also a Heron device).
_HERON_DEV_A = {58, 62, 70}
_HERON_DEV_B = {71, 72, 74}


def build_all_circuits(backend, cloned_map, size_order=(1, 7, 6, 5, 4, 3, 2)):
    """
    Build the full benchmark suite and transpile every circuit against a
    layout found for its qubit-size group.
    """
    suite = generate_default_benchmark_suite(qubit_sizes=size_order)

    all_circuits = []
    for n_qubits in size_order:
        circs = suite[n_qubits]

        # Each circuit register layout has 2 extra qubits (n_qubits data +
        # 2 device registers effectively -2 offset used in the original
        # experiments to size the "device_size" search); mirror that here.
        dist_qft = qft_circuit_dist(
            n_qubits, n_devices=2, device_size=int(n_qubits / 2) + (n_qubits % 2)
        )
        _, final_layout = run_random_layout_experiments(
            dist_qft, backend, cloned_map, num_trials=20
        )

        pm_final = generate_preset_pass_manager(
            optimization_level=3, backend=backend, coupling_map=cloned_map,
            initial_layout=final_layout,
        )
        all_circuits.extend(pm_final.run(qc) for qc in circs)

    return all_circuits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="ibm_brisbane", help="Real backend name to target.")
    parser.add_argument("--shots", type=int, default=200)
    args = parser.parse_args()

    service = get_runtime_service()
    sampler = get_sampler(service, args.backend)

    # Coupling map partitioned to match the target backend's topology.
    cloned_map = build_disconnected_coupling_map(FakeBrisbane(), _HERON_DEV_A, _HERON_DEV_B)

    all_circuits = build_all_circuits(service.backend(args.backend), cloned_map)
    print(f"Built {len(all_circuits)} transpiled circuits.")

    job = submit_circuits(sampler, all_circuits, shots=args.shots)
    print(f"Job ID: {job.job_id()}  (save this for scripts/analyze_hardware_results.py)")


if __name__ == "__main__":
    main()
