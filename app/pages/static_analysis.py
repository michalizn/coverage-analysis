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
                                                html.Label('Filtering:', style={'fontSize':30, 'textAlign':'center'}),
                                                        html.Div([
                                                                html.Div([
                                                                        html.Label('Technology (RAT):'),  # Label for the first additional data selector
                                                                        dcc.Dropdown(
                                                                        id='rat-selector-static',
                                                                        placeholder="Select a Technology (RAT)..."
                                                                        )
                                                                ], style={'width': '33%', 'margin-right': '10px'}),
                                                                html.Div([
                                                                        html.Label('Selected BAND:'),  # Label for the second additional data selector
                                                                        dcc.Dropdown(
                                                                        id='band-selector-static',
                                                                        placeholder="Select a BAND..."
                                                                        )
                                                                ], style={'width': '33%', 'margin-right': '10px'}),
                                                                html.Div([
                                                                        html.Label('Operator (provider):'),  # Label for the third additional data selector
                                                                        dcc.Dropdown(
                                                                        id='operator-selector-static',
                                                                        placeholder="Select a Operator (provider)..."
                                                                        )
                                                                ], style={'width': '33%'}),
                                                        ], style={'display': 'flex', 'margin': '10px'}),
                                        ]),
                                ]),
                        ]),
                ]),
                dbc.Row([
                        dbc.Col([
                                dbc.Card([
                                        dbc.CardHeader("RSRP"),
                                        dcc.Graph(id='rsrp-chart-static', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                                        dcc.RangeSlider(
                                                id='rsrp-filter-static',
                                                min=1,
                                                max=100,
                                                allowCross=False,
                                                tooltip={"always_visible": True},
                                        ),
                                        html.Button(
                                                id='button-filter-static',
                                                children='Filter',
                                        ),
                                ]),
                                dbc.Card([
                                        dbc.CardHeader("RSRQ"),
                                        dcc.Graph(id='rsrq-chart-static', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                                        dcc.RangeSlider(
                                                id='rsrq-filter-static',
                                                min=1,
                                                max=100,
                                                allowCross=False,
                                                tooltip={"always_visible": True},
                                        ),
                                        html.Button(
                                                id='button-filter-static',
                                                children='Filter',
                                        ),
                                ]),
                                dbc.Card([
                                        dbc.CardHeader("RSSI"),
                                        dcc.Graph(id='rssi-chart-static', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                                        dcc.RangeSlider(
                                                id='rssi-filter-static',
                                                min=1,
                                                max=100,
                                                allowCross=False,
                                                tooltip={"always_visible": True},
                                        ),
                                        html.Button(
                                                id='button-filter-static',
                                                children='Filter',
                                        ),
                                ]),
                                dbc.Card([
                                        dbc.CardHeader("RSSNR"),
                                        dcc.Graph(id='rssnr-chart-static', className='graph', style={'height': '300px', 'margin-bottom': '10px'}),
                                        dcc.RangeSlider(
                                                id='rssnr-filter-static',
                                                min=1,
                                                max=100,
                                                allowCross=False,
                                                tooltip={"always_visible": True},
                                        ),
                                        html.Button(
                                                id='button-filter-static',
                                                children='Filter',
                                        ),
                                ]),
                        ]),
                ]),
        ]),
])

if __name__ == "__main__":
    app.run_server(debug=True)