import os
import glob
import random
import webbrowser
import pandas as pd
import json
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
import socket
# def calculate_distance_between_coordinates(lat1, lon1, lat2, lon2):
#     # approximate radius of Earth in kilometers
#     R = 6371.0

#     # convert degrees to radians
#     lat1 = radians(lat1)
#     lon1 = radians(lon1)
#     lat2 = radians(lat2)
#     lon2 = radians(lon2)

#     # calculate the differences of the coordinates
#     dlon = lon2 - lon1
#     dlat = lat2 - lat1

#     # apply the Haversine formula
#     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))

#     # calculate the distance
#     distance = R * c
#     return distance

# def calculate_cumulative_distance(latitudes, longitudes):
#     distance = 0.0

#     # iterate over the coordinates
#     for i in range(len(latitudes) - 1):
#         lat1, lon1 = latitudes[i], longitudes[i]
#         lat2, lon2 = latitudes[i+1], longitudes[i+1]

#         # calculate the distance between neighboring coordinates
#         segment_distance = calculate_distance_between_coordinates(lat1, lon1, lat2, lon2)

#         # add the segment distance to the cumulative distance
#         distance += segment_distance

#     return distance

# def all_values_greater_than(lst, value):
#     return all(x > value for x in lst)

latid_cell = []
lontid_cell = []
name_cell = []
cellid = []
latid_rsrp = []
lontid_rsrp = []
rsrp = []
color_rsrp = []
name_rsrp = []
latid_rsrq = []
lontid_rsrq = []
rsrq = []
color_rsrq = []
name_rsrq = []
latid_sinr = []
lontid_sinr = []
sinr = []
color_sinr = []
name_sinr = []
band = []
operator = []
rat = []
time = []
distance = []
###############################################################
# Initialize dataframe of Cells
df_bts = pd.read_csv(r'/home/baranekm/Documents/Python/5G_module/additional_data/bts_list.csv', delimiter=';')
# Define the directory where your .txt files are located
data_directory = r'/home/baranekm/Documents/Python/5G_module/measured_data'
# Initialize a State variable to store the previous selected file and method
prev_selected_file = None
prev_selected_method = None
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
###############################################################
app.layout = html.Div([
    html.Div([
###############################################################
        html.Label('Select the data for proccesing:'),  # Label for the second additional data selector
        dcc.Dropdown(
            id='data-selector',
            options=[
                {'label': f'Data Set {i}', 'value': file_path}
                for i, file_path in enumerate(glob.glob(r'/home/baranekm/Documents/Python/5G_module/measured_data/*.txt'), start=1)
            ],
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
                    #options=interpolation_methods,
                    placeholder="Select an Interpolation Method..."
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('None:'),  # Label for the second additional data selector
                dcc.Dropdown(
                    id='data-selector-5',
                    # Options and other properties for the second additional data selector
                )
            ], style={'width': '33%', 'margin-right': '10px'}),
###############################################################
            html.Div([
                html.Label('None:'),  # Label for the third additional data selector
                dcc.Dropdown(
                    id='data-selector-6',
                    # Options and other properties for the third additional data selector
                )
            ], style={'width': '33%'}),
        ], style={'display': 'flex', 'margin': '10px'}),
###############################################################        
        dcc.Graph(id='rsrp-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
        dcc.Graph(id='rsrq-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
        dcc.Graph(id='sinr-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
    ], style={'flex': '2', 'display': 'flex', 'flex-direction': 'column'}),
], style={'display': 'flex'})
###############################################################
@app.callback(
    [Output('rsrp-chart', 'figure'), 
     Output('rsrq-chart', 'figure'), 
     Output('sinr-chart', 'figure'), 
     Output('map', 'figure')
    #  Output('band-selector', 'options'),
    #  Output('rat-selector', 'options'),
    #  Output('operator-selector', 'options')
    ],
    [Input('data-selector', 'value'), 
     Input('interpolation-selector', 'value'), 
     Input('rsrp-chart', 'clickData'), 
     Input('rsrq-chart', 'clickData'), 
     Input('sinr-chart', 'clickData'), 
     Input('map', 'clickData')],
    [State('rsrp-chart', 'figure'), 
     State('rsrq-chart', 'figure'), 
     State('sinr-chart', 'figure'), 
     State('map', 'figure')]
)
def update_charts(selected_file, selected_method, rsrp_click_data, rsrq_click_data, sinr_click_data, map_click_data, rsrp_figure, rsrq_figure, sinr_figure, map_figure):
    initial_lat = 0
    initial_lon = 0
    global prev_selected_file  # Use the global keyword to update the previous selected file
    global prev_selected_method  # Use the global keyword to update the previous selected method
###############################################################
    if selected_file != prev_selected_file or selected_method != prev_selected_method:
        map_figure['data'] = []
        latid_cell.clear()
        lontid_cell.clear()
        name_cell.clear()
        cellid.clear()
