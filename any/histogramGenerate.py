import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt
import numpy as np

adxl_z_column = 'ADXL1_z'  # name of column containing ADXL1 z-axis data
max_frequency = 5  # Maximum frequency in Hz
sampling_frequency = 20  # Sampling frequency in Hz

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# List to store filtered ADXL1_z data from all files
all_filtered_adxl_z_data = []

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required column is present
        if adxl_z_column not in data.columns:
            raise ValueError(f"Column '{adxl_z_column}' not found in {file_path}")

        # Extract ADXL1_z data
        adxl_z_data = data[adxl_z_column]

        # Design a low-pass Butterworth filter with a cutoff frequency of max_frequency Hz
        nyquist = 0.5 * sampling_frequency
        cutoff_frequency = max_frequency / nyquist
        b, a = butter(4, cutoff_frequency, btype='low', analog=False)

        # Apply the filter to ADXL1_z data
        filtered_adxl_z_data = filtfilt(b, a, adxl_z_data)

        # Accumulate filtered ADXL1_z data from all files
        all_filtered_adxl_z_data.extend(filtered_adxl_z_data)

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Convert the list of filtered ADXL1_z data arrays into a single array
all_filtered_adxl_z_data = np.array(all_filtered_adxl_z_data)

# Create a histogram for all filtered ADXL1_z data
plt.figure(figsize=(8, 6))
plt.hist(all_filtered_adxl_z_data, bins=50, color='blue', alpha=0.7)
plt.title(f'Histogram of 5Hz Filtered {adxl_z_column} (Combined)')
plt.xlabel(adxl_z_column)
plt.ylabel('Frequency')
plt.grid(True)
plt.show()
