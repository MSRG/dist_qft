"""
Post-processing utilities: cleaning raw measurement counts and computing
fidelity from them.

The compute-uncompute benchmark circuits (see benchmarks.py) are built so
that a noiseless execution always returns the all-zero bitstring on the
`meas` register. Fidelity is therefore estimated as the fraction of shots
that landed on the all-zero outcome.
"""

from collections import defaultdict


def clean_counts(raw_counts: dict) -> dict:
    """
    Strip the register-separator suffix Qiskit appends to multi-register
    bitstring keys (e.g. "0000 0" -> "0000"), collapsing duplicate keys by
    summing their shot counts.
    """
    cleaned = defaultdict(int)
    for key, value in raw_counts.items():
        cleaned_key = key.split()[0]
        cleaned[cleaned_key] += value
    return dict(cleaned)


def clean_counts_list(raw_counts_list: list) -> list:
    """Apply `clean_counts` to a list of per-circuit count dicts."""
    return [clean_counts(counts) for counts in raw_counts_list]


def group_counts_by_qubit_size(cleaned_counts_list: list, size_order: list) -> dict:
    """
    Group a flat list of per-circuit counts into per-qubit-size buckets.

    `size_order` gives the qubit sizes in the order their circuits were
    submitted, e.g. [1, 7, 6, 5, 4, 3, 2]. Each size n contributes 2**n
    circuits (one per computational basis input), consumed from the front
    of `cleaned_counts_list` in order.

    Returns:
        Dict {qubit_size: merged counts dict} where the merged counts dict
        sums shot counts for every circuit of that size.
    """
    size_grouped_counts = {}
    start_index = 0

    for size in size_order:
        count_this_size = 2 ** size
        size_grouped_counts[size] = defaultdict(int)

        for counts in cleaned_counts_list[start_index:start_index + count_this_size]:
            for key, value in counts.items():
                size_grouped_counts[size][key] += value

        start_index += count_this_size

    return {size: dict(counts) for size, counts in size_grouped_counts.items()}


def compute_fidelity_by_size(size_grouped_counts: dict) -> dict:
    """
    Compute the all-zero-outcome fidelity (as a percentage) for each qubit
    size in a grouped-counts dict, as produced by `group_counts_by_qubit_size`.
    """
    fidelities = {}
    for size, counts in size_grouped_counts.items():
        total_shots = sum(counts.values())
        ideal_key = "0" * size
        fidelity_ratio = counts.get(ideal_key, 0) / total_shots
        fidelities[size] = round(fidelity_ratio * 100, 2)
    return fidelities


def compute_success_fidelity_series(counts_list: list, ideal_bitstring: str) -> list:
    """
    Compute a per-circuit success fidelity (percentage of shots matching
    `ideal_bitstring` out of all shots) across a list of raw counts dicts.

    Useful for a single fixed-size sweep (e.g. one qubit count run across
    many input states), as opposed to `compute_fidelity_by_size` which
    groups multiple qubit sizes together.
    """
    fidelities = []
    for counts in counts_list:
        pos_counts = counts.get(ideal_bitstring, 0)
        total_counts = sum(counts.values())
        fidelities.append((pos_counts * 100) / total_counts if total_counts else 0.0)
    return fidelities
