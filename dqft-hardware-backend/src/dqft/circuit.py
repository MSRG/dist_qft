"""
Core distributed Quantum Fourier Transform (QFT) circuit construction.

The construction follows Vernec (2025): the QFT is decomposed into local
QFT stages on each device plus remote controlled-phase rotations between
qubits on different devices. Remote controlled-phase gates are implemented
by teleporting the control qubit's state onto a communication qubit on the
target device (via the cat-entangler gadget), applying the phase rotations
locally, and then disentangling (via the cat-disentangler gadget).
"""

from math import pi

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def qft_circuit_dist(n_qubits: int, n_devices: int, device_size: int) -> QuantumCircuit:
    """
    Build a distributed QFT circuit spread across multiple devices.

    Qubits are packed greedily into `n_devices` registers named `dev0`,
    `dev1`, ... each of size `device_size` (the final populated device may
    hold fewer qubits if `n_qubits` doesn't divide evenly). One additional
    communication qubit is allocated per device in a shared `q_comm`
    register; this assumes a single communication qubit per device.

    Args:
        n_qubits: total number of logical qubits the QFT acts on.
        n_devices: number of devices (communication qubits) available.
        device_size: number of data qubits per device.

    Returns:
        QuantumCircuit: the distributed QFT circuit, with quantum registers
        `dev0`, `dev1`, ..., `q_comm`, and a single-bit classical register
        `cl_comm` used for the mid-circuit feed-forward corrections in the
        cat-entangler/disentangler gadgets.

        Returns None (and prints a message) if `n_qubits` exceeds the total
        available device capacity (`n_devices * device_size`).
    """
    if n_qubits > n_devices * device_size:
        print("not enough device space")
        return

    c = ClassicalRegister(1, "cl_comm")
    qc = QuantumCircuit(c)

    # --- Qubit allocation -------------------------------------------------
    full_devices = min(n_qubits // device_size, n_devices)
    remainder = n_qubits % device_size

    for i in range(full_devices):
        qc.add_register(QuantumRegister(device_size, f"dev{i}"))

    if full_devices < n_devices and remainder > 0:
        qc.add_register(QuantumRegister(remainder, f"dev{full_devices}"))

    qc.add_register(QuantumRegister(n_devices, "q_comm"))

    # --- Circuit logic ------------------------------------------------------
    # Iterate over each device register (all registers except the final
    # communication register).
    for dev_idx, qreg in enumerate(qc.qregs[:-1]):
        for i, idx_qubit in enumerate(qreg):
            angle_coeff = 1
            qc.h(idx_qubit)

            # Local controlled-phase rotations to later qubits on the same device.
            for next_qubit in qreg[i + 1:]:
                qc.cp(pi / (2 ** angle_coeff), idx_qubit, next_qubit)
                angle_coeff += 1

            # Remote controlled-phase rotations to qubits on subsequent devices,
            # implemented via the cat-entangler / cat-disentangler gate
            # teleportation gadgets over the shared communication qubits.
            for later_dev_idx, later_dev in enumerate(qc.qregs[dev_idx + 1:-1], dev_idx + 1):
                # Cat entangler: teleport idx_qubit's control state onto the
                # communication qubit of the later device.
                qc.h(qc.qregs[-1][dev_idx])
                qc.cx(qc.qregs[-1][dev_idx], qc.qregs[-1][later_dev_idx])

                qc.cx(idx_qubit, qc.qregs[-1][dev_idx])
                qc.measure(qc.qregs[-1][dev_idx], c)
                with qc.if_test((c, 1)):
                    qc.x(qc.qregs[-1][dev_idx])
                    qc.x(qc.qregs[-1][later_dev_idx])

                # Apply the controlled-phase rotations locally on the later
                # device, using the teleported communication qubit as control.
                for other_qubit in later_dev:
                    qc.cp(pi / (2 ** angle_coeff), qc.qregs[-1][later_dev_idx], other_qubit)
                    angle_coeff += 1

                # Cat disentangler: consume the e-bit pair and return the
                # control correlation to idx_qubit.
                qc.h(qc.qregs[-1][later_dev_idx])
                qc.measure(qc.qregs[-1][later_dev_idx], c)
                with qc.if_test((c, 1)):
                    qc.z(idx_qubit)
                    qc.x(qc.qregs[-1][later_dev_idx])

    return qc
