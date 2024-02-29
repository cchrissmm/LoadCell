import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

latColumn = 'ICM_az'  # name of column containing lateral acceleration
longColumn = 'ICM_ay'  # name of column containing longitudinal acceleration

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Lists to store lateral and longitudinal acceleration data
all_lateral_g = []
all_longitudinal_g = []

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
        all_lateral_g.extend(data[latColumn])
        all_longitudinal_g.extend(data[longColumn])

    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file

# Create the g-g diagram for all files
plt.figure(figsize=(8, 6))
plt.scatter(all_lateral_g, all_longitudinal_g, alpha=0.5)  # Plot all data points
plt.title('Combined g-g Diagram for All Files')
plt.xlabel('Lateral Acceleration (g)')
plt.ylabel('Longitudinal Acceleration (g)')
plt.grid(True)
plt.axis('equal')  # Ensures equal scaling on both axes

# Optional: Define limits for x and y axes
plt.xlim(-3, 3)
plt.ylim(-3, 3)

# Show the plot
plt.show()
