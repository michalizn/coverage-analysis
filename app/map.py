import os
import glob
import time
import pandas as pd
from math import sin, cos, sqrt, atan2, radians
from math import hypot
import matplotlib.pyplot as plt
import dash
from dash.exceptions import PreventUpdate
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import Input, Output, State, no_update
from dash import html
import plotly.express as px
import plotly.graph_objects as go
from plotly.validators.scatter.marker import SymbolValidator
import numpy as np
from scipy.interpolate import griddata
from scipy.interpolate import LinearNDInterpolator, CloughTocher2DInterpolator
from matplotlib import colors as mpl_colors
import time 

###############################################################
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
###############################################################
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
###############################################################
# Define a function to map values to colors based on input column
def map_column_to_color(df, column_name):
    if column_name == 'rsrp':
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
###############################################################
# Initialize dataframe of Cells
bts_df = pd.read_csv(r'/home/baranekm/Documents/Python/5G_module/additional_data/bts_list.csv', delimiter=';')
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
data_directory = r'/home/baranekm/Documents/Python/5G_module/measured_data'
# Initialize a State variable to store the previous selected file and method
prev_selected_file = None
prev_selected_file_2 = None
prev_selected_method = None
prev_selected_interpolation_data = None
prev_selected_band = None
prev_selected_rat = None
prev_selected_operator = None 
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
###############################################################
# Create the map layout
map_layout = go.Layout(
    mapbox_style='open-street-map',
    #mapbox_style='carto-positron',
    hovermode='closest',
    height=1000,  # Set the height of the map
    width=1000,    # Set the width of the map
    mapbox=dict(
        zoom=12  # Adjust the initial zoom level as needed
    )
)
###############################################################
# Create the figure and add the scatter mapbox trace
map_figure = go.Figure(data=[go.Scattermapbox()], layout=map_layout)
###############################################################
# Create the Dash app
app = dash.Dash(__name__)
# gunicorn map_v1:server --bind=192.168.0.x:8000
server = app.server
###############################################################
app.layout = html.Div([
    html.Div([
        html.Label('Select the data for proccesing:', style={'margin-bottom' : '10px'}),  # Label for the second additional data selector
        dcc.Dropdown(
            id='data-selector',
            options=[
                {'label': f'Data Set: {file_name}', 'value': file_path}
                for file_name, file_path in zip([os.path.basename(file_path) for file_path in glob.glob(r'/home/baranekm/Documents/Python/5G_module/measured_data/*.csv')], glob.glob(r'/home/baranekm/Documents/Python/5G_module/measured_data/*.csv'))
            ],
            multi=True,  # Allow multiple selection
            placeholder="Select a data set..."
        ),
###############################################################
        dcc.Graph(id='map', figure=map_figure, className='map')
    ], style={'flex': '1', 'margin': '10px'}),
###############################################################
    html.Div([
        html.Div([
            html.Div([
                html.Label('Technology (RAT):'),  # Label for the first additional data selector
                dcc.Dropdown(
                    id='rat-selector',
                    placeholder="Select a Technology (RAT)..."
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('Selected BAND:'),  # Label for the second additional data selector
                dcc.Dropdown(
                    id='band-selector',
                    placeholder="Select a BAND..."
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('Operator (provider):'),  # Label for the third additional data selector
                dcc.Dropdown(
                    id='operator-selector',
                    placeholder="Select a Operator (provider)..."
                )
            ], style={'width': '33%'}),
        ], style={'display': 'flex', 'margin': '10px'}),
###############################################################
        html.Div([
            html.Div([
                html.Label('Type of interpolation:'),  # Label for the first additional data selector
                dcc.Dropdown(
                    id='interpolation-selector',
                    placeholder="Select an Interpolation Method..."
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('Data for interpolation:'),  # Label for the second additional data selector
                dcc.Dropdown(
                    id='interpolation-data-selector',
                    placeholder="Select a dara for interpolation..."
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('None:'),  # Label for the third additional data selector
                dcc.Dropdown(
                    id='data-selector-6',
                )
            ], style={'width': '33%'}),
        ], style={'display': 'flex', 'margin': '10px'}),
###############################################################        
        dcc.Graph(id='rsrp-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
        dcc.Graph(id='rsrq-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
        dcc.Graph(id='rssi-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
        dcc.Graph(id='rssnr-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
    ], style={'flex': '2', 'display': 'flex', 'flex-direction': 'column'}),
], style={'display': 'flex'})
###############################################################
@app.callback(
    [Output('rsrp-chart', 'figure'), 
     Output('rsrq-chart', 'figure'),
     Output('rssi-chart', 'figure'),  
     Output('rssnr-chart', 'figure'), 
     Output('map', 'figure')],
    [Input('data-selector', 'value'), 
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
     State('map', 'figure')]
)
def update_charts(selected_file, selected_method, selected_interpolation_data, selected_band, seleceted_rat, selected_operator, rsrp_click_data, rsrq_click_data, rssi_click_data, rssnr_click_data, map_click_data, rsrp_figure, rsrq_figure, sinr_figure, map_figure):
    initial_lat = 0
    initial_lon = 0
    global prev_selected_file  # Use the global keyword to update the previous selected file
    global prev_selected_method  # Use the global keyword to update the previous selected method
    global prev_selected_interpolation_data # Use the global keyword to update the previous selected interpolation data
    global prev_selected_band  # Use the global keyword to update the previous selected method
    global prev_selected_rat  # Use the global keyword to update the previous selected method
    global prev_selected_operator  # Use the global keyword to update the previous selected method
    global meas_df
###############################################################
    if selected_file != prev_selected_file or selected_method != prev_selected_method or selected_interpolation_data != prev_selected_interpolation_data or selected_band != prev_selected_band or seleceted_rat != prev_selected_rat or selected_operator != prev_selected_operator:
        map_figure['data'] = []
###############################################################
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
            # Map 'rsrp' values to colors
            map_column_to_color(meas_df, 'rsrp')
            # Map 'rsrq' values to colors
            map_column_to_color(meas_df, 'rsrq')
            try:
                # Map 'rssi' values to colors
                map_column_to_color(meas_df, 'rssi')
            except:
                print("5G")
            # Map 'rssnr' values to colors
            map_column_to_color(meas_df, 'rssnr')
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
            # Initialize the position of which is the map open
            if 0 < len(meas_df):
                initial_lat = float(meas_df['latitude'].iloc[-1])
                initial_lon = float(meas_df['longitude'].iloc[-1])
            else:
                # Brno center location
                initial_lat = 49.1947
                initial_lon = 16.6078
###############################################################
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
###############################################################
                # Define RSRP thresholds and corresponding colors
                rsrp_thresholds = [-70, -90, -100, -120, -130, -160]
                colors = ['green', 'yellowgreen', 'yellow', 'orange', 'red', 'darkred']
###############################################################
                # Assign colors based on RSRP thresholds
                colors_interpolated = []
                opacities_interpolated = []
                for value in grid_z.flatten():
                    color_interpolated = 'white'  # Default color for values outside the defined thresholds
                    opacity_interpolated = 0
                    if value > -80:
                        color_interpolated = 'green'
                        opacity_interpolated = 1
                    elif value < -160:
                        color_interpolated = 'darkred'
                        opacity_interpolated = 1
                    else:
                        for i in range(len(rsrp_thresholds) - 1):
                            if rsrp_thresholds[i] >= value > rsrp_thresholds[i + 1]:
                                color_interpolated = colors[i]
                                opacity_interpolated = 1
                    colors_interpolated.append(color_interpolated)
                    opacities_interpolated.append(opacity_interpolated)
###############################################################
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
###############################################################
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
###############################################################
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
###############################################################
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
###############################################################
            # Create Scattermapbox trace for Cell points
            scatter_mapbox_trace_cells = go.Scattermapbox(
                lat=bts_df['bts_lat'],
                lon=bts_df['bts_lon'],
                mode='markers',
                marker=dict(size=20, symbol="circle", color='black', opacity=0.2),
                text=bts_df['text'],
                hoverinfo='text',
                name='Cell towers'
            )
###############################################################
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
###############################################################
            # Create the map layout
            map_layout = go.Layout(
                mapbox_style='open-street-map',
                hovermode='closest',
                height=1000,  # Set the height of the map
                width=1000,    # Set the width of the map
                mapbox=dict(
                    center=dict(
                        lat=initial_lat,
                        lon=initial_lon
                    ),
                    zoom=12  # Adjust the initial zoom level as needed
                ),
                legend=dict(x=0, y=-0.1)  # Set x and y coordinates to position the legend at the bottom
            )
###############################################################
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
###############################################################
    # Use dash.callback_context to determine which input triggered the callback
    ctx = dash.callback_context
###############################################################
    # Create a list to hold marker colors and opacity
    marker_colors = ['blue'] * len(meas_df)  # Initialize with the original color
    marker_opacity = [0.5] * len(meas_df)  # Initialize with the original opacity
###############################################################
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
###############################################################  
            # Logic for finding lat_bts and lon_bts
            matching_row = meas_df.loc[meas_df['latitude'] == lat]
            lat_bts = matching_row['bts_lat'].values[0]
            lon_bts = matching_row['bts_lon'].values[0]
###############################################################  
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    if 'lat' in trace and 'lon' in trace and trace['mode'] == 'lines':
                        to_remove.append(i)
###############################################################                 
                for i in reversed(to_remove):
                    map_figure['data'].pop(i)
###############################################################  
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
###############################################################            
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
###############################################################
            # Logic for finding lat_bts and lon_bts
            matching_row = meas_df.loc[meas_df['latitude'] == lat]
            lat_bts = matching_row['bts_lat'].values[0]
            lon_bts = matching_row['bts_lon'].values[0]
###############################################################
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    if 'lat' in trace and 'lon' in trace and trace['mode'] == 'lines':
                        to_remove.append(i)
###############################################################
                for i in reversed(to_remove):
                    map_figure['data'].pop(i)
###############################################################
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
###############################################################
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
###############################################################
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
###############################################################
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
###############################################################
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
###############################################################
    # Create the figure and add the scatter mapbox trace
    rsrp_figure = go.Figure(data=[line_trace_rsrp], layout=line_layout_rsrp)
    rsrq_figure = go.Figure(data=[line_trace_rsrq], layout=line_layout_rsrq)
    rssi_figure = go.Figure(data=[line_trace_rssi], layout=line_layout_rssi)
    rssnr_figure = go.Figure(data=[line_trace_rssnr], layout=line_layout_rssnr)
###############################################################
    return rsrp_figure, rsrq_figure, rssi_figure, rssnr_figure, map_figure
###############################################################
@app.callback(
    [Output('rat-selector', 'disabled'),
     Output('band-selector', 'disabled'),
     Output('operator-selector', 'disabled'),
     Output('interpolation-selector', 'disabled'),
     Output('interpolation-data-selector', 'disabled'),
     Output('data-selector-6', 'disabled')],
    [Input('data-selector', 'value'),
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
###############################################################
@app.callback(
    [Output('band-selector', 'options'),
     Output('rat-selector', 'options'),
     Output('operator-selector', 'options'),
     Output('interpolation-selector', 'options'),
     Output('interpolation-data-selector', 'options')],
    [Input('data-selector', 'value')]
)
def update_selectors_options(selected_file):
    global prev_selected_file_2
    interpolation_methods = []
    interpolation_data = []
###############################################################
    # Check if a data are selected
    if selected_file != prev_selected_file_2:
###############################################################
        if selected_file != None:
            # Initialize a methods for interpolation
            interpolation_methods = ['Linear Interpolation', 'Nearest-Neighbor Interpolation', 'Cubic Interpolation']
            interpolation_data = ['RSRP', 'RSRQ', 'RSSI', 'RSSNR']
            # Make a delay between execution of two callbacks
            time.sleep(0.4)
        else:
            return [], [], [], [], []
###############################################################
        prev_selected_file_2 = selected_file  # Update the previous selected file
        # Update options based on the selected rat 
        return list(meas_df['band'].unique()), list(meas_df['rat'].unique()), list(meas_df['operator'].unique()), interpolation_methods, interpolation_data
    else:
        # If no data are selected, return empty options for other selectors
        return [], [], [], [], []
###############################################################
# Define a callback to update options when the dropdown is clicked
@app.callback(
    Output('data-selector', 'options'),
    [Input('data-selector', 'value')]
)
def update_options(n_clicks):
    # Add your logic to update options based on the click event
    # For example, you can update the options list with new data
    updated_options = [
        {'label': f'Data Set: {file_name}', 'value': file_path}
        for file_name, file_path in zip(
            [os.path.basename(file_path) for file_path in glob.glob(r'/home/baranekm/Documents/Python/5G_module/measured_data/*.csv')],
            glob.glob(r'/home/baranekm/Documents/Python/5G_module/measured_data/*.csv')
        )
    ]
    return updated_options
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)