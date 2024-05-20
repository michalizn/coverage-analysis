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

script_dir = os.path.dirname(__file__).replace('pages', '')
data_directory = os.path.join(script_dir, 'data', 'measured_data', 'static')
"""
- Settings part
        - Select from witch metric will forecast be (dropdown menu)
        - Percentage of train set and test set (slider 0 to 100 %)
        - Cross Validation ON/OFF (Checklist)
        - Features selection (minute, hour, day, day of week, week of month etc..) Dropdown selection
        - Tuning of the model (some input boxes)
- Graphs
        - Metric
        - Division of train/test set
        - Selected features boxplots
        - Feature importance bargraph
- Forecast model result
        - Graph Forecast on test  
        - On specified range
        - Results like RMSE, MSE etc...

"""
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
							id='data-selector-static',
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
					dbc.CardBody([
						html.Label('Settings', style={'fontSize': 30}),
						dcc.Dropdown(
							id='metric-selector',
							options=[
								{'label': 'Metric 1', 'value': 'metric1'},
								{'label': 'Metric 2', 'value': 'metric2'},
								# Add more options as needed
							],
							placeholder='Select Metric for Forecast',
						),
					]),
				]),
			]),
        ]),
        dbc.Row([
            dbc.Col([
				dbc.Card([
						dbc.CardHeader("OpenStreetMap"),
						dcc.Slider(
							id='train-test-slider',
							min=0,
							max=100,
							step=1,
							value=70,
							marks={i: f'{i}%' for i in range(0, 101, 10)},
							tooltip={'always_visible': True}
						),
				]),
			]),
        ]),
        dbc.Row([
            dbc.Col([
				dbc.Card([
						dbc.CardHeader("OpenStreetMap"),
						dcc.Checklist(
							id='cv-checkbox',
							options=[
								{'label': 'Cross Validation', 'value': 'cross-validation'},
							],
							value=[],  # Initialize empty
							inline=True,
						),
				]),
			]),
            dbc.Col([
				dbc.Card([
						dbc.CardHeader("OpenStreetMap"),
						dcc.Dropdown(
							id='feature-selector',
							options=[
								{'label': 'Minute', 'value': 'minute'},
								{'label': 'Hour', 'value': 'hour'},
								{'label': 'Day', 'value': 'day'},
								{'label': 'Day of Week', 'value': 'day_of_week'},
								{'label': 'Week of Month', 'value': 'week_of_month'},
								# Add more options as needed
							],
							multi=True,
							placeholder='Select Features',
						),
				]),
			]),
		]),
		dbc.Row([
            dbc.Col([
				dbc.Card([
					dbc.CardBody([
						html.Label('Model Tuning', style={'fontSize': 20}),
						dbc.Input(id='input-box1', placeholder='Parameter 1'),
						dbc.Input(id='input-box2', placeholder='Parameter 2'),
					# Add more input boxes as needed
				]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label('Graphs', style={'fontSize': 30, 'textAlign': 'center'}),
                    dcc.Graph(id='metric-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.Graph(id='train-test-division', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.Graph(id='selected-boxplots', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.Graph(id='importance-chart', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                ]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label('Forecast Model Result', style={'fontSize': 30, 'textAlign': 'center'}),
                    dcc.Graph(id='forecast', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                    dcc.Graph(id='forecast-range', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                ]),
            ]),
        ]),
    ]),
])
])

# @app.callback(
#     [Output('rsrp-chart', 'figure'), 
#      Output('rsrq-chart', 'figure'),
#      Output('rssi-chart', 'figure'),  
#      Output('rssnr-chart', 'figure'), 
#      Output('map', 'figure'),
#      Output('rsrp-filter', 'min'),
#      Output('rsrp-filter', 'max'),
#      Output('rsrq-filter', 'min'),
#      Output('rsrq-filter', 'max'),
#      Output('rssi-filter', 'min'),
#      Output('rssi-filter', 'max'),
#      Output('rssnr-filter', 'min'),
#      Output('rssnr-filter', 'max'),],
#     [Input('button-filter', 'n_clicks'),
#      Input('data-selector-static', 'value'), 
#      Input('interpolation-selector', 'value'),
#      Input('interpolation-data-selector', 'value'),
#      Input('band-selector', 'value'),
#      Input('rat-selector', 'value'),
#      Input('operator-selector', 'value'),
#      Input('rsrp-chart', 'clickData'), 
#      Input('rsrq-chart', 'clickData'),
#      Input('rssi-chart', 'clickData'), 
#      Input('rssnr-chart', 'clickData'), 
#      Input('map', 'clickData')],
#     [State('rsrp-chart', 'figure'), 
#      State('rsrq-chart', 'figure'), 
#      State('rssnr-chart', 'figure'), 
#      State('map', 'figure'),
#      State('rsrp-filter', 'value'),
#      State('rsrq-filter', 'value'),
#      State('rssi-filter', 'value'),
#      State('rssnr-filter', 'value'),]
# )
# def update_charts(click_filter_button, selected_file, selected_method, selected_interpolation_data, selected_band, seleceted_rat, selected_operator, rsrp_click_data, rsrq_click_data, rssi_click_data, rssnr_click_data, map_click_data, rsrp_figure, rsrq_figure, rssnr_figure, map_figure, filter_rsrp_range, filter_rsrq_range, filter_rssi_range, filter_rssnr_range):

if __name__ == "__main__":
    app.run_server(debug=True)