"""
Benchmark circuit generation for empirically measuring distributed QFT fidelity.

For a fixed number of qubits n, this builds one circuit per computational
basis input |x> (x = 0 .. 2**n - 1) that:

  1. Prepares |x> with X gates.
  2. Applies the distributed QFT (`qft_circuit_dist`).
  3. Applies the *exact* phase corrections that analytically invert the QFT
     for the known input x (rather than re-running an inverse QFT circuit).
  4. Measures every qubit.

Because step 3 undoes the transform analytically, an ideal (noiseless)
execution of any of these circuits always returns the all-zero bitstring.
The measured population of the all-zero outcome on real/noisy hardware is
therefore a direct, per-input proxy for the fidelity of the distributed QFT
implementation -- this is the "compute-uncompute" fidelity test used
throughout the analysis scripts.
"""

from math import pi

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from .circuit import qft_circuit_dist

# Device-size split used for each qubit count in the original experiments.
# device_size is the number of data qubits per device passed to
# qft_circuit_dist(n_qubits, n_devices=2, device_size=...); the last device
# absorbs the remainder. n_qubits == 1 is a special case (see below).
DEFAULT_DEVICE_SIZE_BY_QUBITS = {
    1: 1,  # trivial: single-qubit QFT is just a Hadamard, no distribution needed
    2: 1,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
    7: 4,
}


def _prepare_basis_state(qc: QuantumCircuit, x: int, n_qubits: int) -> None:
    """Apply X gates so the first n_qubits data qubits encode |x>."""
    x_bits = [int(bit) for bit in f"{x:0>{n_qubits}b}"]
    for i, bit in enumerate(x_bits):
        if bit == 1:
            qc.x(i)


def _apply_exact_inverse_qft_phase_correction(qc: QuantumCircuit, x: int, n_qubits: int) -> None:
    """
    Apply the analytic inverse-QFT rotation for a known input x, so that an
    ideal execution collapses back to the all-zero bitstring.
    """
    for i, j in zip(range(n_qubits), range(n_qubits - 1, -1, -1)):
        angle = pi * x / 2 ** j
        qc.rz(-angle, i)
        qc.h(i)


def generate_compute_uncompute_circuits(
    n_qubits: int, n_devices: int, device_size: int
) -> list[QuantumCircuit]:
    """
    Generate the full family of compute-uncompute benchmark circuits for a
    given qubit count and device partition.

    Args:
        n_qubits: number of logical qubits under test.
        n_devices: number of devices to distribute the QFT across.
        device_size: data qubits per device (passed through to
            `qft_circuit_dist`; ignored for the n_qubits == 1 special case).

    Returns:
        A list of 2**n_qubits QuantumCircuits, one per computational basis
        input, each with quantum registers `dev0`, `dev1`, ..., `q_comm`
        and classical registers `cl_comm` (mid-circuit feed-forward) and
        `meas` (final measurement, one bit per logical qubit).
    """
    circuits = []

    for x in range(2 ** n_qubits):
        c = ClassicalRegister(1, "cl_comm")
        qc = QuantumCircuit(c)

        if n_qubits == 1:
            # Trivial case: a single-qubit QFT is just a Hadamard, so we skip
            # qft_circuit_dist entirely but keep the same register layout as
            # the other benchmark circuits for consistency downstream.
            qc.add_register(QuantumRegister(1, "dev0"))
            qc.add_register(QuantumRegister(1, "dev1"))
            qc.add_register(QuantumRegister(2, "q_comm"))
            qc.add_register(ClassicalRegister(n_qubits, "meas"))

            _prepare_basis_state(qc, x, n_qubits)
            qc.barrier()
            qc.h(0)
            qc.barrier()
        else:
            # Mirror the register partition that qft_circuit_dist will build,
            # so the basis-state prep below lines up with the data qubits.
            full_devices = min(n_qubits // device_size, n_devices)
            remainder = n_qubits % device_size

            for i in range(full_devices):
                qc.add_register(QuantumRegister(device_size, f"dev{i}"))
            if full_devices < n_devices and remainder > 0:
                qc.add_register(QuantumRegister(remainder, f"dev{full_devices}"))
            qc.add_register(QuantumRegister(n_devices, "q_comm"))
            qc.add_register(ClassicalRegister(n_qubits, "meas"))

            _prepare_basis_state(qc, x, n_qubits)
            qc.barrier()
            qc = qc.compose(
                qft_circuit_dist(n_qubits, n_devices, device_size),
                qubits=range(n_qubits + n_devices),
            )
            qc.barrier()

        _apply_exact_inverse_qft_phase_correction(qc, x, n_qubits)
        qc.barrier()

        for i in range(n_qubits):
            qc.measure(i, i + 1)

        circuits.append(qc)

    return circuits


def generate_default_benchmark_suite(
    n_devices: int = 2,
    qubit_sizes: range = range(1, 8),
    device_size_by_qubits: dict[int, int] | None = None,
) -> dict[int, list[QuantumCircuit]]:
    """
    Recreate the benchmark suite used in the original experiments: one
    family of compute-uncompute circuits for each qubit count 1..7, using
    the device-size splits in `DEFAULT_DEVICE_SIZE_BY_QUBITS`.

    Args:
        n_devices: number of devices to distribute each QFT across.
        qubit_sizes: iterable of qubit counts to generate circuits for.
        device_size_by_qubits: optional override for the default
            qubit-count -> device-size mapping.

    Returns:
        Dict mapping n_qubits -> list of benchmark circuits for that size.
    """
    mapping = device_size_by_qubits or DEFAULT_DEVICE_SIZE_BY_QUBITS
    return {
        n: generate_compute_uncompute_circuits(n, n_devices, mapping[n])
        for n in qubit_sizes
    }
