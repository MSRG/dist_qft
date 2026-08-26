"""
E-bit pair primitives.

These two circuits are the building blocks used to remotely apply a
controlled operation across a pair of qubits that live on different
"devices" (i.e. qubits with no direct native coupling), by consuming a
shared entangled Bell pair ("e-bit") and a classical feed-forward
correction. This is the standard cat-entangler / cat-disentangler
construction used for gate teleportation in distributed quantum computing.
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def cat_entangler() -> QuantumCircuit:
    """
    Build the cat-entangler gadget.

    Qubit roles (in circuit order):
        q0 - control qubit, local to the source device
        q1 - communication qubit on the source device (local half of the e-bit)
        q2 - communication qubit on the target device (remote half of the e-bit)

    The gadget prepares a Bell pair across (q1, q2), entangles the control
    qubit q0 with the local half of that pair, then measures q1 and applies
    a classically-controlled correction to q2. After this gadget, q2 carries
    the control information that originated on q0, and can be used as the
    control for a local two-qubit gate on the target device.

    Returns:
        QuantumCircuit: a 3-qubit, 1-classical-bit circuit implementing the
        cat entangler.
    """
    q_reg = QuantumRegister(3)
    cl_reg = ClassicalRegister(1, name="ClComm")
    cat_qc = QuantumCircuit(q_reg, cl_reg)

    # Prepare a Bell pair between the two communication qubits.
    cat_qc.h(1)
    cat_qc.cx(1, 2)

    # Entangle the control qubit with the local half of the e-bit pair, then
    # measure it out and classically correct the remote half so it inherits
    # the control's state.
    cat_qc.cx(0, 1)
    cat_qc.measure(1, 0)
    with cat_qc.if_test((0, 1)):
        cat_qc.x(1)
        cat_qc.x(2)

    return cat_qc


def cat_disentangler() -> QuantumCircuit:
    """
    Build the cat-disentangler gadget, which undoes a prior cat_entangler
    application and consumes the remaining half of the e-bit pair.

    Qubit roles (in circuit order):
        q0 - control qubit, local to the source device
        q1 - communication qubit on the target device (remote half of the e-bit)

    Returns:
        QuantumCircuit: a 2-qubit, 1-classical-bit circuit implementing the
        cat disentangler.
    """
    q_reg = QuantumRegister(2)
    cl_reg = ClassicalRegister(1, name="ClComm")
    uncat_qc = QuantumCircuit(q_reg, cl_reg)

    uncat_qc.h(1)
    uncat_qc.measure(1, 0)
    with uncat_qc.if_test((0, 1)):
        uncat_qc.z(0)
        uncat_qc.x(1)

    return uncat_qc
