%matplotlib widget
import os
import numpy as np
import matplotlib.pyplot as plt

# By default we skip the first row, which contains the headers
# By skipping 2 rows, you can disregard the first data-point (0,0) to get a closer look
def plot_trainings(skiprows=1):
    plt.close()
    for filename in os.listdir("training_data"):
        if filename == ".ipynb_checkpoints": continue
        x, y = np.loadtxt("training_data/" + filename, delimiter=',', unpack=True, skiprows=skiprows)
        plt.plot(x,y, label=filename.split('.csv')[0])

    plt.xlabel('Time (s)')
    plt.ylabel('Validation Accuracy')
    plt.title('Training Comparison')
    plt.legend()
    plt.show()
    
plot_trainings()


# 柱状图

plt.bar(x, y, color='green')

# subplot

plt.subplot(1, 2, 1)
plt.plot(x, y)
plt.title('Left Plot')

plt.subplot(1, 2, 2)
plt.scatter(x, y)
plt.title('Right Plot')

plt.show()





*** index select example

import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np

# Data from user input
data = """
num_indices,Triton (heuristic),Triton (atomic_add),Triton (reduce),PyTorch
100000.0,0.140880,0.133152,0.977824,0.315840
200000.0,0.324816,0.312992,1.375984,0.597856
500000.0,2.137216,0.445408,2.112512,1.443072
1000000.0,2.788192,1.142400,2.814432,2.851904
2000000.0,3.728416,1.955840,3.688224,5.682240
4000000.0,5.202736,4.016272,5.096096,11.345824
8000000.0,7.360384,7.533856,7.349088,24.067744
16000000.0,11.442672,16.683472,11.471104,71.931068
24891515.0,15.546688,85.914818,15.293120,133.273758
"""

# Read the data into a pandas DataFrame
df = pd.read_csv(io.StringIO(data))

# Set num_indices as index
df = df.set_index('num_indices')

# Create the plot
plt.style.use('ggplot')
fig, ax = plt.subplots(figsize=(12, 7))

for provider in df.columns:
    ax.plot(df.index, df[provider], marker='o', linestyle='-', label=provider)

# Set titles and labels
ax.set_title('Index Select Performance vs. Number of Indices (D=256)')
ax.set_xlabel('Number of Indices (log scale)')
ax.set_ylabel('Execution Time (ms, log scale)') # Updated Y-axis label
ax.set_xscale('log')
ax.set_yscale('log') # Apply log scale to Y-axis
ax.legend()
ax.grid(True, which="both", ls="--")

# Improve layout
fig.tight_layout()

# Save the plot to a file
output_filename = 'index_select-num_indices-ablation-D256_log_xy.png'
plt.savefig(output_filename)

print(f"Plot saved as {output_filename}")