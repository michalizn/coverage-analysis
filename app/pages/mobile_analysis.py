import plotly
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import dash_table
import plotly.express as px
import numpy as np
import os
import pandas as pd
from app import app
import plotly.graph_objects as go
import glob
import time
from math import sin, cos, sqrt, atan2, radians
from math import hypot
import matplotlib.pyplot as plt
from dash import Input, Output, State, no_update
from plotly.validators.scatter.marker import SymbolValidator
from scipy.interpolate import griddata
from scipy.interpolate import LinearNDInterpolator, CloughTocher2DInterpolator
from matplotlib import colors as mpl_colors

dash.register_page(__name__, path='/')

def calculate_cumulative_distance(latitudes, longitudes):
    distance = 0.0

    # iterate over the coordinates
    for i in range(len(latitudes) - 1):
        lat1, lon1 = latitudes[i], longitudes[i]
        lat2, lon2 = latitudes[i+1], longitudes[i+1]

        # calculate the distance between neighboring coordinates
        segment_distance = calculate_distance_between_coordinates(lat1, lon1, lat2, lon2)

        # add the segment distance to the cumulative distance
        distance += segment_distance

    return distance

def all_values_greater_than(lst, value):
    return all(x > value for x in lst)
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
# Define a function to map values to colors based on input column
def map_column_to_color(df, column_name, max_variable):
    if column_name == 'rsrp':
        if max_variable == 'band1_lte_count':
            thresholds = [-90, -120, -140]
        elif max_variable == 'band3_lte_count':
            thresholds = [-90, -120, -140]
        elif max_variable == 'band7_lte_count':
            thresholds = [-95, -125, -145]
        elif max_variable == 'band20_lte_count':
            thresholds = [-80, -110, -130]
        elif max_variable == 'band78_5g_count':
            thresholds = [-90, -110, -130]
        else:
            thresholds = [-90, -120, -140]
        colors = ['lawngreen', 'yellow', 'orange', 'red']
    elif column_name == 'rsrq':
        thresholds = [-10, -15, -20]
        colors = ['lawngreen', 'yellow', 'orange', 'red']
    elif column_name == 'rssi':
        thresholds = [-65, -75, -85]
        colors = ['lawngreen', 'yellow', 'orange', 'red']
    elif column_name == 'rssnr':
        thresholds = [10, 3, 0]
        colors = ['lawngreen', 'yellow', 'orange', 'red']
    else:
        raise ValueError("Invalid column name")

    def map_value_to_color(value):
        for i in range(len(thresholds)):
            if int(value) >= thresholds[i]:
                return colors[i]
        return colors[-1]  # Default color for values below the lowest threshold

    df[f'color_{column_name}'] = df[column_name].apply(map_value_to_color)
# Initialize dataframe of Cells
script_dir = os.path.dirname(__file__).replace('pages', '')
bts_df = pd.read_csv(os.path.join(script_dir, 'data', 'cell_database', 'bts_list.csv'), delimiter=';')
# Formating to display multiple columns in the text while hovering over the points in the map
bts_df['text'] = 'Node place: ' + bts_df['bts_place'].astype(str) + '<br>' + \
                 'Latitude: ' + bts_df['bts_lat'].astype(str) + '<br>' + \
                 'Lontitude: ' + bts_df['bts_lon'].astype(str) + '<br>' + \
                 'Cell ID: ' + bts_df['hex'].astype(str)
# Clean 'hex' column by removing non-numeric characters
bts_df['hex'] = bts_df['hex'].str.replace(r'\D', '', regex=True)
# Convert 'hex' column to numeric, coerce non-numeric values to NaN
bts_df['hex'] = pd.to_numeric(bts_df['hex'], errors='coerce')
# Define the directory where your .txt files are located
data_directory = os.path.join(script_dir, 'data', 'measured_data', 'dynamic')
# Initialize a State variable to store the previous selected file and method
prev_selected_file = None
prev_selected_file_2 = None
prev_selected_method = None
prev_selected_interpolation_data = None
prev_selected_band = None
prev_selected_rat = None
prev_selected_operator = None
prev_filter_rsrp_range = None 
prev_filter_rsrq_range = None
prev_filter_rssi_range = None
prev_filter_rssnr_range = None
# Define column names
meas_column_names = ['date', 'time', 'operator', 'csq', 'rat', 'operation_mode', 'mobile_country_code', 'location_area_code',
                     'cell_id', 'arfcn', 'band', 'downlink_frequency', 'downlink_bandwidth', 'uplink_bandwidth',
                     'rsrp', 'rsrq', 'rssi', 'rssnr', 'latitude', 'ns_indicator', 'longitude', 'ew_ndicator',
                     'date2', 'time2', 'altitude', 'speed', 'course', 'color_rsrp', 'color_rsrq', 'color_rssi',
                     'color_rssnr', 'text']
