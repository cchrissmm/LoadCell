import pandas as pd
import os

# Function to convert km/h to m/s
def kph_to_mps(speed_kph):
    return speed_kph * (1000 / 3600)

# Function to calculate acceleration
def calculate_acceleration(ground_speed):
    # Calculate delta time (assuming time intervals are constant)
    delta_time = (ground_speed['time'].diff() / 1000).fillna(0)  # Convert milliseconds to seconds

    # Calculate delta speed (convert km/h to m/s)
    delta_speed = (kph_to_mps(ground_speed['GPS_groundSpeed']) - kph_to_mps(ground_speed['GPS_groundSpeed'].shift(1))).fillna(0)

    # Calculate acceleration (m/s^2)
    acceleration = delta_speed / delta_time

    return acceleration

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Loop through all CSV files in the directory
for file_name in os.listdir(current_directory):
    if file_name.endswith(".csv"):
        file_path = os.path.join(current_directory, file_name)
        output_file_path = os.path.join(current_directory, os.path.splitext(file_name)[0] + "_output.csv")

        # Read the CSV file
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        if 'time' in data.columns and 'GPS_groundSpeed' in data.columns:
            # Calculate acceleration
            data['Acceleration'] = calculate_acceleration(data)

            # Output the modified data to a new CSV file
            data.to_csv(output_file_path, index=False)

            print(f"Acceleration calculation completed for {file_name}. Data saved to {output_file_path}")
        else:
            print(f"Ignoring {file_name}: Required columns not found.")
