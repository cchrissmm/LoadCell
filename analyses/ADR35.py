import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from datetime import datetime
import pytz

# Set the working directory to the script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

# Step 1: Find the first CSV in the directory
csv_files = [f for f in os.listdir() if f.endswith('.csv')]
if not csv_files:
    print("No CSV files found.")
    exit()
    
    # Loop over each CSV file
for first_csv in csv_files:
    print(f"Processing file: {first_csv}")

    # Step 2: Read the CSV
    df = pd.read_csv(first_csv)
    
    # Create a datetime object with the GMT time
    gmt_time = datetime(2024, df['GPS_Month'].iloc[0], df['GPS_Day'].iloc[0], 
                    df['GPS_Hours'].iloc[0], df['GPS_Minutes'].iloc[0], df['GPS_Seconds'].iloc[0])

# Set the timezone to GMT
    gmt_time = pytz.timezone('GMT').localize(gmt_time)

# Convert to GMT+11
    local_time = gmt_time.astimezone(pytz.timezone('Etc/GMT-11'))

    # Step 3: Maximum value of LC_Force
    max_lc_force = df['LC_Force'].max()
    print(f"Maximum LC_Force: {max_lc_force}")

    # Prepare the dataframe for subsequent steps
    df['GPS_groundSpeed_m_s'] = df['GPS_groundSpeed'] * (1000 / 3600)  # Convert speed to m/s
    df['delta_speed'] = df['GPS_groundSpeed_m_s'].diff()
    df['delta_time'] = df['time'].diff()
    df['acceleration'] = df['delta_speed'] / df['delta_time']  # Assuming positive values indicate acceleration
    df['acceleration'].fillna(0, inplace=True)
    df['condition'] = (df['LC_Force'] > 30) & (df['GPS_groundSpeed_m_s'] > 2/3.6)  # For highlighting in plot
    
    # Identify start and stop points of the condition
    # Fill NaN values before performing logical operations
    df['condition_shifted'] = df['condition'].shift(1).fillna(False)
    condition_starts = df['condition'] & ~df['condition_shifted']
    condition_stops = ~df['condition'] & df['condition'].shift(1)
    plot_ranges = []

    # Calculate Average Deceleration in the filtered range
    average_deceleration = round(df.loc[df['condition'], 'acceleration'].mean(), 2)
    print(f"Average Deceleration: {average_deceleration} m/s^2")

    # Range of GPS_Heading in the filtered range
    gps_heading_range = round(df.loc[df['condition'], 'GPS_heading'].max() - df.loc[df['condition'], 'GPS_heading'].min(), 2)
    print(f"Max GPS_Heading Deviation: {gps_heading_range}")

    # Transition from LC_Force < 30 to >30 for GPS_Groundspeed
    transition_point = round(df[df['LC_Force'] > 30].index[0] - 1, 2)
    gps_groundspeed_before_transition = df.at[transition_point, 'GPS_groundSpeed'] if transition_point >= 0 else None
    print(f"GPS_Groundspeed before LC_Force > 30 transition: {gps_groundspeed_before_transition}")

    # Define PT1 filter function with improved initialization
    def pt1_filter(input_signal, time_constant, sampling_interval):
        alpha = sampling_interval / (time_constant + sampling_interval)
        output_signal = np.zeros_like(input_signal)
        output_signal[0] = input_signal[0]  # Initialize with the first value of input_signal to avoid initial NaN
        for i in range(1, len(input_signal)):
            output_signal[i] = alpha * input_signal[i] + (1 - alpha) * output_signal[i-1]
        return output_signal

    # Apply PT1 filter to acceleration with a 200ms time constant
    time_constant = 0.5  # Time constant in seconds
    sampling_interval = 1 / 20  # Sampling interval in seconds, based on a sampling rate of 20Hz
    df['filtered_acceleration'] = pt1_filter(df['acceleration'].to_numpy(), time_constant, sampling_interval)

    # Iterate over each start condition index
    for start_index in df[condition_starts].index:
        # Assuming 'time' column exists and is in suitable format
        start_time = df.at[start_index, 'time']
        
        # Find the next stop condition that comes after the current start
        stop_indices = df.index[(df.index > start_index) & condition_stops]
        if not stop_indices.empty:
            stop_index = stop_indices[0]
            stop_time = df.at[stop_index, 'time']
            
            # Add the start and stop times, adjusted by 2 seconds before and after, to the list
            plot_ranges.append((max(start_time - 2, df['time'].min()), min(stop_time + 2, df['time'].max())))
            #print the calculated start and stop times
            print(f"Start time: {start_time}, Stop time: {stop_time}")
            break  # Break the loop after the first iteration
            
    # Initialize df_window to df before the loop
    df_window = df

    # Plot only the identified time ranges
    for start, end in plot_ranges:
        try:
            # Filter the DataFrame for the current time window
            df_window = df[(df['time'] >= start) & (df['time'] <= end)]
        except Exception as e:
            print(f"An error occurred: {e}. Plotting the entire time range.")
            df_window = df  # Use the entire DataFrame
        
    fig, ax1 = plt.subplots(figsize=(6, 5))

    line_width = 0.5  # Set line width

    color = 'tab:red'
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('GPS_Groundspeed (km/h)', color=color)
    ax1.plot(df_window['time'], df_window['GPS_groundSpeed'], color=color, linewidth=line_width)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.fill_between(df_window['time'], df_window['GPS_groundSpeed'], where=df_window['condition'], color='red', alpha=0.3)
    ax1.set_ylim(0, 110)
    
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Pedal Force', color=color)
    ax2.plot(df_window['time'], df_window['LC_Force'], color=color, linewidth=line_width)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1000)
    #ax2.fill_between(df['time'], df['LC_Force'], where=df['condition'], color='blue', alpha=0.3)

    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("axes", 1.2))
    color = 'tab:green'
    ax3.set_ylabel('GPS_Heading (Deg)', color=color)
    ax3.plot(df_window['time'], df_window['GPS_heading'], color=color, linewidth=line_width)
    ax3.tick_params(axis='y', labelcolor=color)
    ax3.set_ylim(0, 360)

    ax4 = ax1.twinx()
    ax4.spines["right"].set_position(("axes", 1.4))  # Adjust position as needed
    color = 'tab:purple'
    ax4.set_ylabel('Acceleration (m/s^2)', color=color)
    ax4.plot(df_window['time'], df_window['filtered_acceleration'], color=color, linestyle='--', linewidth=line_width)
    ax4.tick_params(axis='y', labelcolor=color)
    ax4.set_ylim(-10, 2)

    # Add a legend
    #ax1.legend(loc='upper right')
    
    fig.tight_layout()
    
    plt.subplots_adjust(bottom=0.22, top=0.9)  # Adjust bottom margin
    # Now you can use local_time in your f-string
    metrics_text = f"""Maximum Pedal Force: {max_lc_force} N
    Average Deceleration: {average_deceleration} m/s^2
    GPS_Groundspeed at maneuver begin: {gps_groundspeed_before_transition} km/h
    Date (Local): {local_time.day} / {local_time.month}
    Time (Local): {local_time.hour}:{local_time.minute}"""
                
    plt.figtext(0.01, 0.01, metrics_text, ha="left", fontsize=8)
    
    # Add a footer
    footer_text = "Relativity Engineering Group DAQ1004"
    plt.figtext(0.5, 0.01, footer_text, ha="center", fontsize=6)

    plt.title(first_csv)
    #plt.show()
     # Save the plot as a PNG file with the same base name as the CSV
    output_filename = os.path.splitext(first_csv)[0] + '.png'
    plt.savefig(output_filename, dpi=300)
    plt.close(fig)  # Close the plot window to free memory

print("Processing done for all CSV files.")
