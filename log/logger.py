from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
import serial.tools.list_ports
import serial
from collections import deque
import csv
import os
import subprocess
import re
import time
import threading

root = Tk()

# Set the size and title of the window
root.geometry("1200x700")
root.title("Relativity Engineering Serial Logger")

# Create the serial connection, text box, and ring buffer variables
ser = None
text_box = None
ring_buffer_size = IntVar(value=1000)
traceFileName = StringVar(value="trace")
ring_buffer = deque(maxlen=ring_buffer_size.get())
logging_enabled = False
log_file = None
csv_writer = None
header_line = None
full_path = None
serial_log_file = None
log_text_box = None
autoscroll_enabled = True
start_time = None
counter = 0
f_start_time = time.time()



# Function to update the status label every second
def update_status_label():
    global minutes, seconds
    while logging_enabled:
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        minutes, seconds = divmod(elapsed_time, 60)  # Convert elapsed time to minutes and seconds
        status_label.config(text=f"Logging running for {int(minutes)} m {int(seconds)} s.")  # Update status label
        time.sleep(1)  # Wait for 1 second

# Function to toggle logging on or off
def toggle_logging():
    global logging_enabled, log_file, csv_writer, header_line, full_path, serial_log_file, start_time
    logging_enabled = not logging_enabled
    if logging_enabled:
        log_button.config(text="Stop Logging", bg="red")
        start_time = time.time()  # Start the timer
        threading.Thread(target=update_status_label).start()  # Start the update_status_label thread
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            log_file_path = os.path.join(script_dir, "serial_log.csv")
            log_file = open(log_file_path, "w", newline="")  # Change 'a' to 'w' to overwrite the file
            full_path = os.path.abspath(log_file.name)
            csv_writer = csv.writer(log_file)
            if header_line is not None:
                csv_writer.writerow(header_line)
                log_file.flush()  # Flush the log file to save it to disk immediately
                
                serial_log_path = os.path.join(script_dir, "serial.log")
                serial_log_file = open(serial_log_path, "w")  # Change 'a' to 'w' to overwrite the file
                full_serial_log_path = os.path.abspath(serial_log_file.name)
                #status_label.config(text=f"Logging started: {full_path}")  # Update status label
                print(f"Serial log file opened successfully at {full_serial_log_path}")  # Debugging print statement
        except Exception as e:
            print(f"Error opening log file: {e}")
            logging_enabled = not logging_enabled
            log_button.config(text="Start Logging", bg="green")
    else:
        log_button.config(text="Start Logging", bg="green")
        if log_file is not None and header_line is not None:
            log_file.close()
            log_file = None
            csv_writer = None
            print("Log file closed successfully.")  # Debugging print statement
            if full_path is not None:  # Check if full_path is not None before updating the status label
                #status_label.config(text=f"Logging stopped: {full_path}")  # Update status label
                status_label.config(text=f"Trace {full_path} saved after {int(minutes)} m {int(seconds)} s.")  # Update status label
                check_csv_file(full_path)
        
        if serial_log_file is not None:
            serial_log_file.close()
            serial_log_file = None
            print("Trace file closed successfully.")  # Debugging print statement


def check_csv_file(file_path):
    temp_file_path = file_path + ".temp"
    num_columns = None

    with open(file_path, 'r') as csv_file, open(temp_file_path, 'w', newline='') as temp_file:
        csv_reader = csv.reader(csv_file)
        csv_writer = csv.writer(temp_file)

        for i, row in enumerate(csv_reader):
            if i == 0:
                num_columns = len(row)
                csv_writer.writerow(row)
                continue
            
            # If the number of columns in the row does not match the number of columns in the header, or if the row contains non-numeric values, add a '#' character to the beginning of the row
            if len(row) != num_columns or not all(re.match(r'^-?\d+\.?\d*$', field) for field in row):
                row = ['#' + field for field in row]
            
            csv_writer.writerow(row)

    os.remove(file_path)
    os.rename(temp_file_path, file_path)

# Function to update the ring buffer size
def update_ring_buffer_size():
    global ring_buffer_size, ring_buffer
    new_size = ring_buffer_size.get()
    ring_buffer = deque(ring_buffer, maxlen=new_size)
    status_label.config(text=f"ringbuffer set to: {new_size} cycles")  # Update status label

# Function to connect to the selected COM port
def connect():
    global ser
    port = port_menu.get()
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        status_label.config(text=f"Connected to {port}")
    except:
        status_label.config(text=f"Failed to connect to {port}")

# Function to disconnect from the current COM port
def disconnect():
    global ser
    if ser is not None:
        ser.close()
        ser = None
        status_label.config(text="Disconnected")

# Function to read data from the serial port and display it in the text box
def read_serial():
    global ser, text_box, ring_buffer, logging_enabled, log_file, csv_writer, header_line, serial_log_file, log_text_box, counter, f_start_time

    if ser is not None and ser.isOpen():
        try:
            line = ser.readline().decode("utf-8")
            ring_buffer.append(line)
            text_box.delete(1.0, END)
            text_box.insert(END, ''.join(ring_buffer))
            if autoscroll_enabled:
                text_box.see(END)

            if line.startswith("HEAD"):
                header_line = line[4:].strip().split(",")
                counter += 1
                if counter >= 100:
                    elapsed_time = time.time() - f_start_time  # Calculate elapsed time
                    frequency = counter / elapsed_time  # Calculate frequency
                    freq_label.config(text=f"Logging running at {int(frequency)} Hz.")
                    counter = 0  # Reset the counter
                    f_start_time = time.time()  # Reset the timer

            if logging_enabled and log_file is not None and csv_writer is not None:
                if line.startswith("DATA"):
                    data_line = line[4:].strip().split(",")
                    csv_writer.writerow(data_line)
                
            if not line.startswith("HEAD") and not line.startswith("DATA"):
                if serial_log_file is not None and logging_enabled:
                    serial_log_file.write(line)
                log_text_box.insert(END, line)
                log_text_box.see(END)

        except:
            pass

    root.after(10, read_serial)

