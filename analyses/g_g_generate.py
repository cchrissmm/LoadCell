import os
import pandas as pd

# Constants and variable mappings
ag = 9.81  # Acceleration due to gravity in m/s^2
Fstatic = 950 * ag  # Static force in N
mUnsprung = 50  # Unsprung mass in kg
Cy = 9.81
Cx = 6
ay_chassis = 'ICM_ay'
ax_chassis = 'ICM_ax'
az_chassis = 'ICM_az'
ax_wheel = 'ADXL1_x'
ay_wheel = 'ADXL1_y'
az_wheel = 'ADXL1_z'

# Get the current directory path
current_dir = os.path.dirname(os.path.realpath(__file__))

# Find CSV files in the current directory
csv_files = [file for file in os.listdir(current_dir) if file.endswith('.csv')]

# Read the first CSV file found into a DataFrame
if csv_files:
    csv_file = os.path.join(current_dir, csv_files[0])
    df = pd.read_csv(csv_file)
else:
    print("No CSV files found in the directory.")
    exit()

# Define functions for calculating forces
def calculate_F_lateral(row):
    return row[ay_chassis] * Fstatic * (1 / Cy)

def calculate_F_longitudinal(row):
    return row[ax_chassis] * Fstatic * (1 / Cx)

def calculate_F_chassis_vertical(row, Flat, Flong):
    return Flat + Flong + Fstatic

def calculate_F_road_lateral(row):
    return mUnsprung * (row[ax_wheel] - row[ax_chassis])

def calculate_F_road_longitudinal(row):
    return mUnsprung * (row[ay_wheel] - row[ay_chassis])

def calculate_F_road_vertical(row):
    return mUnsprung * (row[az_wheel] - row[az_chassis])

# Create new columns for calculated forces
df['Flat'] = df.apply(calculate_F_lateral, axis=1)
df['Flong'] = df.apply(calculate_F_longitudinal, axis=1)
df['FchassisVert'] = df.apply(lambda row: calculate_F_chassis_vertical(row, row['Flat'], row['Flong']), axis=1)
df['Froadlat'] = df.apply(calculate_F_road_lateral, axis=1)
df['Froadlong'] = df.apply(calculate_F_road_longitudinal, axis=1)
df['Froadvert'] = df.apply(calculate_F_road_vertical, axis=1)

# Now, you can proceed to plot the calculated forces or perform further analysis
