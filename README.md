# dist_qft

Distributed Quantum Fourier Transform (dQFT)

# Installation

Clone this repository.

Installation inscructions are similar to [github.com/Quantinuum/pytket-dqc#installing-pytket-dqc#installing-pytket-dqc](https://github.com/Quantinuum/pytket-dqc#installing-pytket-dqc), but with additional recommendations below to avoid installation issues.

## 1. Graphviz

`apt install libgraphviz-dev pkg-config`

## 2. Python environment

With uv, simply run `uv sync` from within the `dist_qft` folder to install python environment.

## 3. Boost

First, install boost: [www.boost.org/doc/libs/1_78_0/tools/build/doc/html/index.html#bbv2#bbv2.installation](https://www.boost.org/doc/libs/1_78_0/tools/build/doc/html/index.html#bbv2.installation) with suggested prefix: '/usr/local'

Install boost headers: `apt install libboost-program-options-dev libboost-dev uuid-dev`

## 4. KaHyPar

Installation instructions are similar to [github.com/kahypar/kahypar/blob/1.3.2/README.md#building-kahypar](https://github.com/kahypar/kahypar/blob/1.3.2/README.md#building-kahypar), but with the modifications below for reproducibility and to avoid installation issues.

Use python version 3.11:

```shell
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-dev
```

Clone KaHyPar version 1.3.2 specifically, using this command:`git clone --depth=1 --recursive --branch 1.3.2 https://github.com/kahypar/kahypar.git`
The KaHyPar directory can go anywhere on your system. The remainder of these installation instructions wil assume it is in `/home/ubuntu/`.

Fix a bug in the KaHyPar installation:

```shell
cd /home/ubuntu/kahypar/python/pybind11
git fetch origin --tags
git checkout v2.12.0
```

Now run the KaHyPar building instructions as follows:

```shell
cd /home/ubuntu/kahypar
mkdir build && cd build
cmake ../ -DCMAKE_BUILD_TYPE=RELEASE -DKAHYPAR_PYTHON_INTERFACE=1 -DPython_EXECUTABLE=/usr/bin/python3.11 -DPYTHON_EXECUTABLE=/usr/bin/python3.11
cd python
make
cp kahypar*.so <path-to-site-packages>
```

Make sure to use the correct cmake parameters as written above.
Make sure to replace `<path-to-site-packages>` with the correct path for the python site packages used for this repo (`dist_qft`). For the `.venv` created by uv, this would be `dist_qft/.venv/lib/python3.11/site-packages`.

# Data and plots

Run `main_*_qpus.py` to generate data and `plot_*_qpus.py` to generate graphs from the data.

For reproducibility, run with PYTHONHASHSEED as environment variable. With uv, this can be done with `uv run --env-file .env main_few_qpus.py` to use the same PYTHONHASHSEED as in the paper. 
