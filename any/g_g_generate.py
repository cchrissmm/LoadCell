import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt

latColumn = 'ICM_az'  # name of column containing lateral acceleration
longColumn = 'ICM_ay'  # name of column containing longitudinal acceleration
max_frequency = 5  # Maximum frequency in Hz
sampling_frequency = 20  # Sampling frequency in Hz

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Lists to store filtered lateral and longitudinal acceleration data
all_filtered_lateral_g = []
all_filtered_longitudinal_g = []

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        if latColumn not in data.columns or longColumn not in data.columns:
            raise ValueError("Required columns not found")

        # Assuming your columns are named 'LateralG' and 'LongitudinalG'
        lateral_g = data[latColumn]
        longitudinal_g = data[longColumn]

        # Design a low-pass Butterworth filter with a cutoff frequency of max_frequency Hz
        nyquist = 0.5 * sampling_frequency
        cutoff_frequency = max_frequency / nyquist
        b, a = butter(4, cutoff_frequency, btype='low', analog=False)

        # Apply the filter to lateral and longitudinal acceleration data
        filtered_lateral_g = filtfilt(b, a, lateral_g)
        filtered_longitudinal_g = filtfilt(b, a, longitudinal_g)

        # Store the filtered data
        all_filtered_lateral_g.extend(filtered_lateral_g)
        all_filtered_longitudinal_g.extend(filtered_longitudinal_g)

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Create the filtered g-g diagram for all files
plt.figure(figsize=(8, 6))
plt.scatter(all_filtered_lateral_g, all_filtered_longitudinal_g, alpha=0.5)  # Plot filtered data points
plt.title('Filtered g-g Diagram for All Files (Max Frequency: 5Hz)')
plt.xlabel('Lateral Acceleration (g)')
plt.ylabel('Longitudinal Acceleration (g)')
plt.grid(True)
plt.axis('equal')  # Ensures equal scaling on both axes

# Show the plot
plt.show()
