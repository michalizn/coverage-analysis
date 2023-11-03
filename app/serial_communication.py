import serial
import csv
import time
# commands = ["ATI\r\n", "AT\r\n", "AT+QGPSCFG=\"nmeasrc\",1\r\n", "ATE1V1\r\n", "AT+CPIN?\r\n", "AT+CSQ\r\n", "AT+COPS?\r\n", "AT+CGREG?\r\n", "AT+CGDCONT=1,\"IP\",\"internet.t-mobile.cz\"\r\n", "AT+CGDCONT?\r\n",
#            "AT+CGATT=1\r\n", "AT+CGATT?\r\n", "AT+CGPADDR=1\r\n", "AT+QPING=1,\"seznam.cz\",1,1\r\n", "AT+QENG=\"servingcell\"\r\n", "AT+QGPSGNMEA\r\n", "AT+QGPSLOC\r\n","AT+QGPSEND\r\n"]
# commands = ["AT+CGPS=1\r\n", "AT+CGPS?\r\n", "AT+CGPSINFO\r\n", "ATI\r\n", "ATE1\r\n", "AT+CPIN?\r\n", "AT+CSQ\r\n", "AT+COPS?\r\n", "AT+CGPS=0\r\n"]
meas_data_path = r'C:\Users\Michal\Desktop\Python\5G_module\measured_data'
meas_data = []

# Prepared commands
init_commands = ["ATI\r\n", "AT+CNMP=109\r\n", "ATE1\r\n", "AT+COPS?\r\n"]
meas_commands = ["AT+CCLK?\r\n", "AT+CSQ\r\n", "AT+CPSI?\r\n", "AT+CGPSINFO\r\n"]
end_commands = ["AT+CGPS=0\r\n"]

# Time duration of measurament in seconds
meas_duration = 10 * 1

# Opening of the serial ports
serial_port_AT = serial.Serial('/dev/ttyUSB2', baudrate=115200, timeout=1)
#serial_port_NMEA = serial.Serial('COM28', baudrate=115200, timeout=1)

# Check if the ports are open
if serial_port_AT.is_open:
    print("Serial port opened successfully.")
else:
    print("Failed to open serial port.")
# if serial_port_NMEA.is_open:
#     print("Serial port opened successfully.")
# else:
#     print("Failed to open serial port.")

# Clear any existing data in the serial buffer
print("Clearing input buffers")
serial_port_AT.reset_input_buffer()
# serial_port_NMEA.reset_input_buffer()

# Execute the initial commands
for i in range(len(init_commands)):
    # Send an AT command
    serial_port_AT.write(init_commands[i].encode())
    # Wait for 2s
    time.sleep(0.5)
    # Read the response
    response = serial_port_AT.read_all().decode()
    print("Response:\r\n", response)
    print("\r\n")

# Is GPS ON or OFF? (Start GPS)
serial_port_AT.write("AT+CGPS?\r\n".encode())
# Wait for 2s
time.sleep(2)
# Read the response
response = serial_port_AT.read_all().decode().replace("\r", "").replace("\n", "").replace("OK", "")
if '0' in response:
    serial_port_AT.write("AT+CGPS=1\r\n".encode())
    time.sleep(0.5)
    print(serial_port_AT.read_all().decode())

# Wait 60s to intialize all the functionality of the module
print("Wait for 60s")
time.sleep(60 * 0)

# Get the starting time
start_time = time.time()

# Run the loop for the specified duration
while (time.time() - start_time) < meas_duration:
    temp_data = []
    for command_index in range(len(meas_commands)):
        # Send an AT command
        serial_port_AT.write(meas_commands[command_index].encode())
        # Wait for 0.1s (take sample each second)
        if command_index < (len(meas_commands) - 1):
            time.sleep(0.1)
            # Read the response
            response = serial_port_AT.read_all().decode()
            # Get the starting time
            msg_start_time = time.time()
            max_wait_msg_time = 3
            while True:
                # When there is OK on the end continue
                if "OK" in response:
                    break
                if (time.time() - msg_start_time) < max_wait_msg_time:
                    print("MSG error!")
                    # Clear any existing data in the serial buffer
                    print("Clearing input buffers")
                    serial_port_AT.reset_input_buffer()
                    break
        else:
            # Get the starting time
            gps_start_time = time.time()
            max_wait_gps_time = 3
            while True:
                # Read the response
                response = serial_port_AT.read_all().decode()
                # When there is full message of GPS, get out
                if "+CGPSINFO:" in response:
                    break
                if (time.time() - gps_start_time) > max_wait_gps_time:
                    print("GPS error!")
                    response = "GPSNONE"
                    # Clear any existing data in the serial buffer
                    print("Clearing input buffers")
                    serial_port_AT.reset_input_buffer()
                    break
        if "CCLK" in response and command_index == 0:
            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CCLK?+CCLK: ", "").replace(".0", "")
            response = response.split(',')
            for i in range(len(response)):
                if "+" in response[i]:
                    response[i] = response[i][:response[i].find('+')]
                temp_data.append(response[i])
        elif "CSQ" in response and command_index == 1:
            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CSQ+CSQ: ", "").replace(",", ".").replace(".0", "")
            response = response.split(',')
            for i in range(len(response)):
                try:
                    temp_data.append(float(response[i]))
                except:
                    temp_data.append(float(0.0))
        elif "CPSI" in response and command_index == 2:
            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CPSI?+CPSI: ", "").replace(".0", "")
            response = response.split(',')
            for i in range(len(response)):
                temp_data.append(response[i])
        elif "CGPSINFO" in response and command_index == 3:
            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("+CGPSINFO: ", "").replace(".0", "")
            response = response.split(',')
            for i in range(len(response)):
                temp_data.append(response[i])
        elif "GPSNONE" in response:
            response = ',,,,,,,,,'
            response = response.split(',')
            for i in range(len(response)):
                temp_data.append(response[i])
        else:
            response = None
            # Write the response in list
            # temp_data.append(response.replace("\r", "").replace("\n", "").replace("OK", "").replace("AT+CCLK?+CCLK: ", "").replace("AT+CSQ+CSQ: ", ",").replace("AT+CPSI?+CPSI: ", ",").replace("+CGPSINFO: ", ",").replace("\".0", "\""))
            #temp_data.append(response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CCLK?+CCLK: ", "").replace("AT+CSQ+CSQ: ", "").replace("AT+CPSI?+CPSI: ", "").replace("+CGPSINFO: ", ""))
    if response != None:
        meas_data.append(tuple(temp_data))

# Execute the initial commands
for command_index in range(len(end_commands)):
    # Send an AT command
    serial_port_AT.write(end_commands[command_index].encode())
    # Wait for 2s
    time.sleep(0.5)
    # Read the response
    response = serial_port_AT.read_all().decode()
    print("Response:\r\n", response)
    print("\r\n")

# Close the serial port
serial_port_AT.close()
# serial_port_NMEA.close()

data_path = meas_data_path + '\\' + str(meas_data[0][0]).replace("/", "") + str(meas_data[0][1]).replace(":", "") + '.csv'
# Write each tuple as a line in the file
data = open(data_path, 'w', newline='')
csv_writer = csv.writer(data)
for item in meas_data:
    data_row = []
    for i in range(len(item)):
        data_row.append(item[i])
    csv_writer.writerow(data_row)