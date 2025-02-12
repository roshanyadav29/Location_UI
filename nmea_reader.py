import io
import pynmea2
import serial
import time
import logging
from nmea_to_kml import nmea_to_kml  # Import the KML function

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NMEAHandler:
    def __init__(self):
        self.is_running = False
        self.map_callback = None
        self.gui = None  # Add a reference to the GUI instance
        self.nmea_data = []  # Store NMEA sentences for KML conversion
        
    def set_map_callback(self, callback):
        """Set callback for map updates"""
        self.map_callback = callback
        logger.debug("Map callback set")

    def process_nmea_message(self, msg):
        """Process NMEA message and extract position data"""
        try:
            if isinstance(msg, pynmea2.GGA):
                logger.debug(f"Processing GGA message: {msg}")
                if msg.latitude and msg.longitude and msg.gps_qual > 0:
                    lat = msg.latitude
                    lon = msg.longitude
                    alt = msg.altitude  # Extract altitude
                    logger.info(f"Valid GGA position: lat={lat}, lon={lon}, alt={alt}")
                    if self.map_callback:
                        self.map_callback(lat, lon)
                    self.nmea_data.append(f"{msg}")  # Store the NMEA sentence for KML
                else:
                    logger.warning("Invalid or no fix in GGA message")
                    
            elif isinstance(msg, pynmea2.RMC):
                logger.debug(f"Processing RMC message: {msg}")
                if msg.latitude and msg.longitude and msg.status == 'A':
                    lat = msg.latitude
                    lon = msg.longitude
                    logger.info(f"Valid RMC position: lat={lat}, lon={lon}")
                    if self.map_callback:
                        self.map_callback(lat, lon)
                    self.nmea_data.append(f"{msg}")  # Store the NMEA sentence for KML
                else:
                    logger.warning("Invalid or no fix in RMC message")

            elif isinstance(msg, pynmea2.GLL):
                logger.debug(f"Processing GLL message: {msg}")
                if msg.latitude and msg.longitude:
                    lat = msg.latitude
                    lon = msg.longitude
                    logger.info(f"Valid GLL position: lat={lat}, lon={lon}")
                    if self.map_callback:
                        self.map_callback(lat, lon)
                    self.nmea_data.append(f"{msg}")  # Store the NMEA sentence for KML
                else:
                    logger.warning("Invalid GLL message")
                
        except AttributeError as e:
            logger.error(f"Attribute error processing message: {e}")
        except Exception as e:
            logger.error(f"Error processing NMEA message: {e}")
    
    def start_serial_reading(self, port, baud_rate, callback, gui):
        """Handle serial port reading"""
        logger.info(f"Starting serial reading on port {port} at {baud_rate} baud")
        self.is_running = True  # Ensure the reading is marked as running
        try:
            ser = serial.Serial(port, int(baud_rate), timeout=5.0)
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            
            while self.is_running:
                try:
                    line = sio.readline()
                    if line:
                        line = line.strip()
                        logger.debug(f"Read line: {line}")
                        try:
                            msg = pynmea2.parse(line)
                            callback(f"{msg}\n")
                            self.process_nmea_message(msg)
                        except pynmea2.ParseError as e:
                            if "could not parse data" not in str(e):
                                logger.error(f'Parse error: {e} for line: {line}')
                                callback(f'Parse error: {e}\n')
                except serial.SerialException as e:
                    logger.error(f'Device error: {e}')
                    callback(f'Device error: {e}\n')
                    break
                    
            # After exiting the loop, create KML from the stored NMEA data
            nmea_to_kml(self.nmea_data, "output.kml")  # Save KML file
            logger.info("KML file created successfully.")
            callback("KML file created successfully.\n")  # Notify GUI about KML creation
            
            # Notify GUI to reset the button
            gui.reset_button()  # Call the reset button method
            ser.close()
            
        except Exception as e:
            logger.error(f"Serial reading error: {e}")
            callback(f"Error: {str(e)}\n")
            
        finally:
            logger.info("Serial reading stopped.")
            
    def start_file_reading(self, file_path, callback, gui):
        """Handle file reading"""
        logger.info(f"Starting file reading from {file_path}")
        try:
            with open(file_path, 'r') as f:
                while self.is_running:
                    line = f.readline()
                    if not line:
                        logger.debug("Reached end of file, stopping...")
                        self.is_running = False  # Stop after processing the file
                        callback("Reached end of file, stopping...\n")
                        break
                    
                    line = line.strip()
                    if line:
                        logger.debug(f"Read line: {line}")
                        try:
                            msg = pynmea2.parse(line)
                            callback(f"{msg}\n")  # Update the GUI with the parsed message
                            self.process_nmea_message(msg)
                            time.sleep(0.05)  # Simulate real-time reading
                        except pynmea2.ParseError as e:
                            logger.error(f'Parse error: {e} for line: {line}')
                            callback(f'Parse error: {e}\n')
            
            # After reading the file, convert NMEA data to KML
            nmea_to_kml(self.nmea_data, "output.kml")  # Save KML file
            logger.info("KML file created successfully.")
            callback("KML file created successfully.\n")  # Notify GUI about KML creation
            
            # Notify GUI to reset the button
            gui.reset_button()  # Call the reset button method

        except Exception as e:
            logger.error(f"File reading error: {e}")
            callback(f"Error: {str(e)}\n") 