"""
Smoke tests for circuit construction. These only check structural
properties (register names, qubit/circuit counts) -- they don't run any
simulation, so they're fast and require no IBM Quantum credentials.

Run with:
    pytest tests/
"""

from dqft import cat_entangler, cat_disentangler, qft_circuit_dist
from dqft.benchmarks import generate_compute_uncompute_circuits, generate_default_benchmark_suite


def test_cat_entangler_shape():
    qc = cat_entangler()
    assert qc.num_qubits == 3
    assert qc.num_clbits == 1


def test_cat_disentangler_shape():
    qc = cat_disentangler()
    assert qc.num_qubits == 2
    assert qc.num_clbits == 1


def test_qft_circuit_dist_register_names():
    qc = qft_circuit_dist(n_qubits=4, n_devices=2, device_size=2)
    reg_names = [reg.name for reg in qc.qregs]
    assert reg_names == ["dev0", "dev1", "q_comm"]
    assert qc.num_qubits == 4 + 2  # data qubits + one comm qubit per device


def test_qft_circuit_dist_rejects_oversized_input():
    result = qft_circuit_dist(n_qubits=10, n_devices=2, device_size=2)
    assert result is None


def test_qft_circuit_dist_uneven_split():
    # 5 qubits across 2 devices of size 3 -> dev0 gets 3, dev1 gets remainder (2).
    qc = qft_circuit_dist(n_qubits=5, n_devices=2, device_size=3)
    sizes = {reg.name: len(reg) for reg in qc.qregs}
    assert sizes["dev0"] == 3
    assert sizes["dev1"] == 2
    assert sizes["q_comm"] == 2


def test_generate_compute_uncompute_circuits_count():
    circuits = generate_compute_uncompute_circuits(n_qubits=3, n_devices=2, device_size=2)
    assert len(circuits) == 2 ** 3
    for qc in circuits:
        assert qc.cregs[-1].name == "meas"
        assert len(qc.cregs[-1]) == 3


def test_generate_compute_uncompute_circuits_single_qubit_case():
    circuits = generate_compute_uncompute_circuits(n_qubits=1, n_devices=2, device_size=1)
    assert len(circuits) == 2


def test_generate_default_benchmark_suite_sizes():
    suite = generate_default_benchmark_suite(qubit_sizes=range(1, 4))
    assert set(suite.keys()) == {1, 2, 3}
    assert len(suite[1]) == 2
    assert len(suite[2]) == 4
    assert len(suite[3]) == 8
