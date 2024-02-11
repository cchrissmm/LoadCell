from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import simpledialog
import serial.tools.list_ports
import serial
from collections import deque
import csv
import os
import subprocess
import re
import time
import threading
from queue import Queue

root = Tk()

# Set the size and title of the window
root.geometry("1100x600")
root.title("Relativity Engineering Vehicle Data Logger")

# Create the serial connection, text box, and ring buffer variables
ser = None
text_box = None
ring_buffer_size = IntVar(value=10000)
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
connection_enabled = False

# Queue for thread communication
status_update_queue = Queue()

# Initialize traceFileName with a default filename
traceFileName = StringVar(value="trace")

# Function to update GUI from the queue
def update_gui_from_queue():
    while not status_update_queue.empty():
        message = status_update_queue.get()
        status_label.config(text=message)
        status_update_queue.task_done()
    root.after(1000, update_gui_from_queue)

# Function to update the status label every second using queue
def update_status_label():
    global logging_enabled, start_time, minutes, seconds
    while logging_enabled:
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        status_update_queue.put(f"Logging running for {int(minutes)} m {int(seconds)} s.")
        time.sleep(1)

# Function to toggle logging on or off
def toggle_logging():
    global logging_enabled, log_file, csv_writer, header_line, full_path, serial_log_file, start_time
    logging_enabled = not logging_enabled
    if logging_enabled:
        log_button.config(text="Stop Logging(space)")
        start_time = time.time()
        threading.Thread(target=update_status_label, daemon=True).start()
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
            log_button.config(text="Start Logging")
    else:
        log_button.config(text="Start Logging(space)")
        if log_file is not None and header_line is not None:
            log_file.close()
            log_file = None
            csv_writer = None
            print("Log file closed successfully.")  # Debugging print statement
            if full_path is not None:  # Check if full_path is not None before updating the status label
                #status_label.config(text=f"Logging stopped: {full_path}")  # Update status label
                status_label.config(text=f"Trace {full_path} stopped after {int(minutes)} m {int(seconds)} s.")  # Update status label
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
            #if len(row) != num_columns or not all(re.match(r'^-?\d+\.?\d*$', field) for field in row):
                #row = ['#' + field for field in row]
                #Faultcounter += 1
                #text_box.insert(END, f"Corrupt data row received \n{counter}")
            
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
            line = ser.readline().decode("utf-8").strip()
            #show raw data in box
            #if line:  # Check if the line is not empty
                #text_box.delete(1.0, END)  # Clear the text box
                #text_box.insert(END, line)  # Insert the latest line

            if line.startswith("HEAD"):
                header_line = line[4:].strip().split(",")
                

            if line.startswith("DATA"):
                data_line = line[4:].strip().split(",")
                # Update the live data1 box = velocity
                live_data1_box.delete(1.0, END)
                live_data1_box.insert(END, data_line[1])  # Index 2 corresponds to the third column
                # Update the live data2 box = load cell
                live_data2_box.delete(1.0, END)
                live_data2_box.insert(END, str(data_line[10]))  # Index 2 corresponds to the third column
                # Update the live data2 box = load cell
                live_data3_box.delete(1.0, END)
                live_data3_box.insert(END, str(data_line[14]))  # Index 2 corresponds to the third column
                #GPS Time
                GPSTime_box.delete(1.0, END)
                gps_time = ':'.join(["GPS Time GMT "+ str(data_line[7]), str(data_line[6]), str(data_line[5])])
                GPSTime_box.insert(END, gps_time)  # Index 2 corresponds to the third column
                # GYS X
                GYSX_label.delete(1.0, END)
                GYSX_label.insert(END, "AX: " + str(data_line[17]))  # Index 2 corresponds to the third column
                 # GYS Y
                GYSY_label.delete(1.0, END)
                GYSY_label.insert(END, "AY: " + str(data_line[18]))  # Index 2 corresponds to the third column
                 # GYS Z
                GYSZ_label.delete(1.0, END)
                GYSZ_label.insert(END, "AZ: " + str(data_line[19]))  # Index 2 corresponds to the third column
                
                counter += 1
                if counter >= 60:
                    elapsed_time = time.time() - f_start_time  # Calculate elapsed time
                    frequency = counter / elapsed_time  # Calculate frequency
                    freq_label.config(text=f"Incoming data streaming at {int(frequency)} Hz.")
                    counter = 0  # Reset the counter
                    f_start_time = time.time()  # Reset the timer

                if logging_enabled and log_file is not None and csv_writer is not None:
                    csv_writer.writerow(data_line)
                
            if not line.startswith("HEAD") and not line.startswith("DATA"):
                if serial_log_file is not None and logging_enabled:
                    serial_log_file.write(line + "\n")  # Add a newline character
                log_text_box.insert(END, line + "\n")  # Add the line with a newline to the log text box
                log_text_box.see(END)

        except Exception as e:
            print(f"Error reading serial data: {e}")

        except:
            pass

    root.after(10, read_serial)

