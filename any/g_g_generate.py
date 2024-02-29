import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt

time_column = 'Time'  # name of column containing time
adxl_z_column = 'ADXL_z'  # name of column containing ADXL z-axis data
max_frequency = 5  # Maximum frequency in Hz
sampling_frequency = 20  # Sampling frequency in Hz

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Lists to store filtered ADXL_z data and other samples
all_filtered_adxl_z_data = []
all_sample_data = []

# Initialize time_data outside the loop
time_data = None

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        if time_column not in data.columns or adxl_z_column not in data.columns:
            raise ValueError("Required columns not found")

        # Extract time and ADXL_z data
        if time_data is None:
            time_data = data[time_column]  # Initialize time_data if not already initialized
        adxl_z_data = data[adxl_z_column]

        # Design a low-pass Butterworth filter with a cutoff frequency of max_frequency Hz
        nyquist = 0.5 * sampling_frequency
        cutoff_frequency = max_frequency / nyquist
        b, a = butter(4, cutoff_frequency, btype='low', analog=False)

        # Apply the filter to ADXL_z data
        filtered_adxl_z_data = filtfilt(b, a, adxl_z_data)

        # Store the filtered ADXL_z data
        all_filtered_adxl_z_data.append(filtered_adxl_z_data)

        # Extract and store sample data
        for i in range(1, 11):  # Assuming samples are named sample1, sample2, ..., sample10
            sample_column = f'sample{i}'
            if sample_column in data.columns:
                all_sample_data.append(data[sample_column])

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Create the plot for filtered ADXL_z data and sample data
plt.figure(figsize=(10, 6))

# Plot filtered ADXL_z data
plt.plot(time_data, all_filtered_adxl_z_data, label='Filtered ADXL_z', color='blue')

# Plot sample data
for i, sample_data in enumerate(all_sample_data, start=1):
    plt.plot(time_data, sample_data, label=f'Sample {i}', alpha=0.7)

plt.title('Filtered ADXL_z and Sample Data')
plt.xlabel('Time')
plt.ylabel('Data')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()
