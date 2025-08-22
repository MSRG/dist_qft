from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_results():
    # Define file paths
    result_filenames = [
        "results-data-gcp-s.txt",
        "results-data-gcp-e.txt",
        "results-data-fgp-roee.txt",
        "results-data-pytket-aesd.txt",
        "results-data-pytket-pe.txt",
        "results-data-pytket-phe.txt",
        "results-data-mlfm-r.txt", 
        "results-data-zv-thy.txt",
    ]
    method_names = [
        "GCP-S",
        "GCP-E",
        "FGP-rOEE",
        "Pytket-AESD",
        "Pytket-PE",
        "Pytket-PHE",
        "MLFM-R",
        "Detached Gates (Ours)",
    ]

    folderpath = Path(f'./results_many_qpus/')

    # Initialize data storage
    qpu_sizes = {method:[] for method in method_names}
    qubit_counts = {method:[] for method in method_names}
    partition_counts = {method:[] for method in method_names}
    e_bit_counts = {method:[] for method in method_names}
    times = {method:[] for method in method_names}
    

    for filename, method_name in zip(result_filenames, method_names):

        filepath = folderpath / filename

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if "qpu_size" in line:
                    qpu_size = int(line.split(",")[0].split("=")[1])
                    qpu_sizes[method_name].append(qpu_size)
                if "num_qubits" in line:
                    qubit_count = int(line.split(",")[1].split("=")[1])
                    qubit_counts[method_name].append(qubit_count)
                if "num_qubits" in line:
                    partition_count = int(line.split(",")[2].split("=")[1])
                    partition_counts[method_name].append(partition_count)
                elif "Min e-bit count" in line:
                    e_bit_count = int(line.split(":")[1].strip())
                    e_bit_counts[method_name].append(e_bit_count)
                elif "Time taken" in line:
                    time = float(line.split(":")[1].split()[0].strip())
                    times[method_name].append(time)

    for i in range(len(method_names)-1):
        assert partition_counts[method_names[i]] == partition_counts[method_names[i+1]], f"Partition count do not match across methods {method_names[i]} and {method_names[i+1]}"
    partition_counts = partition_counts[method_names[0]]
    x = np.arange(len(partition_counts))

    qpu_size = qpu_sizes[method_names[0]][0]

    # Plotting
    width = 1 / (len(method_names)+1)  # the width of the bars
    figsize=(width*len(partition_counts)*20, 5)

    # Plot e-bit count vs num_qubits
    plt.figure(figsize=figsize)
    for i, (method, e_bit_count) in enumerate(e_bit_counts.items()):
        offset = width * i
        rects = plt.bar(x + offset, e_bit_count, width, label=method)
        plt.bar_label(rects, padding=3)
    plt.xlabel("Number of QPUs")
    plt.ylabel("Min E-bit Count")
    plt.title(f"E-bit Count vs. Number of {qpu_size}-qubit QPUs")
    plt.xticks(x, partition_counts)
    plt.legend(loc='upper left', ncols=len(method_names))
    plt.legend()
    plt.savefig(folderpath / "bar_chart_e_bit_count_vs_num_qpus.png")
    
    # Plot time vs num_qubits
    plt.figure(figsize=figsize)
    def formatter(f: float):
        if f == 0:
            return "0"
        elif f < 1:
            return "~0"
        else:
            return str(int(f))
    for i, (method, time) in enumerate(times.items()):
        offset = width * i
        rects = plt.bar(x + offset, time, width, label=method)
        plt.bar_label(rects, fmt=formatter, padding=3)
    plt.xlabel("Number of QPUs")
    plt.ylabel("Time (seconds)")
    plt.title(f"Time vs. Number of {qpu_size}-qubit QPUs")
    plt.xticks(x, partition_counts)
    plt.legend(loc='upper left', ncols=len(method_names))
    plt.legend()
    plt.savefig(folderpath / "bar_chart_time_vs_num_qpus.png")

if __name__ == "__main__":
    plot_results()