###############################################################        
        latid_rsrp.clear()
        lontid_rsrp.clear()
        rsrp.clear()
        color_rsrp.clear()
        name_rsrp.clear()
###############################################################
        latid_rsrq.clear()
        lontid_rsrq.clear()
        rsrq.clear()
        color_rsrq.clear()
        name_rsrq.clear()
###############################################################
        latid_sinr.clear()
        lontid_sinr.clear()
        sinr.clear()
        color_sinr.clear()
        name_sinr.clear()
###############################################################
        # band.clear()
        # operator.clear()
        # rat.clear()
        time.clear()
        distance.clear()
###############################################################
        if selected_file != None:
            with open(selected_file, mode="r", encoding="utf-8") as meas_data:
                meas_data = meas_data.readlines()
                i = 0
                for log in meas_data:
###############################################################  
                    latid_rsrp.append(float(log.split(",")[17]))
                    lontid_rsrp.append(float(log.split(",")[19]))
                    name_rsrp.append(str(log.split(",")[3]))
                    cellid.append(int(log.split(",")[7]))
                    rsrp_value = int(log.split(",")[13])
                    rsrp.append(rsrp_value)
                    if rsrp_value >= -80:
                        color_rsrp.append('lawngreen')
                    elif rsrp_value < -80 and rsrp_value >= -90:
                        color_rsrp.append('yellow')
                    elif rsrp_value < -90 and rsrp_value >= -100:
                        color_rsrp.append('orange')
                    elif rsrp_value < -100 :
                        color_rsrp.append('red')
                    else:
                        color_rsrp.append('white')
###############################################################  
                    latid_rsrq.append(float(log.split(",")[17]))
                    lontid_rsrq.append(float(log.split(",")[19]))
                    name_rsrq.append(str(log.split(",")[3]))
                    rsrq_value = float(log.split(",")[14])/100
                    rsrq.append(rsrq_value)
                    if rsrq_value >= -10:
                        color_rsrq.append('lawngreen')
                    elif rsrq_value < -10 and rsrq_value >= -15:
                        color_rsrq.append('yellow')
                    elif rsrq_value < -15 and rsrq_value >= -20:
                        color_rsrq.append('orange')
                    elif rsrq_value < -20 :
                        color_rsrq.append('red')
                    else:
                        color_rsrq.append('white')
###############################################################  
                    latid_sinr.append(float(log.split(",")[17]))
                    lontid_sinr.append(float(log.split(",")[19]))
                    name_sinr.append(str(log.split(",")[3]))
                    sinr_value = float(log.split(",")[15])/100
                    sinr.append(sinr_value)
                    if sinr_value >= 20:
                        color_sinr.append('lawngreen')
                    elif sinr_value < 20 and sinr_value >= 13:
                        color_sinr.append('yellow')
                    elif sinr_value < 13 and sinr_value >= 0:
                        color_sinr.append('orange')
                    elif sinr_value < 0:
                        color_sinr.append('red')
                    else:
                        color_sinr.append('white')
###############################################################  
                    # band.append(str(log.split(",")[20]))
                    # rat.append(str(log.split(",")[14]).split(" ")[1])
                    # operator.append(str(log.split(",")[12].replace("\"", "")))
                    time.append(log.split(",")[1])
                    i += 1
                initial_lat = latid_rsrp[-1]
                initial_lon = lontid_rsrp[-1]
###############################################################  
            for row in df_bts.itertuples():
                latid_cell.append(float(row[9]))
                lontid_cell.append(float(row[10]))
                name_cell.append(str(row[8]))
###############################################################
            if selected_method != None:
                grid_x, grid_y = np.mgrid[min(latid_rsrp):max(latid_rsrp):100j, min(lontid_rsrp):max(lontid_rsrp):100j]
                # Define the interpolation method based on the selected method
                if selected_method == 'Linear Interpolation':
                    grid_z = griddata((latid_rsrp, lontid_rsrp), rsrp, (grid_x, grid_y), method='linear')
                elif selected_method == 'Nearest-Neighbor Interpolation':
                    grid_z = griddata((latid_rsrp, lontid_rsrp), rsrp, (grid_x, grid_y), method='nearest')
                elif selected_method == 'Cubic Interpolation':
                    grid_z = griddata((latid_rsrp, lontid_rsrp), rsrp, (grid_x, grid_y), method='cubic')
                # elif selected_method == 'CloughTocher Interpolation':
                #     interp = CloughTocher2DInterpolator(list(zip(latid_rsrp, lontid_rsrp)), rsrp)
                #     grid_z = interp(grid_x, grid_y)

                # Define RSRP thresholds and corresponding colors
                rsrp_thresholds = [-80, -85, -90, -95, -100, -105]
                colors = ['green', 'yellowgreen', 'yellow', 'orange', 'red', 'darkred']

                # Assign colors based on RSRP thresholds
                colors_interpolated = []
                opacities_interpolated = []
                for value in grid_z.flatten():
                    color_interpolated = 'white'  # Default color for values outside the defined thresholds
                    opacity_interpolated = 0
                    if value > -80:
                        color_interpolated = 'green'
                        opacity_interpolated = 0.4
                    elif value < -105:
                        color_interpolated = 'darkred'
                        opacity_interpolated = 0.4
                    else:
                        for i in range(len(rsrp_thresholds) - 1):
                            if rsrp_thresholds[i] >= value > rsrp_thresholds[i + 1]:
                                color_interpolated = colors[i]
                                opacity_interpolated = 0.4
                    colors_interpolated.append(color_interpolated)
                    opacities_interpolated.append(opacity_interpolated)
