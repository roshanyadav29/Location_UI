import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from serial.tools import list_ports
from datetime import datetime
import os
import sys
from nmea_reader import NMEAHandler
import serial

class NMEAReaderGUI(tk.Tk):
    def __init__(self, nmea_handler):
        super().__init__()
        self.nmea_handler = nmea_handler
        self.title("NMEA Reader")
        self.geometry("1200x600")  # Increased window size
        
        # Create main container
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left frame for controls
        self.left_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.left_frame, weight=1)
        
        # Right frame for map
        self.right_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.right_frame, weight=2)  # Give more weight to the map frame
        
        # Variables
        self.current_thread = None
        self.source_var = tk.StringVar(value="serial")
        
        self.create_widgets()

    def create_widgets(self):
        # Source selection
        self.source_frame = ttk.LabelFrame(self.left_frame, text="Data Source")
        self.source_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Radiobutton(self.source_frame, text="Serial Port", variable=self.source_var, 
                        value="serial", command=self.update_source).pack(side="left", padx=5)
        ttk.Radiobutton(self.source_frame, text="File", variable=self.source_var,
                        value="file", command=self.update_source).pack(side="left", padx=5)
        
        # Serial settings
        self.serial_frame = ttk.LabelFrame(self.left_frame, text="Serial Settings")
        self.serial_frame.pack(padx=5, pady=5, fill="x")
        
        # Center-align the COM port selection
        com_port_label = ttk.Label(self.serial_frame, text="Port:")
        com_port_label.pack(side="left", padx=5)
        self.port_cb = ttk.Combobox(self.serial_frame, values=self.get_com_ports())
        self.port_cb.pack(side="left", padx=5)
        if self.port_cb["values"]:
            self.port_cb.set(self.port_cb["values"][0])
            
        # Center-align the Baud rate selection
        baud_label = ttk.Label(self.serial_frame, text="Baud:")
        baud_label.pack(side="left", padx=5)
        self.baud_cb = ttk.Combobox(self.serial_frame, values=[4800, 9600, 19200, 38400, 115200])
        self.baud_cb.set(115200)
        self.baud_cb.pack(side="left", padx=5)

        # File selection
        self.file_frame = ttk.LabelFrame(self.left_frame, text="File Settings")
        self.file_frame.pack(padx=5, pady=5, fill="x")
        self.file_path = tk.StringVar()
        ttk.Entry(self.file_frame, textvariable=self.file_path, state="readonly").pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(self.file_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)
        
        # Button frame for control buttons
        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(pady=5)
        
        # Start/Stop button
        self.start_button = ttk.Button(button_frame, text="Start", command=self.toggle_reading)
        self.start_button.pack(side="left", padx=5)
        
        # Clear button
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_output)
        self.clear_button.pack(side="left", padx=5)
        
        # Output area in left frame
        self.output = tk.Text(self.left_frame, height=15)
        self.output.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Initial state
        self.file_frame.pack_forget()
        
    def get_com_ports(self):
        return [port.device for port in list_ports.comports()]
        
    def update_source(self):
        if self.source_var.get() == "serial":
            self.file_frame.pack_forget()
            self.serial_frame.pack(after=self.source_frame)
        else:
            self.serial_frame.pack_forget()
            self.file_frame.pack(after=self.source_frame)
            
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            
    def clear_output(self):
        """Clear the output text area"""
        self.output.delete(1.0, tk.END)
        
    def update_output(self, message):
        """Update output with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.output.insert(tk.END, f"[{timestamp}] {message}")
        self.output.see(tk.END)

    def toggle_reading(self):
        if not self.nmea_handler.is_running:
            self.nmea_handler.is_running = True
            self.start_button.config(text="Stop")
            
            # Determine the source of data
            if self.source_var.get() == "file":
                file_path = self.file_path.get()
                if not file_path:
                    self.update_output("Error: No file selected\n")
                    return
                self.start_reading_from_file(file_path)
            else:
                # Use the selected COM port and baud rate
                port_to_read = self.port_cb.get()
                baud_rate = self.baud_cb.get()
                
                if not port_to_read:
                    self.update_output("Error: No COM port selected\n")
                    return
                
                self.start_reading(port_to_read, baud_rate)
        else:
            self.nmea_handler.is_running = False
            self.reset_button()  # Reset button to "Start" when stopped

    def start_reading(self, port_to_read, baud_rate):
        try:
            self.current_thread = threading.Thread(
                target=self.nmea_handler.start_serial_reading,
                args=(port_to_read, baud_rate, self.update_output, self)
            )
            self.current_thread.start()
        except serial.SerialException as e:
            self.update_output(f"Error: Could not open port '{port_to_read}': {e}\n")
            self.nmea_handler.is_running = False  # Reset the running state
            self.reset_button()  # Reset button to "Start"

    def start_reading_from_file(self, file_path):
        try:
            self.current_thread = threading.Thread(
                target=self.nmea_handler.start_file_reading,
                args=(file_path, self.update_output, self)
            )
            self.current_thread.start()
        except Exception as e:
            self.update_output(f"Error: Could not open file '{file_path}': {e}\n")
            self.nmea_handler.is_running = False  # Reset the running state
            self.reset_button()  # Reset button to "Start"

    def reset_button(self):
        """Reset the start/stop button to 'Start'."""
        self.start_button.config(text="Start")