#new save as filename function
def save_trace():
    filename = traceFileName.get()
    if not filename:
        return

    # Get a list of all files in the current directory
    files = os.listdir()

    # Find all files that start with the entered filename and end with a number
    matching_files = [file for file in files if re.match(f"{filename}_\\d+\\.csv", file)]

    # Find the highest number among these files
    highest_number = max((int(file.split('_')[-1].split('.')[0]) for file in matching_files), default=0)

    # Use the next available number for the new file
    full_filename = f"{filename}_{highest_number + 1:04d}.csv"

    try:
        with open(full_path, "r") as original_file:
            content = original_file.read()

        with open(full_filename, "w") as save_as_file:
            save_as_file.write(content)

        status_label.config(text=f"Trace saved as: {full_filename}")
    except Exception as e:
        status_label.config(text=f"Error saving trace, probably no trace taken yet")

def open_uniview(file_path):
    uniview_executable = r'c:\wtools\UNIVW64.exe'  # Replace with the actual path to UNIVW32.EXE
    command = f'"{uniview_executable}" "{file_path}"'
    print(f"open uniview called with: {command}")
    status_label.config(text=f"open uniview called with: {command}")
    subprocess.Popen(command, shell=True)

def update_ports(menu):
    ports = serial.tools.list_ports.comports()
    menu.delete(0, 'end')
    for port in ports:
        menu.add_command(label=port.device, command=lambda p=port.device: port_menu.set(p))

def toggle_connection():
    global connection_enabled
    if connection_enabled:
        disconnect()
        connect_button.config(text='Connect', command=toggle_connection)
    else:
        connect()
        connect_button.config(text='Disconnect', command=toggle_connection)
    connection_enabled = not connection_enabled

# Function to send serial data
def send_serial_data(data):
    if ser is not None and ser.isOpen():
        ser.write(data.encode())  # Encode the string to bytes

# Function to open the save file dialog
def set_file():
    filename = simpledialog.askstring("Set FileName", "Enter the filename:")
    if filename is not None:  # If the user didn't cancel the dialog
        traceFileName.set(filename)
        filename_label.config(text=filename)

# Initialize the periodic GUI update
update_gui_from_queue()

# Create the label and dropdown menu to select the COM port
port_menu = StringVar(root, value="Select COM port")
dropdown = Menubutton(root, textvariable=port_menu, relief=RAISED)
dropdown.grid(row=0, column=0, padx=5, pady=5)
menu = Menu(dropdown, tearoff=False)
dropdown.configure(menu=menu)
# Update the ports when the dropdown is opened
dropdown.bind('<Button-1>', lambda event: update_ports(menu))

# Create the connect and disconnect buttons
# Create the toggle button
connect_button = Button(root, text="Connect", command=toggle_connection)
connect_button.grid(row=0, column=1, padx=5, pady=5)

# Create the zero button
send_button = Button(root, text="Zero Load Cell", command=lambda: send_serial_data("<LCZero>"))
send_button.grid(row=0, column=4, padx=5, pady=5, sticky='W')

# Create the 10kg button
send_button = Button(root, text="Set 10Kg Load Cell", command=lambda: send_serial_data("<LC10kg>"))
send_button.grid(row=1, column=4, padx=5, pady=5, sticky='W')

# Create the reset button
send_button = Button(root, text="Reset ESP", command=lambda: send_serial_data("<resetESP>"))
send_button.grid(row=2, column=4, padx=5, pady=5, sticky='W')

# CalGYS Button
send_button = Button(root, text="Cal Event", command=lambda: send_serial_data("<CALGYS>"))
send_button.grid(row=3, column=4, padx=5, pady=5, sticky='W')