###############################################################
            # Create Scattermapbox trace for measured RSRP points
            scatter_mapbox_trace_rsrp = go.Scattermapbox(
                lat=latid_rsrp,
                lon=lontid_rsrp,
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=color_rsrp, opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=name_rsrp,
                hoverinfo='text',
                name='Measured RSRP Points'
            )
###############################################################
            # Create Scattermapbox trace for measured RSRP points
            scatter_mapbox_trace_rsrq = go.Scattermapbox(
                lat=latid_rsrq,
                lon=lontid_rsrq,
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=color_rsrq, opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=name_rsrq,
                hoverinfo='text',
                name='Measured RSRQ Points',
                visible='legendonly'  # Set visibility to legendonly by default
            )
###############################################################
            # Create Scattermapbox trace for measured RSRP points
            scatter_mapbox_trace_sinr = go.Scattermapbox(
                lat=latid_sinr,
                lon=lontid_sinr,
                mode='markers+lines',
                marker=dict(size=10, symbol="circle", color=color_sinr, opacity=1, colorscale='Viridis'),
                line=dict(width=2, color='grey'),
                text=name_sinr,
                hoverinfo='text',
                name='Measured SINR Points',
                visible='legendonly'  # Set visibility to legendonly by default
            )
###############################################################
            # Create Scattermapbox trace for Cell points
            scatter_mapbox_trace_cells = go.Scattermapbox(
                lat=latid_cell,
                lon=lontid_cell,
                mode='markers',
                marker=dict(size=20, symbol="circle", color='black', opacity=0.2),
                text=name_cell,
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
                    marker=dict(size=10, color=colors_interpolated, opacity=opacities_interpolated, colorscale='Viridis'),
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
                #mapbox_style='basic',
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
                                            scatter_mapbox_trace_sinr, scatter_mapbox_trace_cells, 
                                            scatter_mapbox_trace_interpolated_rsrp], layout=map_layout)
            else:
                # Create the figure and add the scatter mapbox trace
                map_figure = go.Figure(data=[scatter_mapbox_trace_rsrp, scatter_mapbox_trace_rsrq, 
                                            scatter_mapbox_trace_sinr, scatter_mapbox_trace_cells], layout=map_layout)
            prev_selected_file = selected_file  # Update the previous selected file
            prev_selected_method = selected_method  # Update the previous selected method
###############################################################
    # Use dash.callback_context to determine which input triggered the callback
    ctx = dash.callback_context
###############################################################
    # Data to be displayed
    x = time
    y_rsrp = rsrp
    y_rsrq = rsrq
    y_sinr = sinr
###############################################################
    # Create a list to hold marker colors and opacity
    marker_colors = ['blue'] * len(x)  # Initialize with the original color
    marker_opacity = [0.5] * len(x)  # Initialize with the original opacity
###############################################################
    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'rsrp-chart' or trigger_id == 'rsrq-chart' or trigger_id == 'sinr-chart':
            if trigger_id == 'rsrp-chart':
                index = rsrp_click_data['points'][0]['pointIndex']
            elif trigger_id == 'rsrq-chart':
                index = rsrq_click_data['points'][0]['pointIndex']
            elif trigger_id == 'sinr-chart':
                index = sinr_click_data['points'][0]['pointIndex']
            else:
                index = 0
            # Highlight the selected point by changing its marker color
            if index <= len(latid_rsrp):
                marker_colors[index] = 'red'  # Change the color of the selected point
                marker_opacity[index] = 1
                lat = latid_rsrp[index]
                lon = lontid_rsrp[index]
            lat_bts = 0
            lon_bts = 0
###############################################################  
            # Your logic for finding lat_bts and lon_bts goes here
            for row in df_bts.itertuples():
                try:
                    if int(row[2]) == int(cellid[latid_rsrp.index(lat)]):
                        lat_bts = row[9]
                        lon_bts = row[10]
                except:
                    continue
