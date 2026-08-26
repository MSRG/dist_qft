"""
Fetch the results of a previously submitted hardware job (see
submit_hardware_job.py) and compute the compute-uncompute fidelity for
each qubit-size group.

Run with:
    python scripts/analyze_hardware_results.py --job-id <your-job-id>
"""

import argparse

from dqft.hardware import get_runtime_service, fetch_job_result
from dqft.analysis import clean_counts_list, group_counts_by_qubit_size, compute_fidelity_by_size
from dqft.plotting import plot_fidelity_vs_size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True, help="IBM Quantum Runtime job ID to fetch.")
    parser.add_argument(
        "--size-order", nargs="+", type=int, default=[1, 7, 6, 5, 4, 3, 2],
        help="Qubit sizes in the order their circuits were submitted "
             "(default matches submit_hardware_job.py's default suite order).",
    )
    args = parser.parse_args()

    service = get_runtime_service()
    result = fetch_job_result(service, args.job_id)

    raw_counts = [res.data.meas.get_counts() for res in result]
    cleaned = clean_counts_list(raw_counts)
    grouped = group_counts_by_qubit_size(cleaned, args.size_order)
    fidelities = compute_fidelity_by_size(grouped)

    print("Fidelity by qubit size:")
    for size in sorted(fidelities):
        print(f"  {size}-qubit circuits: fidelity = {fidelities[size]:.2f}%")

    plot_fidelity_vs_size(fidelities)


if __name__ == "__main__":
    main()
