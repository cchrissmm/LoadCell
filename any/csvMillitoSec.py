import pandas as pd
import os

# Function to convert milliseconds to seconds and subtract the first time measurement
def convert_time_and_subtract_first(data):
    first_time = data.iloc[0, 0]  # Get the value of the first time measurement
    data.iloc[:, 0] = (data.iloc[:, 0] - first_time) / 1000.0  # Convert milliseconds to seconds and subtract the first time measurement
    return data

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get a list of all CSV files in the directory
csv_files = [file for file in os.listdir(current_dir) if file.endswith(".csv")]

# Process each CSV file in the directory
for input_csv_file in csv_files:
    input_csv_path = os.path.join(current_dir, input_csv_file)
    output_csv_path = os.path.join(current_dir, os.path.splitext(input_csv_file)[0] + "_sec.csv")

    # Read the CSV file into a DataFrame
    data = pd.read_csv(input_csv_path)

    # Check if the DataFrame has a "Time" column
    if "time" in data.columns:
        # Convert time from milliseconds to seconds and subtract the first time measurement
        data = convert_time_and_subtract_first(data)

        # Write the modified data to a new CSV file
        data.to_csv(output_csv_path, index=False)

        print(f"Conversion completed for {input_csv_file}. Data saved to {output_csv_path}")
    else:
        print(f"Ignoring {input_csv_file}: No 'Time' column found.")

