# Distributed QFT Hardware Backend

Implementation and IBM Quantum hardware benchmarking of a **distributed
Quantum Fourier Transform (QFT)** that spans multiple devices with no
direct qubit coupling between them. Cross-device controlled-phase
rotations are implemented via cat-entangler / cat-disentangler gate
teleportation gadgets over shared entangled ("e-bit") pairs.

Construction based on the distributed QFT decomposition of Vernec (2025).

This repository is a cleaned-up, modularized version of the original
research notebook. It was restructured into an installable Python package
plus a set of runnable scripts; the underlying quantum-circuit logic is
unchanged from the original experiments.

## Repository layout

```
src/dqft/
├── ebit.py         # cat-entangler / cat-disentangler gadgets
├── circuit.py       # core distributed QFT circuit builder
├── benchmarks.py     # compute-uncompute fidelity benchmark circuit generation
├── layout.py         # coupling-map partitioning + random-layout depth search
├── hardware.py        # IBM Quantum Runtime connection & job submission
├── analysis.py         # counts cleaning + fidelity computation
└── plotting.py          # shared plotting helpers

scripts/
├── demo_ebit_pairs.py           # minimal e-bit gadget usage example
├── demo_distributed_qft.py      # build & draw a small distributed QFT circuit
├── run_layout_experiment.py     # partition a fake backend & search random layouts
├── submit_hardware_job.py       # build benchmark suite & submit to real hardware
├── analyze_hardware_results.py  # fetch a job's results & compute fidelity
└── reproduce_paper_figures.py   # re-plot previously recorded write-up figures

tests/
└── test_circuits.py   # structural smoke tests (no hardware/network needed)
```

## Setup

### 1. Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .                # installs the dqft package + pinned deps
```

or, without an editable install:

```bash
pip install -r requirements.txt
```

### 2. Graphviz (required for coupling-map visualizations)

Qiskit's `CouplingMap.draw()` renders through
[Graphviz](https://graphviz.org/) via the `pydot` binding. `pydot` alone
is **not** sufficient — you need the actual Graphviz binary installed at
the OS level:

| OS | Command |
|---|---|
| Ubuntu / Debian | `sudo apt-get install graphviz` |
| macOS (Homebrew) | `brew install graphviz` |
| Windows | `choco install graphviz` (or download from graphviz.org) |
| conda (any OS) | `conda install -c conda-forge graphviz python-graphviz` |

If you don't need coupling-map drawings, everything else works without
Graphviz — pass `--no-draw` to `run_layout_experiment.py`.

### 3. IBM Quantum credentials (only needed for real-hardware scripts)

`submit_hardware_job.py` and `analyze_hardware_results.py` talk to real
IBM Quantum hardware and need credentials:

```bash
cp .env.example .env
# edit .env with your IBM Quantum token and instance CRN
export $(grep -v '^#' .env | xargs)   # or use a tool like python-dotenv / direnv
```

**Never commit `.env` or hardcode a token in source.** `hardware.py`
reads credentials exclusively from `IBM_QUANTUM_TOKEN` /
`IBM_QUANTUM_INSTANCE` environment variables and saves a named local
account on first use.

> The original notebook this repo was derived from had a live API token
> hardcoded directly in a cell. That token should be treated as
> compromised — if it's still yours, rotate it in your IBM Quantum
> account settings before relying on this repo for hardware runs.

## Usage

```bash
# No hardware/credentials needed:
python scripts/demo_ebit_pairs.py
python scripts/demo_distributed_qft.py
python scripts/run_layout_experiment.py --no-draw

# Requires IBM Quantum credentials:
python scripts/submit_hardware_job.py --backend ibm_brisbane --shots 200
python scripts/analyze_hardware_results.py --job-id <job-id-from-above>
```

Run the test suite (fast, no hardware/network required):

```bash
pytest tests/
```

## How it works

1. **`ebit.py`** — the `cat_entangler` / `cat_disentangler` gadgets
   consume a shared entangled pair plus a classical feed-forward
   correction to teleport a control qubit's state onto a remote
   communication qubit.
2. **`circuit.py`** — `qft_circuit_dist(n_qubits, n_devices, device_size)`
   partitions qubits across `n_devices` device registers and builds the
   QFT: local Hadamard + controlled-phase stages on each device, and
   remote controlled-phase stages across devices via the e-bit gadgets.
3. **`benchmarks.py`** — for a fixed qubit count, generates one circuit
   per computational basis input that prepares that input, runs the
   distributed QFT, then analytically applies the inverse rotations for
   that specific input. A noiseless run of any such circuit always lands
   on the all-zero bitstring, so the observed population of that outcome
   on real/noisy hardware is a direct fidelity proxy.
4. **`layout.py`** — since the "distributed" device boundary is emulated
   by removing edges from a single physical backend's coupling map,
   `run_random_layout_experiments` searches over random logical-to-physical
   qubit assignments to find layouts that transpile to low circuit depth.
5. **`hardware.py`** / **`analysis.py`** — submit transpiled circuits to
   IBM Quantum Runtime, then clean and group the returned measurement
   counts to compute per-size fidelity.


