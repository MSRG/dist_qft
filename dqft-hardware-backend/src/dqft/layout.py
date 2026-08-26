"""
Coupling-map partitioning and qubit-layout search utilities.

To emulate a "distributed" system on a single physical QPU, we take a real
backend's coupling map and remove the edges directly connecting two chosen
sets of physical qubits, so those two qubit sets behave like separate
devices with no native coupling (communication between them must go
through the e-bit gadgets instead). We then search over random qubit
layouts (device-register -> physical-qubit assignments) and transpile the
distributed QFT circuit under each one, to find layouts that transpile to
low circuit depth.
"""

import random
import warnings

from qiskit.transpiler import CouplingMap, Layout
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# We intentionally pass both `backend` and a modified `coupling_map` to
# generate_preset_pass_manager below: the whole point of this module is to
# transpile against a coupling map with some edges removed (to emulate
# device separation) while still targeting a real backend's gate set and
# calibration data. Qiskit warns about this combination by design, so we
# suppress that specific warning here rather than needing every caller to
# do so.
warnings.filterwarnings(
    "ignore",
    message="Providing `coupling_map` and/or `basis_gates` along with `backend`.*",
    category=UserWarning,
    module="qiskit.transpiler.preset_passmanagers.generate_preset_pass_manager",
)

# Backend-specific physical-qubit pools for the dev0/dev1 registers, keyed
# by the distributed QFT's total qubit count. These were hand-picked to sit
# near the "dev_a"/"dev_b" partition boundary on the target backend
# (originally tuned against FakeBrisbane's Heron topology) so that
# transpiled layouts stay compact. Adjust these if you target a different
# backend or coupling map partition.
#
# Note: the communication register (`q_comm`) is always pinned separately
# to DEFAULT_Q_COMM_PHYSICAL_QUBITS below, matching the original
# experiments -- these per-size tables only affect dev0/dev1 placement.
_REGISTER_PHYSICAL_MAPS_BY_QUBIT_COUNT = {
    11: {"dev0": {67, 68, 55, 49, 48}, "dev1": {84, 85, 86, 87}},
    10: {"dev0": {67, 68, 55, 49}, "dev1": {84, 85, 86, 87}},
    9: {"dev0": {67, 68, 55, 49}, "dev1": {84, 85, 86}},
    8: {"dev0": {67, 68, 55}, "dev1": {84, 85, 86}},
    7: {"dev0": {67, 68, 55}, "dev1": {84, 85}},
    6: {"dev0": {67, 68}, "dev1": {84, 85}},
    5: {"dev0": {67, 68}, "dev1": {84, 85}},
    4: {"dev0": {67}, "dev1": {85}},
}
_DEFAULT_REGISTER_PHYSICAL_MAP = {
    "dev0": set(range(12, 62)),
    "dev1": set(range(75, 126)),
}
# Fallback used for dist_qft.num_qubits <= 3.
_SMALL_REGISTER_PHYSICAL_MAP = {"dev0": {67}, "dev1": {85}}

# Physical qubits the two `q_comm` register qubits are pinned to. Fixed
# across all circuit sizes in the original experiments.
DEFAULT_Q_COMM_PHYSICAL_QUBITS = (62, 72)


def build_disconnected_coupling_map(backend, dev_a: set, dev_b: set) -> CouplingMap:
    """
    Clone a backend's coupling map and remove any edges directly connecting
    physical qubits in `dev_a` to physical qubits in `dev_b`, simulating a
    partition of one physical QPU into two devices with no native coupling
    between them.

    Args:
        backend: a Qiskit backend (real or fake) exposing `.configuration()`.
        dev_a: set of physical qubit indices assigned to "device A".
        dev_b: set of physical qubit indices assigned to "device B".

    Returns:
        CouplingMap: a copy of the backend's coupling map with the
        A<->B edges removed.
    """
    coupling_list = backend.configuration().coupling_map
    cloned_map = CouplingMap(couplinglist=coupling_list)

    for u, v in list(cloned_map.get_edges()):
        if (u in dev_a and v in dev_b) or (u in dev_b and v in dev_a):
            cloned_map.graph.remove_edge(u, v)

    return cloned_map


def get_qubits_by_register_name(circuit, register_name: str):
    """Return the list of Qubit objects belonging to a named register."""
    for reg in circuit.qregs:
        if reg.name == register_name:
            return reg[:]
    raise ValueError(f"Register '{register_name}' not found.")


