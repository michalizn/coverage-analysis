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
bands_czech_republic_4g = ['EUTRAN-BAND1', 'EUTRAN-BAND3', 'EUTRAN-BAND20']

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
                            id='measurement-band',
                            options=bands_czech_republic_4g,
                            placeholder="Select Preferred Measurement Band",
                        ),
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
                        html.P(id="paragraph_id", children=[""]),
                    ],
                    style={'width': '100%', 'margin-bottom': '10px'},
                ),
            ],
            style={'margin': '10px'},
        ),
    ]
)

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
            State("measurement-band", "value")],
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
    ],
    cancel=Input("cancel_button_id", "n_clicks"),
    progress=[Output("progress_bar", "value"), 
              Output("progress_bar", "max"),
              Output("output_console_time", "children")],
    prevent_initial_call=True
)
def update_progress(set_progress, n_clicks, name, duration, band):
    if int(duration) > 0:
        set_progress((str(int(0)), str(int(duration)), f'Start of a Measurement'))

        meas_data_path = r'/home/baranekm/Documents/Python/5G_module/measured_data'

        # Prepared commands
        init_commands = ["ATI\r\n", "ATE1\r\n", "AT+CNMP=38\r\n", "AT+CFUN=1\r\n"]
        meas_commands = ["AT+CCLK?\r\n", "AT+CPSI?\r\n"]

        ports_to_test = ['/dev/ttyUSB2', '/dev/ttyUSB3']

        if band in bands_czech_republic_4g:
            # getting numbers from string
            temp = re.findall(r'\d+', ' '.join(band))
            res = ''.join(map(str, temp))
            init_commands.append("AT+CSYSSEL=\"lte_band\"," + str(res) + "\r\n")
        # Iterate through ports
        STAT = False
        for port in ports_to_test:
            if test_serial_port(port):
                STAT = True
                break
        
        serial_port_AT = serial.Serial(port, baudrate=115200, timeout=1)

        # Check if the ports are open
        if serial_port_AT.is_open:
            set_progress((str(int(0)), str(int(duration)), f'Serial port opened successfully.'))
            print("Serial port opened successfully.")
        else:
            set_progress((str(int(0)), str(int(duration)), f'Failed to open serial port.'))
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
                set_progress((str(int(0)), str(int(duration)), f'Writing init commands: {response}'))
                print("Response:\r\n", response)
                print("\r\n")

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
                csv_writer.writerow(['datetime', 'rsrp', 'rsrq', 'rssi', 'rssnr'])
            # Get the starting time
            start_time = time.time()

            set_progress((str(int(0)), str(int(duration)), f'Measurement file {meas_file_name} created!'))

            meas_timer = 0

            # Run the loop for the specified duration
            while (time.time() - start_time) < int(duration):
                temp_data = []

                for command_index in range(len(meas_commands)):
                    time.sleep(0.1)
                    response = None
                    try:
                        serial_port_AT.reset_input_buffer()
                        # Send an AT command
                        serial_port_AT.write(meas_commands[command_index].encode())
                        # Wait for 0.1s (take sample each second)
                        if command_index < (len(meas_commands)):
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
                        if "CCLK" in response and command_index == 0:
                            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CCLK?+CCLK: ", "").replace(".0", "")
                            response = response.split(',')
                            for i in range(len(response)):
                                if "+" in response[i]:
                                    response[i] = response[i][:response[i].find('+')]
                            temp_data.append(response[0] + ' ' + response[1])
                        elif "CPSI" in response and command_index == 1:
                            response = response.replace("\r", "").replace("\n", "").replace("\"", "").replace("OK", "").replace("AT+CPSI?+CPSI: ", "").replace(".0", "").replace('+CPSI: NR5G_NSA', ',NR5G_NSA')
                            response = response.split(',')
                            try:
                                temp_data.append(response[10])
                                temp_data.append(int(response[11])/100)
                                temp_data.append(int(response[12])/10)
                                temp_data.append(response[13])
                            except:
                                temp_data.append(0)
                                temp_data.append(0)
                                temp_data.append(0)
                                temp_data.append(0)
                        else:
                            response = None
                    except:
                        print("Something went wrong in main loop")

                if response != None:
                    with open(data_path, 'a', newline='') as data:
                        csv_writer = csv.writer(data)
                        csv_writer.writerow(temp_data)

                meas_timer = (time.time() - start_time)
                set_progress((str(int(meas_timer)), str(int(duration)), f''))

            # Close the serial port
            serial_port_AT.close()

        set_progress((str(int(duration)), str(int(duration)), f''))

    return f""

if __name__ == "__main__":
    app.run(debug=True)