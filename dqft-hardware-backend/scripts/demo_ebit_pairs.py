"""
Minimal demo of the e-bit pair gadgets: build a cat-entangler and
cat-disentangler, and compose them around a remote CX to show how a
controlled operation can be teleported between a "control" qubit and a
"target" qubit that don't share a direct connection.

Run with:
    python scripts/demo_ebit_pairs.py
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from dqft import cat_entangler, cat_disentangler


def main():
    control = QuantumRegister(1, name="Control")
    comm = QuantumRegister(2, name="Comm")
    target = QuantumRegister(1, name="Target")
    creg = ClassicalRegister(1, name="ClComm")

    qc = QuantumCircuit(control, comm, target, creg)

    # Entangle the control qubit's state onto the remote communication qubit.
    qc = qc.compose(cat_entangler(), range(3), clbits=[creg[0]])

    # Perform the "remote" CX now that control's state has been teleported
    # onto the local communication qubit of the target's device.
    qc.cx(2, 3)

    # Disentangle, returning correlations to the original control qubit.
    qc = qc.compose(cat_disentangler(), [control[0], comm[1]], clbits=creg[0])

    print(qc.draw(output="text"))


if __name__ == "__main__":
    main()
