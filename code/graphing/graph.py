## To run just type "python3 graph.py"
## It needs an edited version of memsum.py, which is now located in the "graphing" folder
## To ensure smooth execution, please check if path need to check (It's under "Run experiments")
## If new parameter is used in the experiment, please also check file's name respectively (It's at the very last lines) 

import subprocess
import matplotlib.pyplot as plt

# Configurations
traces = ["swim.trace", "sixpack.trace", "gcc.trace", "bzip.trace"]
types = ["rand", "lru", "clock"]
cache_sizes = range(1, 100)
memsim_path = "memsim.py"

# Data storage: {type: {trace: [(cache_size, hit_rate), ...]}}
results = {
    t: {trace: {"hit_rate": [], "reads": [], "writes": [], "reads_writes": []} for trace in traces}
    for t in types
}

# Run experiments
for t in types:
    for trace in traces:
        print(f"Running {t} on {trace} ...")
        for cache in cache_sizes:
            cmd = [
                "python3", memsim_path,
                f"../all_trace_file/{trace}",
                str(cache),
                t,
                "quiet"
            ]
            output = subprocess.check_output(cmd, text=True).strip().splitlines()
            last_line = output[-1].strip()

            # Safe parsing
            parts = {}
            for item in last_line.split(","):
                if "=" in item:
                    k, v = item.split("=")
                    parts[k.strip()] = v.strip()

            frames = int(parts["frames"].strip("[]"))
            hit_rate = float(parts["hit_rate"])
            reads = int(parts["reads"])
            writes = int(parts["writes"])
            reads_writes = int(parts["reads_writes"])

            results[t][trace]["hit_rate"].append((frames, hit_rate))
            results[t][trace]["reads"].append((frames, reads))
            results[t][trace]["writes"].append((frames, writes))
            results[t][trace]["reads_writes"].append((frames, reads_writes))


# Plot results per trace and metric
# metrics = ["hit_rate", "reads", "writes", "reads_writes"]
metrics = ["reads_writes"]

for trace in traces:
    for metric in metrics:
        plt.figure(figsize=(10, 6))
        for t in types:
            sizes, values = zip(*results[t][trace][metric])
            plt.plot(sizes, values, label=t)
        print(f"Creating {metric} graph for {trace}...")
        plt.title(f"Cache Performance ({metric}) - {trace}")
        plt.xlabel("Cache Size")
        plt.ylabel(metric.capitalize())
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{trace}_{metric}_100_cache_size.png")
        print(f"{trace} ({metric}) has been saved!")
        plt.show()
