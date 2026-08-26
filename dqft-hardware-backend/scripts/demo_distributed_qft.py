"""
Build and draw a small distributed QFT circuit split across two devices.

Run with:
    python scripts/demo_distributed_qft.py
"""

from dqft import qft_circuit_dist


def main():
    # 4 logical qubits, split across 2 devices of 2 qubits each.
    dist_qft = qft_circuit_dist(n_qubits=4, n_devices=2, device_size=2)

    print(f"Registers: {[reg.name for reg in dist_qft.qregs]}")
    print(f"Circuit depth: {dist_qft.depth()}")
    print(dist_qft.draw(output="text", fold=120))


if __name__ == "__main__":
    main()
