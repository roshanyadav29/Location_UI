import pynmea2

def nmea_to_kml(nmea_data, output_file):
    """
    Convert NMEA data to KML format and save to a file.

    :param nmea_data: List of NMEA sentences (strings).
    :param output_file: Path to the output KML file.
    """
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>NMEA Data</name>
<description>Converted NMEA data to KML</description>
"""
    kml_footer = """
</Document>
</kml>
"""
    kml_placemarks = ""

    for line in nmea_data:
        try:
            msg = pynmea2.parse(line)
            if isinstance(msg, pynmea2.GGA) and msg.latitude and msg.longitude:
                lat = msg.latitude
                lon = msg.longitude
                alt = msg.altitude  # Extract altitude
                kml_placemarks += f"""
<Placemark>
    <name>{msg.timestamp}</name>
    <description>Latitude: {lat}, Longitude: {lon}, Altitude: {alt} m</description>
    <Point>
        <coordinates>{lon},{lat},{alt}</coordinates>
    </Point>
</Placemark>
"""
        except pynmea2.ParseError as e:
            print(f"Parse error: {e} for line: {line}")

    # Write KML to file
    with open(output_file, 'w') as f:
        f.write(kml_header + kml_placemarks + kml_footer)

    print(f"KML file saved as: {output_file}")