# Define the 4G and 5G bands in europe
bands_czech_republic_4g = ['EUTRAN-BAND1', 'EUTRAN-BAND3', 'EUTRAN-BAND7', 'EUTRAN-BAND20']
bands_czech_republic_5g = ['NR-BANDn1', 'NR-BANDn3', 'NR-BANDn78', 'NR-BANDn28']
# Define the main dataframe
meas_df = pd.DataFrame(columns=meas_column_names)
# Create the map layout
map_layout = go.Layout(
    mapbox_style='open-street-map',
    #mapbox_style='carto-positron',
    hovermode='closest',
    height=1000,  # Set the height of the map
    #width=1000,    # Set the width of the map
    mapbox=dict(
        center=dict(
        lat=49.1947,
        lon=16.6078
        ),
        zoom=12  # Adjust the initial zoom level as needed
        ),
)
# Create the figure and add the scatter mapbox trace
map_figure = go.Figure(data=[go.Scattermapbox()], layout=map_layout)

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                ], style={'textAlign': 'center'}),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Label('Select the data for proccesing:', style={'fontSize':30, 'textAlign':'center'}),
                        dcc.Dropdown(
                            id='data-selector',
                            options=[
                                {'label': f'Data Set: {file_name}', 'value': file_path}
                                for file_name, file_path in zip([os.path.basename(file_path) for file_path in glob.glob(os.path.join(data_directory, '*.csv'))],
                                                                    glob.glob(os.path.join(data_directory, '*.csv')))
                            ],
                            multi=True,
                            clearable=True,
                            searchable=True,
                        ),
                    ]),
                ]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("OpenStreetMap"),
                    dcc.Graph(id='map', figure=map_figure, className='map'),
                ]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Label('Filtering:', style={'fontSize':30, 'textAlign':'center'}),
                            html.Div([
                                html.Div([
                                    html.Label('Technology (RAT):'),  # Label for the first additional data selector
                                    dcc.Dropdown(
                                    id='rat-selector',
                                    placeholder="Select a Technology (RAT)..."
                                    )
                                ], style={'width': '33%', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label('Selected BAND:'),  # Label for the second additional data selector
                                    dcc.Dropdown(
                                    id='band-selector',
                                    placeholder="Select a BAND..."
                                    )
                                ], style={'width': '33%', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label('Operator (provider):'),  # Label for the third additional data selector
                                    dcc.Dropdown(
                                    id='operator-selector',
                                    placeholder="Select a Operator (provider)..."
                                    )
                                ], style={'width': '33%'}),
                            ], style={'display': 'flex', 'margin': '10px'}),
                        html.Label('Interpolation:', style={'fontSize':30, 'textAlign':'center'}),
                            html.Div([
                                html.Div([
                                    html.Label('Type of interpolation:'),  # Label for the first additional data selector
                                    dcc.Dropdown(
                                    id='interpolation-selector',
                                    placeholder="Select an Interpolation Method..."
                                    )
                                ], style={'width': '33%', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label('Data for interpolation:'),  # Label for the second additional data selector
                                    dcc.Dropdown(
                                    id='interpolation-data-selector',
                                    placeholder="Select a dara for interpolation..."
                                    )
                                ], style={'width': '33%', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label('None:'),  # Label for the third additional data selector
                                    dcc.Dropdown(
                                    id='data-selector-6',
                                    )
                                ], style={'width': '33%', 'display': 'None'}),
                            ], style={'display': 'flex', 'margin': '10px'}
                        ),
                    ]),
                ]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("RSRP"),
                    dcc.Graph(id='rsrp-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.RangeSlider(
                        id='rsrp-filter',
                        min=1,
                        max=100,
                        allowCross=False,
                        tooltip={"always_visible": True},
                    ),
                    html.Button(
                        id='button-filter',
                        children='Filter',
                    ),
                ]),
                dbc.Card([
                    dbc.CardHeader("RSRQ"),
                    dcc.Graph(id='rsrq-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.RangeSlider(
                        id='rsrq-filter',
                        min=1,
                        max=100,
                        allowCross=False,
                        tooltip={"always_visible": True},
                    ),
                    html.Button(
                        id='button-filter',
                        children='Filter',
                    ),
                ]),
                dbc.Card([
                    dbc.CardHeader("RSSI"),
                    dcc.Graph(id='rssi-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.RangeSlider(
                        id='rssi-filter',
                        min=1,
                        max=100,
                        allowCross=False,
                        tooltip={"always_visible": True},
                    ),
                    html.Button(
                        id='button-filter',
                        children='Filter',
                    ),
                ]),
                dbc.Card([
                    dbc.CardHeader("RSSNR"),
                    dcc.Graph(id='rssnr-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.RangeSlider(
                        id='rssnr-filter',
                        min=1,
                        max=100,
                        allowCross=False,
                        tooltip={"always_visible": True},
                    ),
                    html.Button(
                        id='button-filter',
                        children='Filter',
                    ),
                ]),
            ]),
        ]),
    ]),
])

