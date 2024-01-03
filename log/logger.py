import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import datetime
import threading
import queue

class SerialLogger:
    def __init__(self, root, buffer_size=1000):
        self.root = root
        self.buffer_size = buffer_size
        self.log_queue = queue.Queue()
        self.running = False
        self.thread = None

        # Set up GUI components
        self.setup_gui()

    def setup_gui(self):
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        self.ports = serial.tools.list_ports.comports()
        self.port_list = [port.device for port in self.ports]

        self.com_port_combo = ttk.Combobox(self.top_frame, values=self.port_list)
        self.com_port_combo.grid(row=0, column=0, padx=10)

        self.start_button = tk.Button(self.top_frame, text="Start", command=self.start_logging)
        self.start_button.grid(row=0, column=1, padx=10)

        self.stop_button = tk.Button(self.top_frame, text="Stop", command=self.stop_logging, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=10)

        self.text_data = tk.Text(self.root, height=15, width=50)
        self.text_data.pack(pady=10)

        self.root.bind('<space>', self.toggle_logging)

    def toggle_logging(self, event):
        if self.running:
            self.stop_logging()
        else:
            self.start_logging()

    def start_logging(self):
        self.selected_port = self.com_port_combo.get()
        if not self.selected_port:
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.thread = threading.Thread(target=self.read_serial)
        self.thread.start()

    def stop_logging(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if self.thread and self.thread.is_alive():
            self.thread.join()

        while not self.log_queue.empty():
            self.write_to_file(self.log_queue.get())

    def read_serial(self):
        with serial.Serial(self.selected_port, 115200, timeout=1) as ser:
            while self.running:
                line = ser.readline().decode('utf-8').strip()
                self.text_data.insert(tk.END, line + '\n')
                self.text_data.see(tk.END)

                if line.startswith('<h>') and '<p>' in line:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_line = f'{timestamp} - {line}\n'
                    self.log_queue.put(log_line)
                    if self.log_queue.qsize() > self.buffer_size:
                        self.log_queue.get()

    def write_to_file(self, line):
        with open("log_file.d97", "a") as file:
            file.write(line)

# Main window
root = tk.Tk()
root.title("Serial Logger")

# Initialize the serial logger
serial_logger = SerialLogger(root)

root.mainloop()
