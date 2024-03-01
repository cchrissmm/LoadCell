import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Constants and variable mappings
ag = 9.81  # Acceleration due to gravity in m/s^2
Fstatic = 910 * ag  # Static force in N
mUnsprung = 40  # Unsprung mass in kg
Cy = 9.81
Cx = 6
ay_chassis = 'ICM_ax' 
ax_chassis = 'ICM_az'
az_chassis = 'ICM_ay'
ax_wheel = 'ADXL1_z'
ay_wheel = 'ADXL1_x'
az_wheel = 'ADXL1_y'

# Get the current directory path
current_dir = os.path.dirname(os.path.realpath(__file__))

# Find CSV files in the current directory
csv_files = [file for file in os.listdir(current_dir) if file.endswith('.csv')]

# Low-pass filter parameters
cutoff_frequency = 10  # Hz
order = 4

# Function to apply Butterworth low-pass filter
def apply_filter(signal, sampling_frequency=20, cutoff_frequency=5):
    nyquist = 0.5 * sampling_frequency
    normalized_cutoff_frequency = cutoff_frequency / nyquist
    b, a = butter(4, normalized_cutoff_frequency, btype='low', analog=False)
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

# Read the first CSV file found into a DataFrame
if csv_files:
    csv_file = os.path.join(current_dir, csv_files[0])
    df = pd.read_csv(csv_file)
else:
    print("No CSV files found in the directory.")
    exit()

# Low-pass filter the acceleration signals
df[ax_chassis] = apply_filter(df[ax_chassis])
df[ay_chassis] = apply_filter(df[ay_chassis])
df[az_chassis] = apply_filter(df[az_chassis])
df[ax_wheel] = apply_filter(df[ax_wheel])
df[ay_wheel] = apply_filter(df[ay_wheel])
df[az_wheel] = apply_filter(df[az_wheel])

# Align the axes of the acceleration sensors with the global axes
df[ax_chassis] *= 10
df[ay_chassis] *= -10
df[az_chassis] *= -10
df[ax_wheel] *= -10
df[ay_wheel] *= -10
df[az_wheel] *= 10

# Define functions for calculating forces
def calculate_F_lateral(row):
    return row[ay_chassis] * Fstatic * (1 / Cy)

def calculate_F_longitudinal(row):
    return row[ax_chassis] * Fstatic * (1 / Cx)

def calculate_F_chassis_vertical(row, Flat, Flong):  # Adjusted to accept Flat and Flong as arguments
    return Flat + Flong + Fstatic

def calculate_F_road_lateral(row):
    return mUnsprung * (row[ax_wheel] - row[ax_chassis])

def calculate_F_road_longitudinal(row):
    return mUnsprung * (row[ay_wheel] - row[ay_chassis])

def calculate_F_road_vertical(row):
    return mUnsprung * (row[az_wheel] - row[az_chassis])

def calculate_F_Tyre_vertical(row):
    return calculate_F_chassis_vertical(row, row['Flat'], row['Flong']) + calculate_F_road_vertical(row)

def calculate_F_Tyre_lateral(row):
    return calculate_F_lateral(row) + calculate_F_road_lateral(row)

def calculate_F_Tyre_longitudinal(row):
    return calculate_F_longitudinal(row) + calculate_F_road_longitudinal(row)


# Create new columns for calculated forces
df['Flat'] = df.apply(calculate_F_lateral, axis=1)
df['Flong'] = df.apply(calculate_F_longitudinal, axis=1)
df['FchassisVert'] = df.apply(lambda row: calculate_F_chassis_vertical(row, row['Flat'], row['Flong']), axis=1)
df['Froadlat'] = df.apply(calculate_F_road_lateral, axis=1)
df['Froadlong'] = df.apply(calculate_F_road_longitudinal, axis=1)
df['Froadvert'] = df.apply(calculate_F_road_vertical, axis=1)
df['FtyreVert'] = df.apply(calculate_F_Tyre_vertical, axis=1)
df['FtyreLat'] = df.apply(calculate_F_Tyre_lateral, axis=1)
df['FtyreLong'] = df.apply(calculate_F_Tyre_longitudinal, axis=1)

    
# Plot the calculated forces
plt.figure(figsize=(10, 6))

counts, bins, patches = plt.hist(df['FtyreLat'], bins=50, alpha=0.5, label='Ftyrelat')
plt.plot(bins[:-1], counts, linestyle='-', color='black')

counts, bins, patches = plt.hist(df['FtyreLong'], bins=50, alpha=0.5, label='Ftyrelong')
plt.plot(bins[:-1], counts, linestyle='-', color='red')

counts, bins, patches = plt.hist(df['FtyreVert'], bins=50, alpha=0.5, label='Ftyrevert')
plt.plot(bins[:-1], counts, linestyle='-', color='blue')

plt.xlabel('Force')
plt.ylabel('Frequency')
plt.title('Histogram of Forces and Acceleration')
plt.legend()

# Plot 2: Calculation Results
plt.figure(figsize=(10, 6))

plt.plot(df.index, df['Flat'], label='Flat')
plt.plot(df.index, df['Flong'], label='Flong')
plt.plot(df.index, df['FchassisVert'], label='FchassisVert')
plt.plot(df.index, df['Froadlat'], label='Froadlat')
plt.plot(df.index, df['Froadlong'], label='Froadlong')
plt.plot(df.index, df['Froadvert'], label='Froadvert')
plt.plot(df.index, df['ICM_az'], label='az_chassis')
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Calculation Results')
plt.legend()

plt.tight_layout()

plt.show()
