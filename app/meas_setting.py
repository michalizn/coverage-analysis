import time
import os
import serial
import csv
import time
import re
from datetime import datetime
import dash
from dash import Dash, DiskcacheManager, CeleryManager, Input, Output, State, html, callback, dcc
from dash.exceptions import PreventUpdate
from math import radians, sin, cos, sqrt, atan2
import plotly.graph_objects as go

if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

# Define the 4G and 5G bands in europe
bands_czech_republic_4g = ['EUTRAN-BAND1', 'EUTRAN-BAND3', 'EUTRAN-BAND7', 'EUTRAN-BAND20']
bands_czech_republic_5g = ['NR-BANDn1', 'NR-BANDn3', 'NR-BANDn78', 'NR-BANDn28']

def calculate_distance_between_coordinates(lat1, lon1, lat2, lon2):
    # approximate radius of Earth in kilometers
    R = 6371.0

    # convert degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # calculate the differences of the coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # apply the Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # calculate the distance
    distance = R * c
    return distance

def test_serial_port(port):
    try:
        serial_port_AT = serial.Serial(port, baudrate=115200, timeout=1)
        if serial_port_AT.is_open:
            print(f"Serial port {port} opened successfully.")
            serial_port_AT.reset_input_buffer()
            serial_port_AT.write("AT\r\n".encode())
            time.sleep(2)
            if "OK" in serial_port_AT.read_all().decode():
                print(f"Serial port {port} ready for AT commands.")
                return True
            else:
                raise ValueError
    except Exception as e:
        print(f"Serial port {port} cannot be open: {e}")
        return False
    
app = dash.Dash(__name__, background_callback_manager=background_callback_manager)

