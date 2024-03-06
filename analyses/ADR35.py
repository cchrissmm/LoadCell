import os
import pandas as pd
import matplotlib.pyplot as plt

# Set the working directory to the script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

# Step 1: Find the first CSV in the directory
csv_files = [f for f in os.listdir() if f.endswith('.csv')]
if not csv_files:
    print("No CSV files found.")
    exit()

first_csv = csv_files[0]
print(f"Processing file: {first_csv}")  # Print the name of the file being processed

# Step 2: Read the CSV
df = pd.read_csv(first_csv)

# Step 3: Maximum value of LC_Force
max_lc_force = df['LC_Force'].max()
print(f"Maximum LC_Force: {max_lc_force}")

# Prepare the dataframe for subsequent steps
df['GPS_groundSpeed_m_s'] = df['GPS_groundSpeed'] * (1000 / 3600)  # Convert speed to m/s for acceleration calculation
df['delta_speed'] = df['GPS_groundSpeed_m_s'].diff()
df['delta_time'] = df['time'].diff()
df['deceleration'] = df['delta_speed'] / df['delta_time']
df['condition'] = (df['LC_Force'] > 30) & (df['GPS_groundSpeed_m_s'] > 2/3.6)  # For highlighting in plot

# Calculate Average Deceleration in the filtered range
average_deceleration = round(df.loc[df['condition'], 'deceleration'].mean(),2)
print(f"Average Deceleration: {average_deceleration} m/s^2")

# Range of GPS_Heading in the filtered range
gps_heading_range = round(df.loc[df['condition'], 'GPS_heading'].max() - df.loc[df['condition'], 'GPS_heading'].min(),2)
print(f"Max GPS_Heading Deviation: {gps_heading_range}")

# Transition from LC_Force < 30 to >30 for GPS_Groundspeed
transition_point = round(df[df['LC_Force'] > 30].index[0] - 1,2)
gps_groundspeed_before_transition = df.at[transition_point, 'GPS_groundSpeed'] if transition_point >= 0 else None
print(f"GPS_Groundspeed before LC_Force > 30 transition: {gps_groundspeed_before_transition}")

# Plotting
# Plotting
fig, ax1 = plt.subplots(figsize=(10, 8))  # Adjust figure size as needed

color = 'tab:red'
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('GPS_Groundspeed (km/h)', color=color)
ax1.plot(df['time'], df['GPS_groundSpeed'], color=color)
ax1.tick_params(axis='y', labelcolor=color)
ax1.fill_between(df['time'], df['GPS_groundSpeed'], where=df['condition'], color='red', alpha=0.3)

ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('LC_Force', color=color)
ax2.plot(df['time'], df['LC_Force'], color=color)
ax2.tick_params(axis='y', labelcolor=color)
ax2.fill_between(df['time'], df['LC_Force'], where=df['condition'], color='blue', alpha=0.3)

ax3 = ax1.twinx()
ax3.spines["right"].set_position(("axes", 1.2))
color = 'tab:green'
ax3.set_ylabel('GPS_Heading', color=color)
ax3.plot(df['time'], df['GPS_heading'], color=color)
ax3.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.subplots_adjust(bottom=0.2, top=0.9)  # Adjust bottom margin
# Display metrics as text below the plot
metrics_text = f"Maximum Pedal Force: {max_lc_force} N\nAverage Deceleration: {average_deceleration} m/s^2\n" \
               f"GPS_Heading Range: {gps_heading_range} Deg\n" \
               f"GPS_Groundspeed at manoeuver begin: {gps_groundspeed_before_transition} kmh"
#plt.figtext(0.5, -0.1, metrics_text, ha="center", fontsize=10, bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})
plt.figtext(0.5, 0.01, metrics_text, ha="center", fontsize=10, bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})

# Set adjustable property of subplot to 'box' to prevent resizing
ax1.set_adjustable('box')
plt.title('Analyses of ' + first_csv)  # Set the title of the plot
plt.show()

print("Processing done.")  # Indicate completion