@app.callback(
    [Output('rsrp-chart', 'figure'), 
     Output('rsrq-chart', 'figure'),
     Output('rssi-chart', 'figure'),  
     Output('rssnr-chart', 'figure'), 
     Output('map', 'figure'),
     Output('rsrp-filter', 'min'),
     Output('rsrp-filter', 'max'),
     Output('rsrq-filter', 'min'),
     Output('rsrq-filter', 'max'),
     Output('rssi-filter', 'min'),
     Output('rssi-filter', 'max'),
     Output('rssnr-filter', 'min'),
     Output('rssnr-filter', 'max'),],
    [Input('button-filter', 'n_clicks'),
     Input('data-selector', 'value'), 
     Input('interpolation-selector', 'value'),
     Input('interpolation-data-selector', 'value'),
     Input('band-selector', 'value'),
     Input('rat-selector', 'value'),
     Input('operator-selector', 'value'),
     Input('rsrp-chart', 'clickData'), 
     Input('rsrq-chart', 'clickData'),
     Input('rssi-chart', 'clickData'), 
     Input('rssnr-chart', 'clickData'), 
     Input('map', 'clickData')],
    [State('rsrp-chart', 'figure'), 
     State('rsrq-chart', 'figure'), 
     State('rssnr-chart', 'figure'), 
     State('map', 'figure'),
     State('rsrp-filter', 'value'),
     State('rsrq-filter', 'value'),
     State('rssi-filter', 'value'),
     State('rssnr-filter', 'value'),]
)
def update_charts(click_filter_button, selected_file, selected_method, selected_interpolation_data, selected_band, seleceted_rat, selected_operator, rsrp_click_data, rsrq_click_data, rssi_click_data, rssnr_click_data, map_click_data, rsrp_figure, rsrq_figure, rssnr_figure, map_figure, filter_rsrp_range, filter_rsrq_range, filter_rssi_range, filter_rssnr_range):
    initial_lat = 0
    initial_lon = 0
    max_rsrp_value = 0
    min_rsrp_value = 0
    max_rsrq_value = 0
    min_rsrq_value = 0
    max_rssi_value = 0
    min_rssi_value = 0
    max_rssnr_value = 0
    min_rssnr_value = 0
    global prev_selected_file  # Use the global keyword to update the previous selected file
    global prev_selected_method  # Use the global keyword to update the previous selected method
    global prev_selected_interpolation_data # Use the global keyword to update the previous selected interpolation data
    global prev_selected_band  # Use the global keyword to update the previous selected method
    global prev_selected_rat  # Use the global keyword to update the previous selected method
    global prev_selected_operator  # Use the global keyword to update the previous selected method
    global prev_filter_rsrp_range  # Use the global keyword to update the previous selected method
    global prev_filter_rsrq_range  # Use the global keyword to update the previous selected method
    global prev_filter_rssi_range  # Use the global keyword to update the previous selected method
    global prev_filter_rssnr_range  # Use the global keyword to update the previous selected method
    global meas_df
    if selected_file != prev_selected_file or selected_method != prev_selected_method or selected_interpolation_data != prev_selected_interpolation_data or selected_band != prev_selected_band or seleceted_rat != prev_selected_rat or selected_operator != prev_selected_operator or filter_rsrp_range != prev_filter_rsrp_range or filter_rsrq_range != prev_filter_rsrq_range or filter_rssi_range != prev_filter_rssi_range or filter_rssnr_range != prev_filter_rssnr_range:
        map_figure['data'] = []
        if selected_file != None:
            meas_df = pd.DataFrame(columns=meas_column_names)
            for file in selected_file:
                # Read the measurement .csv file
                temp_meas_df = pd.read_csv(file, header=None,  names=meas_column_names, delimiter=',')
                # Merge the DataFrames on 'cell_id' column
                temp_meas_df = temp_meas_df.merge(bts_df, left_on='cell_id', right_on='hex', how='left')
                # Append the anouther DataFrame to the measurement DataFrame
                meas_df = pd.concat([meas_df, temp_meas_df], ignore_index=True)
            # Perform '/ 100' or '/ 10' operation on the 'rsrq' column to get float values
            meas_df.loc[meas_df['rat'] == 'LTE', 'rsrq'] /= 100
            meas_df.loc[meas_df['rat'] == 'NR5G_NSA', 'rsrq'] /= 10
            # Perform '/ 10' operation on the columns to get float values
            meas_df['rssi'] /= 10
            meas_df.loc[meas_df['rat'] == 'NR5G_NSA', 'rsrp'] /= 10
            meas_df.loc[meas_df['rat'] == 'NR5G_NSA', 'rssnr'] /= 10
            # Perform valiadation of the data and clip the extreme values
            meas_df['rsrp'] = meas_df['rsrp'].clip(lower=-200, upper=-30)
            meas_df['rsrq'] = meas_df['rsrq'].clip(lower=-20, upper=10)
            meas_df['rssi'] = meas_df['rssi'].clip(lower=-150, upper=0)
            meas_df['rssnr'] = meas_df['rssnr'].clip(lower=-15, upper=50)
            max_rsrp_value = meas_df['rsrp'].max()
            min_rsrp_value = meas_df['rsrp'].min()
            max_rsrq_value = meas_df['rsrq'].max()
            min_rsrq_value = meas_df['rsrq'].min()
            max_rssi_value = meas_df['rssi'].max()
            min_rssi_value = meas_df['rssi'].min()
            max_rssnr_value = meas_df['rssnr'].max()
            min_rssnr_value = meas_df['rssnr'].min()
            if filter_rsrp_range or filter_rsrp_range != None:
                meas_df = meas_df[(meas_df['rsrp'] >= filter_rsrp_range[0]) & (meas_df['rsrp'] <= filter_rsrp_range[1])]
            if filter_rsrq_range or filter_rsrq_range != None:
                meas_df = meas_df[(meas_df['rsrq'] >= filter_rsrq_range[0]) & (meas_df['rsrq'] <= filter_rsrq_range[1])]
            if filter_rssi_range or filter_rssi_range != None:
                meas_df = meas_df[(meas_df['rssi'] >= filter_rssi_range[0]) & (meas_df['rssi'] <= filter_rssi_range[1])]
            if filter_rssnr_range or filter_rssnr_range != None:
                meas_df = meas_df[(meas_df['rssnr'] >= filter_rssnr_range[0]) & (meas_df['rssnr'] <= filter_rssnr_range[1])]
            # Get all band values in df
            band1_lte_count = 0
            band3_lte_count = 0
            band7_lte_count = 0
            band20_lte_count = 0
            band78_5g_count = 0
            uniq_rat = meas_df['band'].unique()
            for ind in range(len(uniq_rat)):
                if uniq_rat[ind] == 'EUTRAN-BAND1':
                    band1_lte_count = len(meas_df[meas_df['band'] == uniq_rat[ind]])
                if uniq_rat[ind] == 'EUTRAN-BAND3':
                    band3_lte_count = len(meas_df[meas_df['band'] == uniq_rat[ind]])
                if uniq_rat[ind] == 'EUTRAN-BAND7':
                    band7_lte_count = len(meas_df[meas_df['band'] == uniq_rat[ind]])
                if uniq_rat[ind] == 'EUTRAN-BAND20':
                    band20_lte_count = len(meas_df[meas_df['band'] == uniq_rat[ind]])
                if uniq_rat[ind] == 'NR5G_BAND78':
                    band78_5g_count = len(meas_df[meas_df['band'] == uniq_rat[ind]])
            counts = {
                'band1_lte_count': band1_lte_count,
                'band3_lte_count': band3_lte_count,
                'band7_lte_count': band7_lte_count,
                'band20_lte_count': band20_lte_count,
                'band78_5g_count': band78_5g_count
            }
            max_variable = max(counts, key=counts.get)
            # Map 'rsrp' values to colors
            map_column_to_color(meas_df, 'rsrp', max_variable)
            # Map 'rsrq' values to colors
            map_column_to_color(meas_df, 'rsrq', max_variable)
            try:
                # Map 'rssi' values to colors
                map_column_to_color(meas_df, 'rssi', max_variable)
            except:
                print("5G")
            # Map 'rssnr' values to colors
            map_column_to_color(meas_df, 'rssnr', max_variable)
            # Formating to display multiple columns in the text while hovering over the points in the map
            meas_df['text'] = 'Meausered time: ' + meas_df['time'].astype(str) + ', ' + meas_df['date'].astype(str) + '<br>' + \
                              'CSQ: ' + meas_df['csq'].astype(str) + '<br>' + \
                              'Operator: ' + meas_df['operator'].astype(str) + '<br>' + \
                              'RAT: ' + meas_df['rat'].astype(str) + '<br>' + \
                              'Mobile Country Code: ' + meas_df['mobile_country_code'].astype(str) + '<br>' + \
                              'Location Area Code: ' + meas_df['location_area_code'].astype(str) + '<br>' + \
                              'Cell ID: ' + meas_df['cell_id'].astype(str) + '<br>' + \
                              'ARFCN: ' + meas_df['arfcn'].astype(str) + '<br>' + \
                              'Band: ' + meas_df['band'].astype(str) + '<br>' + \
                              'DL Frequency: ' + meas_df['downlink_frequency'].astype(str) + ' MHz'  + '<br>' + \
                              'DL Bandwidth: ' + meas_df['downlink_bandwidth'].astype(str) + ' MHz'  + '<br>' + \
                              'UL Bandwidth: ' + meas_df['uplink_bandwidth'].astype(str) + ' MHz'  + '<br>' + \
                              'RSRP: ' + meas_df['rsrp'].astype(str) + ' dBm' + '<br>' + \
                              'RSRQ: ' + meas_df['rsrq'].astype(str) + ' dB'  + '<br>' + \
                              'RSSI: ' + meas_df['rssi'].astype(str) + ' dBm'  + '<br>' + \
                              'RSSNR: ' + meas_df['rssnr'].astype(str) + ' dB'
            # Filter the DataFrame based on selected value
            if selected_band != None:
                meas_df = meas_df[meas_df['band'] == selected_band]
            elif seleceted_rat != None:
                meas_df = meas_df[meas_df['rat'] == seleceted_rat]
            elif selected_operator != None:
                meas_df = meas_df[meas_df['operator'] == selected_operator]
            
            # Combine 'date' and 'time' columns into a single datetime column
            meas_df['datetime'] = pd.to_datetime(meas_df['date'] + ' ' + meas_df['time'], format="%y/%m/%d %H:%M:%S")
			# Set 'datetime' as the index
            meas_df.set_index('datetime', inplace=True)

			# Sort the DataFrame by the datetime index
            meas_df.sort_index(inplace=True)
                
            # Initialize the position of which is the map open
            if 0 < len(meas_df):
                initial_lat = float(meas_df['latitude'].iloc[-1])
                initial_lon = float(meas_df['longitude'].iloc[-1])
            else:
                # Brno center location
                initial_lat = 49.1947
                initial_lon = 16.6078
            if selected_method != None:
                grid_x, grid_y = np.mgrid[min(meas_df['latitude']):max(meas_df['latitude']):100j, min(meas_df['longitude']):max(meas_df['longitude']):100j]
                # Define the interpolation method based on the selected method
                if selected_interpolation_data == 'RSRP':
                    if selected_method == 'Linear Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='linear')
                    elif selected_method == 'Nearest-Neighbor Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='nearest')
                    elif selected_method == 'Cubic Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='cubic')
                elif selected_interpolation_data == 'RSRQ':
                    if selected_method == 'Linear Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrq'], (grid_x, grid_y), method='linear')
                    elif selected_method == 'Nearest-Neighbor Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrq'], (grid_x, grid_y), method='nearest')
                    elif selected_method == 'Cubic Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrq'], (grid_x, grid_y), method='cubic')
                elif selected_interpolation_data == 'RSSI':
                    if selected_method == 'Linear Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssi'], (grid_x, grid_y), method='linear')
                    elif selected_method == 'Nearest-Neighbor Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssi'], (grid_x, grid_y), method='nearest')
                    elif selected_method == 'Cubic Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssi'], (grid_x, grid_y), method='cubic')
                elif selected_interpolation_data == 'RSSNR':
                    if selected_method == 'Linear Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssnr'], (grid_x, grid_y), method='linear')
                    elif selected_method == 'Nearest-Neighbor Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssnr'], (grid_x, grid_y), method='nearest')
                    elif selected_method == 'Cubic Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rssnr'], (grid_x, grid_y), method='cubic')
                else:
                    if selected_method == 'Linear Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='linear')
                    elif selected_method == 'Nearest-Neighbor Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='nearest')
                    elif selected_method == 'Cubic Interpolation':
                        grid_z = griddata((meas_df['latitude'], meas_df['longitude']), meas_df['rsrp'], (grid_x, grid_y), method='cubic')
                # Define RSRP thresholds and corresponding colors
                rsrp_thresholds = [-70, -90, -100, -120, -130, -160]
                if max_variable == 'band1_lte_count':
                    rsrp_thresholds = [-90, -100, -120, -130, -140, -160]
                elif max_variable == 'band3_lte_count':
                    rsrp_thresholds = [-90, -100, -120, -130, -140, -160]
                elif max_variable == 'band7_lte_count':
                    rsrp_thresholds = [-90, -105, -125, -135, -145, -165]
                elif max_variable == 'band20_lte_count':
                    rsrp_thresholds = [-80, -95, -110, -120, -130, -140]
                elif max_variable == 'band78_5g_count':
                    rsrp_thresholds = [-85, -90, -95, -100, -105, -110]
                colors = ['green', 'yellowgreen', 'yellow', 'orange', 'red', 'darkred']
                # Assign colors based on RSRP thresholds
                colors_interpolated = []
                opacities_interpolated = []
                for value in grid_z.flatten():
                    color_interpolated = 'white'  # Default color for values outside the defined thresholds
                    opacity_interpolated = 0
                    if value > rsrp_thresholds[0]:
                        color_interpolated = 'green'
                        opacity_interpolated = 1
                    elif value < rsrp_thresholds[-1]:
                        color_interpolated = 'darkred'
                        opacity_interpolated = 1
                    else:
                        for i in range(len(rsrp_thresholds) - 1):
                            if rsrp_thresholds[i] >= value > rsrp_thresholds[i + 1]:
                                color_interpolated = colors[i]
                                opacity_interpolated = 1
                    colors_interpolated.append(color_interpolated)
                    opacities_interpolated.append(opacity_interpolated)
            # Create Scattermapbox trace for measured RSRP points
            scatter_mapbox_trace_rsrp = go.Scattermapbox(
                lat=meas_df['latitude'],
                lon=meas_df['longitude'],
                #mode='markers+lines',
                mode='markers',
                marker=dict(size=10, symbol="circle", color=meas_df['color_rsrp'], opacity=1, colorscale='Viridis'),
                #line=dict(width=2, color='grey'),
                text=meas_df['text'],
                hoverinfo='text',
                name='Measured RSRP Points'
            )
            # Create Scattermapbox trace for measured RSRQ points
            scatter_mapbox_trace_rsrq = go.Scattermapbox(
                lat=meas_df['latitude'],
                lon=meas_df['longitude'],
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=meas_df['color_rsrq'], opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=meas_df['text'],
                hoverinfo='text',
                name='Measured RSRQ Points',
                visible='legendonly'  # Set visibility to legendonly by default
            )
            # Create Scattermapbox trace for measured RSSNR points
            scatter_mapbox_trace_rssi = go.Scattermapbox(
                lat=meas_df['latitude'],
                lon=meas_df['longitude'],
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=meas_df['color_rssi'], opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=meas_df['text'],
                hoverinfo='text',
                name='Measured RSSI Points',
                visible='legendonly'  # Set visibility to legendonly by default
            )
            # Create Scattermapbox trace for measured RSSNR points
            scatter_mapbox_trace_rssnr = go.Scattermapbox(
                lat=meas_df['latitude'],
                lon=meas_df['longitude'],
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=meas_df['color_rssnr'], opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=meas_df['text'],
                hoverinfo='text',
                name='Measured RSSNR Points',
                visible='legendonly'  # Set visibility to legendonly by default
            )
            # Create Scattermapbox trace for Cell points
            scatter_mapbox_trace_cells = go.Scattermapbox(
                lat=bts_df['bts_lat'],
                lon=bts_df['bts_lon'],
                mode='markers',
                marker=dict(size=20, symbol="circle", color='black', opacity=0.2),
                text=bts_df['text'],
                hoverinfo='text',
                name='Cell towers',
                visible='legendonly'  # Set visibility to legendonly by default
            )
            if selected_method != None:
                # Create Scattermapbox trace for interpolated RSRP points
                scatter_mapbox_trace_interpolated_rsrp = go.Scattermapbox(
                    lat=grid_x.flatten(),
                    lon=grid_y.flatten(),
                    mode='markers',
                    marker=dict(size=10, color=colors_interpolated, opacity=opacities_interpolated),
                    hoverinfo='none',
                    #text=grid_z.flatten(),
                    selectedpoints=[],  # Disable click actions on these points
                    name='Interpolated RSRP Points',
                    visible='legendonly'  # Set visibility to legendonly by default
                )
            # Create the map layout
            map_layout = go.Layout(
                mapbox_style='open-street-map',
                hovermode='closest',
                height=1000,  # Set the height of the map
                #width=1000,    # Set the width of the map
                mapbox=dict(
                    center=dict(
                        lat=initial_lat,
                        lon=initial_lon
                    ),
                    zoom=12  # Adjust the initial zoom level as needed
                ),
                legend=dict(x=0, y=-0.1)  # Set x and y coordinates to position the legend at the bottom
            )
            if selected_method != None:
                # Create the figure and add the scatter mapbox trace
                map_figure = go.Figure(data=[scatter_mapbox_trace_rsrp, scatter_mapbox_trace_rsrq, 
                                            scatter_mapbox_trace_rssi, scatter_mapbox_trace_rssnr, 
                                            scatter_mapbox_trace_cells, scatter_mapbox_trace_interpolated_rsrp], layout=map_layout)
            else:
                # Create the figure and add the scatter mapbox trace
                map_figure = go.Figure(data=[scatter_mapbox_trace_rsrp, scatter_mapbox_trace_rsrq, 
                                            scatter_mapbox_trace_rssi, scatter_mapbox_trace_rssnr, 
                                            scatter_mapbox_trace_cells], layout=map_layout)
            prev_selected_file = selected_file  # Update the previous selected file
            prev_selected_method = selected_method  # Update the previous selected method
            prev_selected_interpolation_data = selected_interpolation_data # Update the previous selected interpolation data
            prev_selected_band = selected_band # Update the previous selected band
            prev_selected_rat = seleceted_rat # Update the previous selected rat
            prev_selected_operator = selected_operator # Update the previous selected operator
            prev_filter_rsrp_range = filter_rsrp_range
            prev_filter_rsrq_range = filter_rsrq_range
            prev_filter_rssi_range = filter_rssi_range
            prev_filter_rssnr_range = filter_rssnr_range
    # Use dash.callback_context to determine which input triggered the callback
    ctx = dash.callback_context
    # Create a list to hold marker colors and opacity
    marker_colors = ['blue'] * len(meas_df)  # Initialize with the original color
    marker_opacity = [0.5] * len(meas_df)  # Initialize with the original opacity
    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'rsrp-chart' or trigger_id == 'rsrq-chart' or trigger_id == 'rssi-chart' or trigger_id == 'rssnr-chart':
            if trigger_id == 'rsrp-chart':
                index = rsrp_click_data['points'][0]['pointIndex']
            elif trigger_id == 'rsrq-chart':
                index = rsrq_click_data['points'][0]['pointIndex']
            elif trigger_id == 'rssi-chart':
                index = rssi_click_data['points'][0]['pointIndex']
            elif trigger_id == 'rssnr-chart':
                index = rssnr_click_data['points'][0]['pointIndex']
            else:
                index = 0
            # Highlight the selected point by changing its marker color
            if index <= len(meas_df):
                marker_colors[index] = 'red'  # Change the color of the selected point
                marker_opacity[index] = 1
                # lat = latid_rsrp[index]
                # lon = lontid_rsrp[index]
                lat = meas_df['latitude'].iloc[index]
                lon = meas_df['longitude'].iloc[index]
            lat_bts = 0
            lon_bts = 0  
            # Logic for finding lat_bts and lon_bts
            matching_row = meas_df.loc[meas_df['latitude'] == lat]
            lat_bts = matching_row['bts_lat'].values[0]
            lon_bts = matching_row['bts_lon'].values[0]  
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    if 'lat' in trace and 'lon' in trace and trace['mode'] == 'lines':
                        to_remove.append(i)                 
                for i in reversed(to_remove):
                    map_figure['data'].pop(i)  
                # Create and append the new line_trace
                line_trace = go.Scattermapbox(
                    lat=[lat, lat_bts],
                    lon=[lon, lon_bts],
                    mode='lines',
                    line=dict(width=2, color='darkblue'),
                    hoverinfo='none',
                    name="Connection line - distance: "  + str(round(calculate_distance_between_coordinates(lat, lon, lat_bts, lon_bts), 2)) + " km"
                )
                map_figure['data'].append(line_trace)
                #map_figure.add_trace(line_trace)            
        elif trigger_id == 'map':
            index = map_click_data['points'][0]['pointIndex']
            # Highlight the selected point by changing its marker color
            if index <= len(meas_df):
                marker_colors[index] = 'red'  # Change the color of the selected point
                marker_opacity[index] = 1     # Change the opacity of the selected point
                lat = meas_df['latitude'].iloc[index]
                lon = meas_df['longitude'].iloc[index]
            lat_bts = 0
            lon_bts = 0
            # Logic for finding lat_bts and lon_bts
            matching_row = meas_df.loc[meas_df['latitude'] == lat]
            lat_bts = matching_row['bts_lat'].values[0]
            lon_bts = matching_row['bts_lon'].values[0]
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    if 'lat' in trace and 'lon' in trace and trace['mode'] == 'lines':
                        to_remove.append(i)
                for i in reversed(to_remove):
                    map_figure['data'].pop(i)
                # Create and append the new line_trace
                line_trace = go.Scattermapbox(
                    lat=[lat, lat_bts],
                    lon=[lon, lon_bts],
                    mode='lines',
                    line=dict(width=2, color='darkblue'),
                    hoverinfo='none',
                    name="Connection line - distance: " + str(round(calculate_distance_between_coordinates(lat, lon, lat_bts, lon_bts), 2)) + " km"
                )
                map_figure['data'].append(line_trace)
                #map_figure.add_trace(line_trace)
    # Create the line trace with updated marker colors
    line_trace_rsrp = go.Scatter(
        x=meas_df['time'],
        y=meas_df['rsrp'],
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
        text=meas_df['text'],
        hoverinfo='text',
        name='RSRP',
    )
    # Create the line chart layout (you can customize this)
    line_layout_rsrp = go.Layout(
        title='RSRP',
        xaxis=dict(title='time', tickangle=45),
        yaxis=dict(title='RSRP (dBm)'),
    )
    # Create the line trace with updated marker colors
    line_trace_rsrq = go.Scatter(
        x=meas_df['time'],
        y=meas_df['rsrq'],
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
        text=meas_df['text'],
        hoverinfo='text',
        name='RSRQ',
    )
    # Create the line chart layout (you can customize this)
    line_layout_rsrq = go.Layout(
        title='RSRQ',
        xaxis=dict(title='time', tickangle=45),
        yaxis=dict(title='RSRQ (dB)'),
    )
    # Create the line trace with updated marker colors
    line_trace_rssi = go.Scatter(
        x=meas_df['time'],
        y=meas_df['rssi'],
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
        text=meas_df['text'],
        hoverinfo='text',
        name='RSSI',
    )
    # Create the line chart layout (you can customize this)
    line_layout_rssi = go.Layout(
        title='RSSI',
        xaxis=dict(title='time', tickangle=45),
        yaxis=dict(title='RSSI (dBm)'),
    )
    # Create the line trace with updated marker colors
    line_trace_rssnr = go.Scatter(
        x=meas_df['time'],
        y=meas_df['rssnr'],
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
        text=meas_df['text'],
        hoverinfo='text',
        name='RSSNR',
    )
    # Create the line chart layout (you can customize this)
    line_layout_rssnr = go.Layout(
        title='RSSNR',
        xaxis=dict(title='time', tickangle=45),
        yaxis=dict(title='RSSNR (dB)'),
    )
    # Create the figure and add the scatter mapbox trace
    rsrp_figure = go.Figure(data=[line_trace_rsrp], layout=line_layout_rsrp)
    rsrq_figure = go.Figure(data=[line_trace_rsrq], layout=line_layout_rsrq)
    rssi_figure = go.Figure(data=[line_trace_rssi], layout=line_layout_rssi)
    rssnr_figure = go.Figure(data=[line_trace_rssnr], layout=line_layout_rssnr)
    return rsrp_figure, rsrq_figure, rssi_figure, rssnr_figure, map_figure, min_rsrp_value, max_rsrp_value, min_rsrq_value, max_rsrq_value, min_rssi_value, max_rssi_value, min_rssnr_value, max_rssnr_value