###############################################################  
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    #if 'lat' in trace and 'lon' in trace and trace.get('mode', '') == 'lines':
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
                    name=name_rsrp[latid_rsrp.index(lat)]
                )
                map_figure['data'].append(line_trace)
                #map_figure.add_trace(line_trace)
###############################################################            
        elif trigger_id == 'map':
            index = map_click_data['points'][0]['pointIndex']
            # Highlight the selected point by changing its marker color
            if index <= len(latid_rsrp):
                marker_colors[index] = 'red'  # Change the color of the selected point
                marker_opacity[index] = 1     # Change the opacity of the selected point
                lat = latid_rsrp[index]
                lon = lontid_rsrp[index]
            lat_bts = 0
            lon_bts = 0
###############################################################
            # Your logic for finding lat_bts and lon_bts goes here
            for row in df_bts.itertuples():
                try:
                    if int(row[2]) == int(cellid[latid_rsrp.index(lat)]):
                        lat_bts = row[9]
                        lon_bts = row[10]
                except:
                    continue
###############################################################
            if lat_bts and lon_bts != 0:
                # Find and remove existing line_trace traces
                to_remove = []
                for i, trace in enumerate(map_figure['data']):
                    #if 'lat' in trace and 'lon' in trace and trace.get('mode', '') == 'lines':
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
                    name=name_rsrp[latid_rsrp.index(lat)]
                )
                map_figure['data'].append(line_trace)
                #map_figure.add_trace(line_trace)
###############################################################
    # Create the line trace with updated marker colors
    line_trace_rsrp = go.Scatter(
        x=x,
        y=y_rsrp,
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
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
        x=x,
        y=y_rsrq,
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
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
    line_trace_sinr = go.Scatter(
        x=x,
        y=y_sinr,
        mode='lines+markers',  # Display lines and markers
        line=dict(width=2, color='blue'),
        marker=dict(
            size=8,
            opacity=marker_opacity,
            color=marker_colors,  # Set marker colors
            symbol='square',
        ),
        name='SINR',
    )
    # Create the line chart layout (you can customize this)
    line_layout_sinr = go.Layout(
        title='SINR',
        xaxis=dict(title='time', tickangle=45),
        yaxis=dict(title='SINR (dB)'),
    )
###############################################################
    # Create the figure and add the scatter mapbox trace
    rsrp_figure = go.Figure(data=[line_trace_rsrp], layout=line_layout_rsrp)
    rsrq_figure = go.Figure(data=[line_trace_rsrq], layout=line_layout_rsrq)
    sinr_figure = go.Figure(data=[line_trace_sinr], layout=line_layout_sinr)
###############################################################
    return rsrp_figure, rsrq_figure, sinr_figure, map_figure
###############################################################
@app.callback(
    [Output('rat-selector', 'disabled'),
     Output('band-selector', 'disabled'),
     Output('operator-selector', 'disabled'),
     Output('interpolation-selector', 'disabled'),
     Output('data-selector-5', 'disabled'),
     Output('data-selector-6', 'disabled')],
    [Input('data-selector', 'value')]
)
def update_selectors_availability(selected_file):
    # Check if a data set is selected
    if selected_file:
        # If selected_file is not None, enable the new data selectors
        return False, False, False, False, False, False
    else:
        # If no data set is selected, disable the new data selectors
        return True, True, True, True, True, True
###############################################################
@app.callback(
    [Output('band-selector', 'options'),
     Output('rat-selector', 'options'),
     Output('operator-selector', 'options'),
     Output('interpolation-selector', 'options')],
    [Input('data-selector', 'value')]
)
def update_selectors_options(selected_file):
    global prev_selected_file
    interpolation_methods = []
###############################################################
    # Check if a data are selected
    if selected_file != prev_selected_file:
        band.clear()
        operator.clear()
        rat.clear()
###############################################################
        if selected_file != None:
            # Initialize a methods for interpolation
            interpolation_methods = ['Linear Interpolation', 'Nearest-Neighbor Interpolation', 'Cubic Interpolation']
            with open(selected_file, mode="r", encoding="utf-8") as meas_data:
                meas_data = meas_data.readlines()
                for log in meas_data:                  
###############################################################
                    band.append(str(log.split(",")[9]))
                    rat.append(str(log.split(",")[3]))
                    operator.append(str(log.split(",")[4]))         #TODO change to operator name
###############################################################
        band_options = list(set(band))
        rat_options = list(set(rat))
        operator_options = list(set(operator))
###############################################################
        prev_selected_file = selected_file  # Update the previous selected file
        # Update options based on the selected rat 
        return band_options, rat_options, operator_options, interpolation_methods
    else:
        # If no data are selected, return empty options for other selectors
        return [], [], [], []
###############################################################
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