server = app.server

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        dcc.Input(
                            id='measurement-name',
                            type='text',
                            placeholder='Measurement Name',
                            style={
                                'width': '100%',
                                'height': '35px',
                            },
                        ),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                html.Div(
                    [
                        dcc.Input(
                            id='measurement-duration',
                            type='text',
                            placeholder='Measurement Duration in seconds',
                            style={
                                'width': '100%',
                                'height': '35px',
                            },
                            persistence=True,
                        ),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id='measurement-technology',
                            options=[
                                {'label': '4G', 'value': '4G'},
                                {'label': '5G', 'value': '5G'},
                            ],
                            multi=True,
                            placeholder="Select Radio Access Technology",
                        ),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                # html.Div(
                #     [
                #         html.Label('Measurement Sample Frequency:'),
                #         dcc.Slider(
                #             id='sample-freq',
                #             min=1,
                #             max=100,
                #             step=1,
                #             value=1,
                #             marks={i: f'{i}' for i in range(0, 100, 5)},
                #             persistence=True,
                #         ),
                #     ],
                #     style={'width': '100%', 'margin-bottom': '10px'},
                # ),
                # html.Div(
                #     [
                #         dcc.Dropdown(
                #             id='measurement-unit',
                #             options=[
                #                 {'label': 'Meters', 'value': 'METERS'},
                #                 {'label': 'Seconds', 'value': 'SECONDS'},
                #             ],
                #             placeholder="Select sampling unit Meters/Seconds",
                #             persistence=True,
                #         ),
                #     ],
                #     style={'width': '100%', 'margin-bottom': '10px'},
                # ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id='measurement-band',
                            options=[],
                            placeholder="Select Preferred Measurement Band",
                        ),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                html.Div(
                    [
                        dcc.Checklist(
                            id='checkbox',
                            options=[
                                {'label': 'Turn off GPS localization', 'value': 'GPS_off'}
                            ],
                        )
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                html.Div(
                    [
                        html.Label('Start the measurement:'),
                        html.Button(
                            id='button_id',
                            children='Start',
                            style={
                                'backgroundColor': 'green',
                                'width': '100%',
                                'height': '50px',
                                'margin-bottom': '10px',
                            },
                        ),
                        html.Button(
                            id='cancel_button_id',
                            children='Stop',
                            style={
                                'backgroundColor': 'red',
                                'width': '100%',
                                'height': '50px',
                            },
                        ),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
                html.Div(
                    [
                        html.Progress(
                            id="progress_bar",
                            value='0',
                            style={
                                'visibility': 'hidden',
                                'width': '100%',
                            },
                        ),
                        html.P(id="output_console_time", children=[""]),
                        html.P(id="output_console_rat", children=[""]),
                        html.P(id="output_console_band", children=[""]),
                        html.P(id="output_console_dl_bw", children=[""]),
                        html.P(id="output_console_ul_bw", children=[""]),
                        html.P(id="output_console_rsrp", children=[""]),
                        html.P(id="output_console_rsrq", children=[""]),
                        html.P(id="output_console_rssi", children=[""]),
                        html.P(id="output_console_rssnr", children=[""]),
                        html.P(id="output_console_lat", children=[""]),
                        html.P(id="output_console_lon", children=[""]),
                        html.P(id="output_console_5g", children=[""]),
                        html.P(id="paragraph_id", children=[""]),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
            ],
            style={'margin': '10px'},
        ),
    ]
)

@callback(
    [Output('measurement-band', 'options'),
     Output('measurement-band', 'disabled')],
    [Input('measurement-technology', 'value')]
)
def update_bands(technology):
    selected = ''
    if technology != None:
        for rat in technology:
            if rat == '4G':
                selected += '4G'
            if rat == '5G':
                selected += '5G'
        if selected == '4G':
            return bands_czech_republic_4g, False
        elif selected == '5G':
            return bands_czech_republic_5g, False
        elif selected == '4G5G' or selected == '5G4G':
            bands_czech_republic_4_and_5g = bands_czech_republic_4g + bands_czech_republic_5g
            return bands_czech_republic_4_and_5g, False
        else:
            return [], True  # Disable dropdown menu if no technology is selected
    else:
        return [], True  # Disable dropdown menu if no technology is selected

# Callback to enable/disable the button based on the input value
@callback(
    [Output('button_id', 'disabled'),
     Output('cancel_button_id', 'disabled')],
    [Input('measurement-duration', 'value')]
)
def enable_button(duration):
    # Check if the input value can be converted to an integer
    try:
        int(duration)
        # If conversion is successful, return False (button enabled)
        return False, True
    except (TypeError, ValueError):
        # If conversion fails, return True (button disabled)
        return True, True

@callback(
    output=Output("paragraph_id", "children"),
    inputs=[Input("button_id", "n_clicks"),
            State("measurement-name", "value"),
            State("measurement-duration", "value"),
            State("measurement-technology", "value"),
            #State("sample-freq", "value"),
            #State("measurement-unit", "value"),
            State("measurement-band", "value"),
            State("checkbox", "value")],
    background=True,
    running=[
        (Output("button_id", "disabled"), True, False),
        (Output("cancel_button_id", "disabled"), False, True),
        (
            Output("paragraph_id", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("progress_bar", "style"),
            {"visibility": "visible", 'width': '100%', 'margin': '10px', 'margin-left': '-0px'},
            {"visibility": "hidden"},
        ),
            (Output("output_console_time", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_rat", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_band", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_dl_bw", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_ul_bw", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_rsrp", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_rsrq", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_rssi", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_rssnr", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_lat", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_lon", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
            (Output("output_console_5g", "style"), {"visibility": "visible", 'textAlign': 'center'}, {"visibility": "hidden"}),
    ],
    cancel=Input("cancel_button_id", "n_clicks"),
    progress=[Output("progress_bar", "value"), 
              Output("progress_bar", "max"),
              Output("output_console_time", "children"),
              Output("output_console_rat", "children"),
              Output("output_console_band", "children"),
              Output("output_console_dl_bw", "children"),
              Output("output_console_ul_bw", "children"),
              Output("output_console_rsrp", "children"),
              Output("output_console_rsrq", "children"),
              Output("output_console_rssi", "children"),
              Output("output_console_rssnr", "children"),
              Output("output_console_lat", "children"),
              Output("output_console_lon", "children"),
              Output("output_console_5g", "children")],
    prevent_initial_call=True
)
def update_progress(set_progress, n_clicks, name, duration, technology, band, gps):
    if int(duration) > 0:
        print(gps)
        if gps == None:
            gps = []
        set_progress((str(int(0)), str(int(duration)), f'Start of a Measurement', f'', f'', f'', f'', 
                                                                f'', f'', f'', f'', f'',
                                                                f'', f''))

        meas_data_path = r'/home/baranekm/Documents/Python/5G_module/measured_data'

        # Prepared commands
        init_commands = ["ATI\r\n", "ATE1\r\n", "AT+CFUN=1\r\n"]
        meas_commands = ["AT+CCLK?\r\n", "AT+COPS?\r\n", "AT+CSQ\r\n", "AT+CPSI?\r\n", "AT+CGPSINFO\r\n"]

        ports_to_test = ['/dev/ttyUSB2', '/dev/ttyUSB3']

        # Check if "4G" is in the list
        if technology != None and len(technology) < 2:
            if "4G" in technology:
                init_commands.append("AT+CNMP=38\r\n")
            # Check if "5G" is in the list
            if "5G" in technology:
                init_commands.append("AT+CNMP=71\r\n")
            else:
                init_commands.append("AT+CNMP=109\r\n")
        else:
            init_commands.append("AT+CNMP=109\r\n") 

        if band in bands_czech_republic_4g and "4G" in technology:
            # getting numbers from string
            temp = re.findall(r'\d+', ' '.join(band))
            res = ''.join(map(str, temp))
            init_commands.append("AT+CSYSSEL=\"lte_band\"," + str(res) + "\r\n")
        if band in bands_czech_republic_5g and "5G" in technology:
            # getting numbers from string
            temp = re.findall(r'\d+', ' '.join(band))
            res = ''.join(map(str, temp))
            init_commands.append("AT+CSYSSEL=\"nsa_nr5g_band\"," + str(res) + "\r\n")

        # Iterate through ports
        STAT = False
        for port in ports_to_test:
            if test_serial_port(port):
                STAT = True
                break
        
        serial_port_AT = serial.Serial(port, baudrate=115200, timeout=1)

        # Check if the ports are open
        if serial_port_AT.is_open:
            set_progress((str(int(0)), str(int(duration)), f'Serial port opened successfully.', f'', f'', f'', f'', 
                                                                f'', f'', f'', f'', f'',
                                                                f'', f''))
            print("Serial port opened successfully.")
        else:
            set_progress((str(int(0)), str(int(duration)), f'Failed to open serial port.', f'', f'', f'', f'', 
                                                                f'', f'', f'', f'', f'',
                                                                f'', f''))
            print("Failed to open serial port.")

        # Clear any existing data in the serial buffer
        print("Clearing input buffers")
        serial_port_AT.reset_input_buffer()

        if STAT:
            # Execute the initial commands
            for i in range(len(init_commands)):
                # Send an AT command
                serial_port_AT.write(init_commands[i].encode())
                # Wait for 2s
                time.sleep(0.5)
                # Read the response
                response = serial_port_AT.read_all().decode()
                set_progress((str(int(0)), str(int(duration)), f'Writing init commands:', f'{response}', f'', f'', f'', 
                                                                f'', f'', f'', f'', f'',
                                                                f'', f''))
                print("Response:\r\n", response)
                print("\r\n")
            
            if 'GPS_off' in gps:
                set_progress((str(int(0)), str(int(duration)), f'GPS localiaztion turned off.', f'', f'', f'', f'', 
                                                                    f'', f'', f'', f'', f'',
                                                                    f'', f''))
            else:
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

                    print("Wait for 60s")
                    # Set the start time
                    wait_start_time = time.time()

                    # Loop to print elapsed time every second
                    while (time.time() - wait_start_time) < 60:
                        elapsed_time = 60 - (time.time() - wait_start_time)
                        set_progress((str(int(0)), str(int(duration)), f'Wait 60s for GPS cold start.', f'{int(elapsed_time)} seconds remaining', f'', f'', f'', 
                                                                    f'', f'', f'', f'', f'',
                                                                    f'', f''))
                        time.sleep(1)  # Wait for 1 second before printing again

            serial_port_AT.close()

            meas_file_name = ''

            if name:
                data_path = meas_data_path + '/' + str(name) + '.csv'
                meas_file_name = name + '.csv'
            else:
                # Get current date and time
                current_datetime = datetime.now()
                date_info = current_datetime.strftime("%Y%m%d")
                time_info = current_datetime.strftime("%H%M%S")
                meas_file_name = str(date_info) + str(time_info) + '.csv'
                data_path = meas_data_path + '/' + str(date_info) + str(time_info) + '.csv'
            with open(data_path, 'w', newline='') as data_file:
                csv_writer = csv.writer(data_file)

            # Get the starting time
            start_time = time.time()

            set_progress((str(int(0)), str(int(duration)), f'Measurement file', f'{meas_file_name}', f'created!', f'', f'', 
                                                                    f'', f'', f'', f'', f'',
                                                                    f'', f''))

            meas_timer = 0

            # Run the loop for the specified duration
            while (time.time() - start_time) < int(duration):
                temp_data = []
                try:
                    for port in ports_to_test:
                        if test_serial_port(port):
                            break
                    serial_port_AT = serial.Serial(port, baudrate=115200, timeout=1)
                except:
                    print("Error with port opening.")

                for command_index in range(len(meas_commands)):
                    time.sleep(0.1)
                    response = None
                    try:
                        serial_port_AT.reset_input_buffer()
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
                            if 'GPS_off' in gps:
                                print('GPS is off.')
                                response = "GPSNONE"
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
                        if "COPS" in response and command_index == 1:
                            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+COPS?+COPS: ", "").replace(".0", "")
                            response = response.split(',')
                            temp_data.append(response[2])
                        elif "CSQ" in response and command_index == 2:
                            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CSQ+CSQ: ", "").replace(",", ".").replace(".0", "")
                            response = response.split(',')
                            for i in range(len(response)):
                                try:
                                    temp_data.append(float(response[i]))
                                except:
                                    temp_data.append(float(0.0))
                        elif "CPSI" in response and command_index == 3:
                            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CPSI?+CPSI: ", "").replace(".0", "").replace('+CPSI: NR5G_NSA', ',NR5G_NSA')
                            response = response.split(',')
                            for i in range(len(response)):
                                temp_data.append(response[i])
                        elif "CGPSINFO" in response and command_index == 4:
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
                    except:
                        print("Something")
                        time.sleep(1)
                if response != None:
                    with open(data_path, 'a', newline='') as data:
                        csv_writer = csv.writer(data)
                        csv_writer.writerow(temp_data)
                        time_msg = f'TIME: {temp_data[0]} - {temp_data[1]}'
                        rat_msg = f'RAT: {temp_data[4]}'
                        band_msg = f'BAND: {temp_data[10]}'
                        dl_bw_msg = f'DL_BW: {temp_data[12]}'
                        ul_bw_msg = f'UL_BW: {temp_data[13]}'
                        rsrp_msg = f'RSRP: {temp_data[14]}'
                        rsrq_msg = f'RSRQ: {int(temp_data[15])/100}'
                        rssi_msg = f'RSSI: {int(temp_data[16])/10}'
                        rssnr_msg = f'RSSNR: {temp_data[17]}'
                        if 'NR5G_NSA' in temp_data:
                            index_5g = temp_data.index('NR5G_NSA')
                            msg5g = f'{temp_data[index_5g:index_5g+7]}'
                            lat_msg = f'LAT: {temp_data[25]}'
                            lon_msg = f'LON: {temp_data[27]}'
                        else:
                            msg5g = f'NO 5G DATA'
                            lat_msg = f'LAT: {temp_data[18]}'
                            lon_msg = f'LON: {temp_data[20]}'
                meas_timer = (time.time() - start_time)

                set_progress((str(int(meas_timer)), str(int(duration)), time_msg, rat_msg, band_msg, dl_bw_msg, ul_bw_msg, 
                                                                        rsrp_msg, rsrq_msg, rssi_msg, rssnr_msg, lat_msg,
                                                                        lon_msg, msg5g))
                
                # Close the serial port
                serial_port_AT.close()

        set_progress((str(int(duration)), str(int(duration)), f'', f'', f'', f'', f'', 
                                                                f'', f'', f'', f'', f'',
                                                                f'', f''))

    return f""

if __name__ == "__main__":
    app.run(debug=True)