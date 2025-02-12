from gui import NMEAReaderGUI
from nmea_reader import NMEAHandler

def main():
    nmea_handler = NMEAHandler()
    app = NMEAReaderGUI(nmea_handler)
    nmea_handler.gui = app  # Pass the GUI instance to the NMEAHandler
    app.mainloop()

if __name__ == "__main__":
    main()