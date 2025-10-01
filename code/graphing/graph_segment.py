## To run just type "python3 graph_segment.py"
## It's possible that this won't work because lrummu, clockmmu and randmmu file is in a different directory

from lrummu import LruMMU
from clockmmu import ClockMMU
from randmmu import RandMMU
import matplotlib.pyplot as plt

def simulate_with_segmentation(mmu_class, trace_file, frames, num_segments=10):
    PAGE_OFFSET = 12
    with open(trace_file, 'r') as f:
        lines = f.readlines()
    total_events = len(lines)
    segment_size = total_events // num_segments

    mmu = mmu_class(frames)

    results = {"segment": [], "reads": [], "writes": [], "faults": [], "hit_rate": []}

    for i, line in enumerate(lines, start=1):
        addr, op = line.strip().split()
        page = int(addr, 16) >> PAGE_OFFSET

        if op == "R":
            mmu.read_memory(page)
        elif op == "W":
            mmu.write_memory(page)

        if i % segment_size == 0:
            seg_id = i // segment_size
            reads = mmu.get_total_disk_reads()
            writes = mmu.get_total_disk_writes()
            faults = mmu.get_total_page_faults()
            hit_rate = 1 - faults / i

            results["segment"].append(seg_id)
            results["reads"].append(reads)
            results["writes"].append(writes)
            results["faults"].append(faults)
            results["hit_rate"].append(hit_rate)

    return results


def plot_segmentation(results, title, policy_name=None, trace_name=None, num_frame=None, num_seg=None):
    plt.figure(figsize=(10, 6))

    for metric, values in results.items():
        plt.plot(range(1, len(values) + 1), values, label=metric)

    plt.title(title)
    plt.xlabel("Segment")
    plt.ylabel("Metric Value")
    plt.legend()
    plt.grid(True)

    # Make sure policy and trace name are safe for filenames
    policy = policy_name.replace(" ", "_")
    trace = trace_name.replace(".", "_").replace("-", "_")
    filename = f"segmentation_{trace}_{policy}_num_frame_{num_frame}_num_seg_{num_seg}.png"

    plt.savefig(filename)
    print(f"Saved: {filename}")


# Define configs
traces = [
    "../all_trace_file/swim.trace",
    "../all_trace_file/sixpack.trace",
    "../all_trace_file/gcc.trace",
    "../all_trace_file/bzip.trace"
]

policies = {
    "LRU": LruMMU,
    "Clock": ClockMMU,
    "Rand": RandMMU
}

frames = 64
num_segments = 100

# Run segmentation for all traces & policies
for policy_name, policy_class in policies.items():
    for trace in traces:
        results = simulate_with_segmentation(policy_class, trace, frames=frames, num_segments=num_segments)
        trace_name = trace.split("/")[-1]  # extract filename eg "swim.trace"
        title = f"{policy_name} - {trace_name} - Number of frames {frames}"
        plot_segmentation(results, title=title, policy_name=policy_name, trace_name=trace_name, num_frame=frames, num_seg= num_segments)


