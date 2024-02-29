import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt
import numpy as np

adxl_z_column = 'ADXL1_z'  # name of column containing ADXL1 z-axis data
adxl_y_column = 'ADXL1_y'  # name of column containing ADXL1 y-axis data
adxl_x_column = 'ADXL1_x'  # name of column containing ADXL1 x-axis data
max_frequency = 5  # Maximum frequency in Hz
sampling_frequency = 20  # Sampling frequency in Hz

# Define custom bin ranges for the histograms
bin_ranges = np.linspace(-40, 40, 51)  # Example: from -2 to 2 with 51 bins

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Lists to store filtered ADXL1_z, ADXL1_y, and ADXL1_x data from all files
all_filtered_adxl_z_data = []
all_filtered_adxl_y_data = []
all_filtered_adxl_x_data = []

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        if any(col not in data.columns for col in [adxl_z_column, adxl_y_column, adxl_x_column]):
            raise ValueError(f"One or more required columns not found in {file_path}")

        # Extract ADXL1_z, ADXL1_y, and ADXL1_x data
        adxl_z_data = data[adxl_z_column]
        adxl_y_data = data[adxl_y_column]
        adxl_x_data = data[adxl_x_column]

        # Design a low-pass Butterworth filter with a cutoff frequency of max_frequency Hz
        nyquist = 0.5 * sampling_frequency
        cutoff_frequency = max_frequency / nyquist
        b, a = butter(4, cutoff_frequency, btype='low', analog=False)

        # Apply the filter to ADXL1_z, ADXL1_y, and ADXL1_x data
        filtered_adxl_z_data = filtfilt(b, a, adxl_z_data)
        filtered_adxl_y_data = filtfilt(b, a, adxl_y_data)
        filtered_adxl_x_data = filtfilt(b, a, adxl_x_data)

        # Zero the ADXL1_y data by subtracting its mean
        zeroed_adxl_y_data = filtered_adxl_y_data - np.mean(filtered_adxl_y_data)

        # Accumulate filtered ADXL1_z, zeroed ADXL1_y, and ADXL1_x data from all files
        all_filtered_adxl_z_data.extend(filtered_adxl_z_data)
        all_filtered_adxl_y_data.extend(zeroed_adxl_y_data)
        all_filtered_adxl_x_data.extend(filtered_adxl_x_data)

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Convert the lists of filtered ADXL1_z, zeroed ADXL1_y, and ADXL1_x data arrays into single arrays
all_filtered_adxl_z_data = np.array(all_filtered_adxl_z_data)
all_filtered_adxl_y_data = np.array(all_filtered_adxl_y_data)
all_filtered_adxl_x_data = np.array(all_filtered_adxl_x_data)

# Calculate the 99.5th percentile points
adxl_z_995 = np.percentile(all_filtered_adxl_z_data, 99.5)
adxl_y_995 = np.percentile(all_filtered_adxl_y_data, 99.5)
adxl_x_995 = np.percentile(all_filtered_adxl_x_data, 99.5)

# Create histograms for all filtered ADXL1_z, zeroed ADXL1_y, and ADXL1_x data with custom bin ranges
plt.figure(figsize=(8, 6))

# Plot histograms as lines
plt.plot(bin_ranges[:-1], np.histogram(all_filtered_adxl_z_data, bins=bin_ranges, density=True)[0],
         color='blue', label='ADXL1_z')
plt.plot(bin_ranges[:-1], np.histogram(all_filtered_adxl_y_data, bins=bin_ranges, density=True)[0],
         color='green', label='Zeroed ADXL1_y')
plt.plot(bin_ranges[:-1], np.histogram(all_filtered_adxl_x_data, bins=bin_ranges, density=True)[0],
         color='red', label='ADXL1_x')

# Plot vertical lines at the 99.5th percentile points
plt.axvline(x=adxl_z_995, linestyle='--', color='blue', label=f'99.5th percentile (ADXL1_z): {adxl_z_995:.2f}')
plt.axvline(x=adxl_y_995, linestyle='--', color='green', label=f'99.5th percentile (Zeroed ADXL1_y): {adxl_y_995:.2f}')
plt.axvline(x=adxl_x_995, linestyle='--', color='red', label=f'99.5th percentile (ADXL1_x): {adxl_x_995:.2f}')

plt.title('Line Histograms of 5Hz Filtered ADXL1_z, Zeroed ADXL1_y, and ADXL1_x (Combined)')
plt.xlabel('Acceleration')
plt.ylabel('Density')
plt.legend()
plt.grid(True)
plt.show()
