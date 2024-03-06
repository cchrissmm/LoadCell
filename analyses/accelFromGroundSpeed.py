import pandas as pd
import os
from scipy.signal import butter, filtfilt

# Function to convert km/h to m/s
def kph_to_mps(speed_kph):
    return speed_kph * (1000 / 3600)

# Function to calculate acceleration
def calculate_acceleration(ground_speed):
    # Calculate delta time (assuming time intervals are constant)
    delta_time = (ground_speed['time'].diff()).fillna(0)  

    # Calculate delta speed (convert km/h to m/s)
    delta_speed = (kph_to_mps(ground_speed['GPS_groundSpeed']) - kph_to_mps(ground_speed['GPS_groundSpeed'].shift(1))).fillna(0)

    # Calculate acceleration (m/s^2)
    acceleration = delta_speed / delta_time

    return acceleration

# Function to apply Butterworth low-pass filter
def apply_filter(signal, sampling_frequency=20, cutoff_frequency=2):
    nyquist = 0.5 * sampling_frequency
    normalized_cutoff_frequency = cutoff_frequency / nyquist
    b, a = butter(4, normalized_cutoff_frequency, btype='low', analog=False)
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

# Function to process each CSV file
def process_file(file_path):
    # Read the CSV file
    data = pd.read_csv(file_path)

    # Calculate acceleration
    if 'time' in data.columns and 'GPS_groundSpeed' in data.columns:
        data['GPS_Accel_x'] = calculate_acceleration(data)
        data['GPS_Accel_xF'] = apply_filter(data['GPS_Accel_x'])
    else:
        print(f"Ignoring {file_path}: Required columns not found.")

    # Apply filter to ADXL and ICM signals
    for column in data.columns:
        if column.startswith(('ADXL', 'ICM')):
            filtered_column = apply_filter(data[column])
            data[column + 'F'] = filtered_column

    # Write the modified data to a new CSV file
    output_file_path = os.path.splitext(file_path)[0] + "_processed.csv"
    data.to_csv(output_file_path, index=False)
    print(f"Processing completed for {file_path}. Processed data saved to {output_file_path}")

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Process each CSV file in the directory
for file_name in os.listdir(current_directory):
    if file_name.endswith(".csv"):
        file_path = os.path.join(current_directory, file_name)
        process_file(file_path)
