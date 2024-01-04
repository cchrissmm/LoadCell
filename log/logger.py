import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import datetime
import threading
import queue
import time
import csv
import re

class SerialLogger:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.serial_connected = False
        self.thread = None
        self.messages = []
        self.headers_written = False

        # Set up GUI components
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

        self.start_button = tk.Button(self.top_frame, text="Start Logging", command=self.start_logging, state=tk.DISABLED)
        self.start_button.grid(row=0, column=2, padx=10)

        self.stop_button = tk.Button(self.top_frame, text="Stop Logging", command=self.stop_logging, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=10)

        self.save_as_button = tk.Button(self.top_frame, text="Save As", command=self.save_as)
        self.save_as_button.grid(row=0, column=4, padx=10)

        self.text_data = tk.Text(self.root, height=15, width=50)
        self.text_data.pack(pady=10)

        self.root.bind('<space>', self.toggle_logging)

    def get_buffer_size(self):
        try:
            return int(self.buffer_size_entry.get())
        except ValueError:
            messagebox.showwarning("Warning", "Invalid buffer size, using default value 1000.")
            return 1000

    def connect_serial(self):
        try:
            self.selected_port = self.com_port_combo.get()
            if not self.selected_port:
                messagebox.showerror("Error", "No COM port selected.")
                return

            self.serial_port = serial.Serial(self.selected_port, 115200, timeout=1)
            self.serial_connected = True
            self.start_button.config(state=tk.NORMAL)
            self.connect_button.config(state=tk.DISABLED)
            messagebox.showinfo("Success", "Connected to " + self.selected_port)

            self.thread = threading.Thread(target=self.read_serial)
            self.thread.start()
        except serial.SerialException as e:
            messagebox.showerror("Error", str(e))

    def toggle_logging(self, event):
        if self.running:
            self.stop_logging()
        else:
            self.start_logging()

    def start_logging(self):
        if not self.serial_connected:
            messagebox.showerror("Error", "Not connected to any COM port.")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.last_written_time = time.time()

    def stop_logging(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def read_serial(self):
        while self.serial_connected:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                self.root.after(0, lambda: self.text_data.insert(tk.END, line + '\n'))
                self.root.after(0, lambda: self.text_data.see(tk.END))

                if self.running:
                    self.messages.append(line)
                    current_time = time.time()
                    if current_time - self.last_written_time >= 0.05:  # 50ms
                        self.write_to_csv()
                        self.last_written_time = current_time
            except serial.SerialException as e:
                self.root.after(0, lambda: messagebox.showerror("Serial Error", str(e)))
                break

    def write_to_csv(self):
        if not self.messages:
            return

        with open("log_file.csv", "a", newline='') as file:
            csv_writer = csv.writer(file)
            
            if not self.headers_written:
                headers = [self.parse_header(message) for message in self.messages]
                csv_writer.writerow(headers)
                self.headers_written = True

            payloads = [self.parse_payload(message) for message in self.messages]
            csv_writer.writerow(payloads)
            self.messages.clear()

    def parse_header(self, message):
        header = re.search(r'<h>(.*?)<.h>', message)
        return header.group(1) if header else 'N/A'

    def parse_payload(self, message):
        payload = re.search(r'<p>(.*?)<.p>', message)
        return payload.group(1) if payload else 'N/A'

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                while not self.log_queue.empty():
                    file.write(self.log_queue.get())

# Main window
root = tk.Tk()
root.title("Serial Logger")

# Initialize the serial logger
serial_logger = SerialLogger(root)

root.mainloop()