@app.callback(
    [Output('rat-selector', 'disabled'),
     Output('band-selector', 'disabled'),
     Output('operator-selector', 'disabled'),
     Output('interpolation-selector', 'disabled'),
     Output('interpolation-data-selector', 'disabled'),
     Output('data-selector-6', 'disabled')],
    [Input('rsrp-chart', 'figure'),
     Input('interpolation-data-selector', 'value')]
)
def update_selectors_availability(selected_file, interpolation_data):
    # Check if a data set is selected
    if selected_file and interpolation_data:
        # If selected_file is not None, enable the new data selectors
        return False, False, False, False, False, False
    elif selected_file:
        return False, False, False, True, False, False
    else:
        # If no data set is selected, disable the new data selectors
        return True, True, True, True, True, True
@app.callback(
    [Output('band-selector', 'options'),
     Output('rat-selector', 'options'),
     Output('operator-selector', 'options')],
    [Input('rsrp-chart', 'figure')]
)
def update_selectors_options(fig):
    if fig:
        return list(meas_df['band'].unique()), list(meas_df['rat'].unique()), list(meas_df['operator'].unique())
    else:
        return [], [], []

@app.callback(
    [Output('data-selector', 'options'),
     Output('interpolation-selector', 'options'),
     Output('interpolation-data-selector', 'options')],
    [Input('data-selector', 'value')]
)
def update_options(n_clicks):
    interpolation_methods = ['Linear Interpolation', 'Nearest-Neighbor Interpolation', 'Cubic Interpolation']
    interpolation_data = ['RSRP', 'RSRQ', 'RSSI', 'RSSNR']
    updated_options = [
        {'label': f'Data Set: {file_name}', 'value': file_path}
        for file_name, file_path in zip(
            [os.path.basename(file_path) for file_path in glob.glob(os.path.join(data_directory, '*.csv'))],
            glob.glob(os.path.join(data_directory, '*.csv'))
        )
    ]
    return updated_options, interpolation_methods, interpolation_data

if __name__ == '__main__':
    app.run_server(debug=True)