# SaveCalGYS Button
send_button = Button(root, text="Save Cal", command=lambda: send_serial_data("<SAVEGYS>"))
send_button.grid(row=4, column=4, padx=5, pady=5, sticky='W')

# Create an entry to specify the ring buffer size
Label(root, text="Ring buffer size #samples").grid(row=1, column=0, padx=5, pady=5)
ring_buffer_entry = Entry(root, textvariable=ring_buffer_size)
ring_buffer_entry.grid(row=1, column=1, padx=5, pady=5)
Button(root, text="Update Ring Buffer Size", command=update_ring_buffer_size).grid(row=1, column=2, padx=5, pady=5)

# Create the text box to display the debug data
log_text_box = ScrolledText(root,font=("default", 10),height = 6, width = 80)
log_text_box.grid(row=3, column=0, columnspan=4, rowspan=3,padx=5, pady=5, sticky='W')

# Create the label to display the status
status_label = Label(root, text="Disconnected",  anchor='w', font=("default", 16))
status_label.grid(row=7, column=0, columnspan=4, padx=5, pady=5, sticky='W')

# Create the label to display the frequency
freq_label = Label(root, text="No data",  anchor='w', font=("default", 16))
freq_label.grid(row=8, column=0, columnspan=4, padx=5, pady=5, sticky='W')

# Create the start/stop logging button
log_button = Button(root, text="Start Logging(space)", command=toggle_logging, font=("default", 14))
log_button.grid(row=9, column=0, padx=5, pady=5)
# Bind the spacebar to the start stop logging function
root.bind('<space>', lambda event: toggle_logging())

# Create the launch Uniview button
uniview_button = Button(root, text="Open Uniview(u)", font=("default", 14), command=lambda: open_uniview(full_path))
uniview_button.grid(row=9, column=1, padx=5, pady=5)
root.bind('u', lambda event: open_uniview(full_path))

# Create the save trace button
Button(root, text="Save Trace(s)", command=save_trace, font=("default", 14)).grid(row=9, column=2, padx=5, pady=5)
root.bind('s', lambda event: save_trace())

# Create a button to open the set file dialog
setFileName_button = Button(root, text="Set FileName", command=set_file, font=("default", 14))
setFileName_button.grid(row=9, column=3, padx=5, pady=5)

# Create a label to display the filename
filename_label = Label(root, text=traceFileName.get(), font=("default", 14))
filename_label.grid(row=9, column=4, padx=5, pady=5)

# Velocity
live_data1_label = Label(root, text="Speed (m/s):", font=("default", 16))
live_data1_label.grid(row=10, column=0, sticky='W')
live_data1_box = Text(root, width=8, height=1,font=("default", 50))
live_data1_box.grid(row=11, column=0, columnspan=2, padx=5, pady=5, sticky='W')

# Pedal
live_data2_label = Label(root, text="Pedal Force (N):", font=("default", 16))
live_data2_label.grid(row=10, column=2, sticky='W')
live_data2_box = Text(root, width=8, height=1,font=("default", 50))
live_data2_box.grid(row=11, column=2, columnspan=2, padx=5, pady=5, sticky='W')

# GPS AX
live_data3_label = Label(root, text="GPS AX:", font=("default", 16))
live_data3_label.grid(row=10, column=4, sticky='W')
live_data3_box = Text(root, width=6, height=1,font=("default", 50))
live_data3_box.grid(row=11, column=4, columnspan=2, padx=5, pady=5, sticky='W')

# GYS X
GYSX_label = Text(root, width=10, height=1,font=("default", 12))
GYSX_label.grid(row=13, column=0, columnspan=1, padx=5, pady=5, sticky='W')

# GYZ Y
GYSY_label = Text(root, width=10, height=1,font=("default", 12))
GYSY_label.grid(row=13, column=1, columnspan=1, padx=5, pady=5, sticky='W')

# GYS Z
GYSZ_label = Text(root, width=10, height=1,font=("default", 12))
GYSZ_label.grid(row=13, column=2, columnspan=1, padx=5, pady=5, sticky='W')

# Time
GPSTime_box = Text(root, width=25, height=1,font=("default", 12))
GPSTime_box.grid(row=13, column=3, columnspan=2, padx=5, pady=5, sticky='W')
# Start reading data from the serial port
read_serial()

# Start the GUI
root.mainloop()