#new save as filename function
def save_trace():
    filename = traceFile_entry.get()
    if not filename:
        return

    # Get a list of all files in the current directory
    files = os.listdir()

    # Find all files that start with the entered filename and end with a number
    matching_files = [file for file in files if re.match(f"{filename}_\d+\.csv", file)]

    # Find the highest number among these files
    highest_number = max((int(file.split('_')[-1].split('.')[0]) for file in matching_files), default=0)

    # Use the next available number for the new file
    full_filename = f"{filename}_{highest_number + 1:04d}.csv"

    try:
        with open(full_path, "r") as original_file:
            content = original_file.read()

        with open(full_filename, "w") as save_as_file:
            save_as_file.write(content)

        status_label.config(text=f"Log file saved as: {full_filename}")
    except Exception as e:
        status_label.config(text=f"Error saving file, probably no trace taken yet")

#autoscrol function
def toggle_autoscroll():
    global autoscroll_enabled
    autoscroll_enabled = not autoscroll_enabled
    if autoscroll_enabled:
        autoscroll_button.config(text="Autoscroll: ON", bg="green")
    else:
        autoscroll_button.config(text="Autoscroll: OFF", bg="red")

def open_uniview(file_path):
    uniview_executable = r'c:\wtools\UNIVW64.exe'  # Replace with the actual path to UNIVW32.EXE
    command = f'"{uniview_executable}" "{file_path}"'
    print(f"open uniview called with: {command}")
    status_label.config(text=f"open uniview called with: {command}")
    subprocess.Popen(command, shell=True)

# Create the label and dropdown menu to select the COM port
Label(root, text="Select COM port:").grid(row=0, column=0, padx=5, pady=5)
ports = serial.tools.list_ports.comports()
port_menu = StringVar(root)
port_menu.set(ports[0].device)
OptionMenu(root, port_menu, *[p.device for p in ports]).grid(row=0, column=1, padx=5, pady=5)

# Create the connect and disconnect buttons
Button(root, text="Connect", command=connect, width=20).grid(row=1, column=0, padx=5, pady=5)
Button(root, text="Disconnect", command=disconnect, width=20).grid(row=1, column=1, padx=5, pady=5)

#create the autoscroll button
autoscroll_button = Button(root, text="Autoscroll: ON", command=toggle_autoscroll, width=20, bg="green")
autoscroll_button.grid(row=1, column=2, padx=5, pady=5)

# Create the start/stop logging button
log_button = Button(root, text="Start Logging(space)", command=toggle_logging, width=20, bg="green")
log_button.grid(row=3, column=0, padx=5, pady=5)
# Bind the spacebar to the start stop logging function
root.bind('<space>', lambda event: toggle_logging())

# Create the launch Uniview button
uniview_button = Button(root, text="Open Uniview(v)", command=lambda: open_uniview(full_path))
uniview_button.grid(row=3, column=1, padx=5, pady=5)
root.bind('v', lambda event: open_uniview(full_path))

# Create the save trace button
Button(root, text="Save Trace(s)", command=save_trace, width=20).grid(row=3, column=2, padx=5, pady=5)
root.bind('s', lambda event: save_trace())

# Create an entry to specify the save filename
Label(root, text="Trace Filename:").grid(row=3, column=3, padx=5, pady=5)
traceFile_entry = Entry(root, textvariable=traceFileName, width=10)
traceFile_entry.grid(row=3, column=4, padx=5, pady=5)

# Create an entry to specify the ring buffer size
Label(root, text="Ring buffer size (#measurments):").grid(row=4, column=0, padx=5, pady=5)
ring_buffer_entry = Entry(root, textvariable=ring_buffer_size, width=10)
ring_buffer_entry.grid(row=4, column=1, padx=5, pady=5)
Button(root, text="Update Ring Buffer Size", command=update_ring_buffer_size, width=25).grid(row=4, column=2, padx=5, pady=5)

# Create the text box to display the serial data stream
text_box = ScrolledText(root, width=120, height=10)
text_box.grid(row=5, column=0, columnspan=5, padx=5, pady=5)

# Create the text box to display the debug data
log_text_box = ScrolledText(root, width=120, height=10)
log_text_box.grid(row=6, column=0, columnspan=5, padx=5, pady=5)

# Create the label to display the status
status_label = Label(root, text="Disconnected", width=100, anchor='w')
status_label.grid(row=7, column=0, columnspan=4, padx=5, pady=5)

# Create the label to display the frequency
freq_label = Label(root, text="Disconnected", width=100, anchor='w')
freq_label.grid(row=8, column=0, columnspan=4, padx=5, pady=5)

# Start reading data from the serial port
read_serial()

# Start the GUI
root.mainloop()
