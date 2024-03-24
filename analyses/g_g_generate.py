import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt

latColumn = 'ICM_ax'  # name of column containing lateral acceleration
longColumn = 'ICM_az'  # name of column containing longitudinal acceleration

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Initialize lists to hold the data from all files
lateral_g_all = []
longitudinal_g_all = []

# Define the filter
fs = 20.0  # Sample frequency (Hz)
cutoff = 5.0  # Desired cutoff frequency (Hz)
nyq = 0.5 * fs  # Nyquist Frequency
order = 2  # Order of the filter
normal_cutoff = cutoff / nyq
b, a = butter(order, normal_cutoff, btype='low', analog=False)

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        if latColumn not in data.columns or longColumn not in data.columns:
            raise ValueError("Required columns not found")

        # Filter the data
        lateral_g_filtered = filtfilt(b, a, data[latColumn])
        longitudinal_g_filtered = filtfilt(b, a, data[longColumn])

        # Append the filtered data from this file to the lists
        lateral_g_all.extend(lateral_g_filtered)
        longitudinal_g_all.extend(longitudinal_g_filtered)

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Create the g-g diagram
plt.figure(figsize=(8, 6))
plt.scatter(lateral_g_all, longitudinal_g_all, alpha=0.5)  # Plot data points
plt.title('g-g Diagram')
plt.xlabel('Lateral Acceleration (m/s^2)')
plt.ylabel('Longitudinal Acceleration (m/s^2)')
plt.grid(True)
plt.axis('equal')  # Ensures equal scaling on both axes

# Optional: Define limits for x and y axes
#plt.xlim(-10, 2)
#plt.ylim(-10, 10)

# Save the plot to a file in the same directory as the CSV files
plt.savefig(os.path.join(current_dir, 'g_g_Diagram.png'))

# Show the plot
plt.show()