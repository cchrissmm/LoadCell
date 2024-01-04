import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time 

class SerialLogger:
    def __init__(self, root):
        self.root = root
        self.serial_connected = False
        self.logging_active = False
        self.temp_file_name = "temp_data.txt"
        self.thread = None
        self.start_time = 0  # Add a variable to store the start time of the logging session

        self.setup_gui()

    def setup_gui(self):
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        self.ports = serial.tools.list_ports.comports()
        self.port_list = [port.device for port in self.ports]

        self.com_port_combo = ttk.Combobox(self.top_frame, values=self.port_list)
        self.com_port_combo.grid(row=0, column=0, padx=10)

        self.connect_button = tk.Button(self.top_frame, text="Connect", command=self.connect_serial)
        self.connect_button.grid(row=0, column=1, padx=10)

        self.start_button = tk.Button(self.top_frame, text="Start Logging", state=tk.DISABLED, command=self.start_logging)
        self.start_button.grid(row=0, column=2, padx=10)

        self.stop_button = tk.Button(self.top_frame, text="Stop Logging", state=tk.DISABLED, command=self.stop_logging)
        self.stop_button.grid(row=0, column=3, padx=10)

        self.text_data = tk.Text(self.root, height=15, width=100)
        self.text_data.pack(pady=10)

    def connect_serial(self):
        self.selected_port = self.com_port_combo.get()
        if not self.selected_port:
            return

        try:
            self.serial_port = serial.Serial(self.selected_port, 115200, timeout=1)
            self.serial_connected = True
            self.connect_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.thread = threading.Thread(target=self.read_serial, daemon=True)
            self.thread.start()
        except serial.SerialException as e:
            self.root.after(0, lambda: self.text_data.insert(tk.END, f"Error: {str(e)}\n"))

    def start_logging(self):
        if not self.serial_connected:
            return

        self.clear_temp_file()  # Clear the temp file for a new logging session
        self.logging_active = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        # Record the start time when logging is started
        self.start_time = time.time() * 1000  # Convert seconds to milliseconds

    def stop_logging(self):
        self.logging_active = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def read_serial(self):
        while self.serial_connected:
            try:
                line = self.serial_port.readline().decode('utf-8')
                timestamp = int((time.time() * 1000) - self.start_time)  # Calculate elapsed time in ms
                log_line = f"{timestamp} : {line}"  # Combine timestamp and data
                self.root.after(0, lambda: self.text_data.insert(tk.END, log_line))
                if self.logging_active:
                    with open(self.temp_file_name, "a") as temp_file:
                        temp_file.write(line)
            except serial.SerialException as e:
                self.root.after(0, lambda: self.text_data.insert(tk.END, f"Error: {str(e)}\n"))
                break

    def clear_temp_file(self):
        open(self.temp_file_name, 'w').close()

# Main window
root = tk.Tk()
root.title("Serial Logger")

# Initialize the serial logger
serial_logger = SerialLogger(root)

root.mainloop()
