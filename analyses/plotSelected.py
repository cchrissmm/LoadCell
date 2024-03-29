import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from scipy.signal import butter, filtfilt
from datetime import datetime
import pytz
import matplotlib.cm as cm
import numpy as np

# List of signals to plot
signals = ['GPS_groundSpeed','ICM_ax', 'ICM_az', 'ICM_gy','GPS_heading','LC_Force']

# List of signals to be low-pass filtered
filtered_signals = ['ICM_ax', 'ICM_az','ICM_gy']
#filtered_signals = []

# Dictionary of display names for each signal
signal_names = {'GPS_groundSpeed': 'Ground Speed (m/s)','ICM_ax': 'Lateral Acc (m/s^2)', 'ICM_az': 'Long Acc (m/s^2)', 'ICM_gy': 'Yaw Rate (Deg/s)','GPS_heading' : 'Heading (deg)','LC_Force' : 'Brake Pedal Force (N)'}

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(f"{current_dir}/*.csv")

# Define the filter
fs = 20.0  # Sample frequency (Hz)
cutoff = 2.0  # Desired cutoff frequency (Hz)
nyq = 0.5 * fs  # Nyquist Frequency
order = 2  # Order of the filter
normal_cutoff = cutoff / nyq
b, a = butter(order, normal_cutoff, btype='low', analog=False)

# Process each CSV file in the folder
for file_path in csv_files:
    print(f"Reading file: {file_path}")  # Print log message

    try:
        # Load the CSV data
        data = pd.read_csv(file_path)

        # Check if the required columns are present
        for signal in signals:
            if signal not in data.columns:
                raise ValueError(f"Required column {signal} not found")
            
            # Create a datetime object with the GMT time
        gmt_time = datetime(2024, data['GPS_Month'].iloc[0], data['GPS_Day'].iloc[0], 
                    data['GPS_Hours'].iloc[0], data['GPS_Minutes'].iloc[0], data['GPS_Seconds'].iloc[0])

    #  Set the timezone to GMT
        gmt_time = pytz.timezone('GMT').localize(gmt_time)

    # Convert to GMT+11
        local_time = gmt_time.astimezone(pytz.timezone('Etc/GMT-11'))

        # Filter the signals and plot them
        fig, axes = plt.subplots(len(signals), 1, sharex=True, figsize=(6, 8))
        
        # Set the plot title
        fig.suptitle(os.path.basename(file_path), fontsize=14, verticalalignment='top')

        # Create a colormap
        colors = cm.rainbow(np.linspace(0, 1, len(signals)))

        for i, signal in enumerate(signals):
            if signal in filtered_signals:
                filtered_signal = filtfilt(b, a, data[signal])
                # Calculate max and min values
                max_val = filtered_signal.max()
                min_val = filtered_signal.min()
                axes[i].plot(filtered_signal, label=f"{signal_names.get(signal, signal)} (Max: {max_val:.2f}, Min: {min_val:.2f})", linewidth=0.5, color=colors[i])
            else:
                # Calculate max and min values
                max_val = data[signal].max()
                min_val = data[signal].min()
                axes[i].plot(data[signal], label=f"{signal_names.get(signal, signal)} (Max: {max_val:.2f}, Min: {min_val:.2f})", linewidth=0.5, color=colors[i])
            
            # Add a legend to each subplot
            axes[i].legend(fontsize='small')

        # Print the local time at the bottom of the plot
        plt.figtext(0.01, 0.01, f"Mmt Taken At: {str(local_time)}\nRelativity Engineering Group DAQ1004", ha="left", fontsize=8)

        # Save the plot to a file
        base_name = os.path.basename(file_path)
        plot_file_name = f"{os.path.splitext(base_name)[0]}_plot.png"
        plt.savefig(os.path.join(current_dir, plot_file_name))

        # Show the plot
        plt.show()
    except Exception as e:
        print(f"Ignoring file due to error: {e}")  # Log the error and continue to the next file