def get_register_name(circuit, qubit) -> str | None:
    """Return the register name a given qubit belongs to."""
    _, reg_info = circuit.find_bit(qubit)
    return reg_info[0][0].name if reg_info else None


def get_register_index(circuit, qubit) -> int | None:
    """Return a qubit's index within its register."""
    _, reg_info = circuit.find_bit(qubit)
    return reg_info[0][1] if reg_info else None


def generate_random_layout(
    circuit, q_comm_layout: dict, register_physical_map: dict, seed: int | None = None
) -> Layout:
    """
    Generate a random initial layout: the communication register is pinned
    to `q_comm_layout`, and each device register's qubits are randomly
    assigned to physical qubits drawn from its pool in
    `register_physical_map`.

    Args:
        circuit: the logical circuit being laid out.
        q_comm_layout: fixed {logical q_comm qubit: physical qubit index} map.
        register_physical_map: {register_name: set of candidate physical
            qubit indices} for the "dev0"/"dev1"/... registers.
        seed: optional RNG seed for reproducibility.

    Returns:
        Layout: a Qiskit transpiler Layout covering all qubits in `circuit`.
    """
    if seed is not None:
        random.seed(seed)

    layout = Layout()
    used_physical = set(q_comm_layout.values())

    for q, p in q_comm_layout.items():
        layout[q] = p

    for reg in circuit.qregs:
        if reg.name in ("q_comm",):
            continue
        logical_qubits = get_qubits_by_register_name(circuit, reg.name)
        physical_pool = list(register_physical_map[reg.name] - used_physical)
        if len(logical_qubits) > len(physical_pool):
            raise ValueError(f"Not enough physical qubits for {reg.name}")
        random.shuffle(physical_pool)
        for q, p in zip(logical_qubits, physical_pool):
            layout[q] = p
            used_physical.add(p)

    return layout


def layout_to_str(layout: Layout, circuit) -> str:
    """Render a layout as a sorted, human-readable 'register[idx]: physical' string."""
    layout_strs = []
    for q in circuit.qubits:
        reg_name = get_register_name(circuit, q)
        reg_idx = get_register_index(circuit, q)
        phys = layout[q]
        layout_strs.append(f"{reg_name}[{reg_idx}]: {phys}")
    return ", ".join(sorted(layout_strs))


def _register_physical_map_for(num_qubits: int) -> dict:
    """Look up the physical-qubit pool table for a given total qubit count."""
    if num_qubits in _REGISTER_PHYSICAL_MAPS_BY_QUBIT_COUNT:
        return _REGISTER_PHYSICAL_MAPS_BY_QUBIT_COUNT[num_qubits]
    if num_qubits <= 3:
        return _SMALL_REGISTER_PHYSICAL_MAP
    return _DEFAULT_REGISTER_PHYSICAL_MAP


def run_random_layout_experiments(
    dist_qft, backend, cloned_map: CouplingMap, num_trials: int = 20, seed: int = 123456789
):
    """
    Transpile `dist_qft` under `num_trials` random initial layouts and
    record the resulting transpiled circuit depth for each.

    Args:
        dist_qft: the distributed QFT circuit to transpile.
        backend: target backend for transpilation.
        cloned_map: coupling map to transpile against (e.g. one produced by
            `build_disconnected_coupling_map`).
        num_trials: number of random layouts to try.
        seed: base RNG seed; trial i uses seed + i.

    Returns:
        Tuple of:
            results: dict {layout description string: transpiled circuit depth}
            last_layout: the Layout object used in the final trial.
    """
    register_physical_map = _register_physical_map_for(dist_qft.num_qubits)

    q_comm_register = next(reg for reg in dist_qft.qregs if reg.name == "q_comm")
    q_comm_qubits = q_comm_register[:]
    q_comm_layout = {
        q_comm_qubits[i]: DEFAULT_Q_COMM_PHYSICAL_QUBITS[i] for i in range(len(q_comm_qubits))
    }

    results = {}
    last_layout = None

    for i in range(num_trials):
        layout = generate_random_layout(dist_qft, q_comm_layout, register_physical_map, seed + i)
        layout_key = layout_to_str(layout, dist_qft)

        pm = generate_preset_pass_manager(
            optimization_level=3,
            backend=backend,
            coupling_map=cloned_map,
            initial_layout=layout,
            seed_transpiler=seed,
        )
        tdist_qft = pm.run(dist_qft)
        results[layout_key] = tdist_qft.depth()
        last_layout = layout

    return results, last_layout
