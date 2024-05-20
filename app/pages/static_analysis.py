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
						html.Label('Rolling Average:', style={'fontSize':30, 'textAlign':'center'}),
							html.Div([
								html.Label('Select number of minutes that will be a rolling average over the data set:'),
								dcc.Slider(
								id='average-rolling-slider',
								min=1,
								max=120,
								value=15,  # Default value
								marks={i: str(i) for i in range(0, 121, 10)},  # Add marks every 10 steps
								),
							html.Div(id='slider-output-container', style={'margin-top': 20}),
							html.Button(
								id='button-average-static',
								children='Select',
								style={'width': '100%'}),
						]),
					]),
				]),
			]),
		]),
		dbc.Row([
			dbc.Col([
				dbc.Card([
					dbc.CardBody([
						html.Label('Optimize dataset size:', style={'fontSize':30, 'textAlign':'center'}),
							html.Div([
								dcc.Checklist(
									id='checkbox-static',
									options=[
										{'label': '  Get better loading times of the data sets', 'value': 'optimize'}
									],
								),
						]),
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
					dbc.CardHeader("Box Plots"),
					html.Div([
						html.Div([
							dcc.Graph(id='boxplot-rsrp-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
						html.Div([
							dcc.Graph(id='boxplot-rsrq-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
                    ], style={'display': 'flex', 'margin': '10px'}),
					html.Div([
						html.Div([
							dcc.Graph(id='boxplot-rssi-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
						html.Div([
							dcc.Graph(id='boxplot-rssnr-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
                    ], style={'display': 'flex', 'margin': '10px'}),
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
		dbc.Row([
			dbc.Col([
				dbc.Card([
					dbc.CardHeader("Histograms"),
					html.Div([
						html.Div([
							dcc.Graph(id='histogram-rsrp-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
						html.Div([
							dcc.Graph(id='histogram-rsrq-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
                    ], style={'display': 'flex', 'margin': '10px'}),
					html.Div([
						html.Div([
							dcc.Graph(id='histogram-rssi-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
						html.Div([
							dcc.Graph(id='histogram-rssnr-chart-static'),
						], style={'width': '50%', 'margin-right': '10px'}),
                    ], style={'display': 'flex', 'margin': '10px'}),
				]),
			]),
		]),
	]),
])
@app.callback(
	Output('slider-output-container', 'children'),
	[Input('average-rolling-slider', 'value')]
)
def update_output(value):
	return f'You have selected {value} minutes for the rolling average.'

@app.callback(
	[Output('rsrp-chart-static', 'figure'), 
	 Output('rsrq-chart-static', 'figure'),
	 Output('rssi-chart-static', 'figure'),  
	 Output('rssnr-chart-static', 'figure'),
	 Output('boxplot-rsrp-chart-static', 'figure'), 
	 Output('boxplot-rsrq-chart-static', 'figure'),
	 Output('boxplot-rssi-chart-static', 'figure'),  
	 Output('boxplot-rssnr-chart-static', 'figure'),
	 Output('histogram-rsrp-chart-static', 'figure'), 
	 Output('histogram-rsrq-chart-static', 'figure'),
	 Output('histogram-rssi-chart-static', 'figure'),  
	 Output('histogram-rssnr-chart-static', 'figure'),
	 Output('rsrp-filter-static', 'min'),
	 Output('rsrp-filter-static', 'max'),
	 Output('rsrq-filter-static', 'min'),
	 Output('rsrq-filter-static', 'max'),
	 Output('rssi-filter-static', 'min'),
	 Output('rssi-filter-static', 'max'),
	 Output('rssnr-filter-static', 'min'),
	 Output('rssnr-filter-static', 'max')],
	[Input('button-filter-static', 'n_clicks'),
  	 Input('button-average-static', 'n_clicks'),
	 Input('data-selector-static', 'value'), 
	 Input('band-selector-static', 'value'),
	 Input('rat-selector-static', 'value'),
	 Input('operator-selector-static', 'value')],
	[State('rsrp-chart-static', 'figure'), 
	 State('rsrq-chart-static', 'figure'), 
	 State('rssnr-chart-static', 'figure'), 
	 State('rsrp-filter-static', 'value'),
	 State('rsrq-filter-static', 'value'),
	 State('rssi-filter-static', 'value'),
	 State('rssnr-filter-static', 'value'),
	 State('average-rolling-slider', 'value'),
	 State("checkbox-static", "value")]
)
def update_charts(click_filter_button, click_avg_button, selected_file, selected_band, seleceted_rat, selected_operator, rsrp_figure, rsrq_figure, rssnr_figure, filter_rsrp_range, filter_rsrq_range, filter_rssi_range, filter_rssnr_range, average_value, optim_size):
	max_rsrp_value = 0
	min_rsrp_value = 0
	max_rsrq_value = 0
	min_rsrq_value = 0
	max_rssi_value = 0
	min_rssi_value = 0
	max_rssnr_value = 0
	min_rssnr_value = 0
	global prev_selected_file  # Use the global keyword to update the previous selected file
	global prev_selected_band  # Use the global keyword to update the previous selected method
	global prev_selected_rat  # Use the global keyword to update the previous selected method
	global prev_selected_operator  # Use the global keyword to update the previous selected method
	global prev_filter_rsrp_range  # Use the global keyword to update the previous selected method
	global prev_filter_rsrq_range  # Use the global keyword to update the previous selected method
	global prev_filter_rssi_range  # Use the global keyword to update the previous selected method
	global prev_filter_rssnr_range  # Use the global keyword to update the previous selected method
	global meas_df
	if selected_file != prev_selected_file or selected_band != prev_selected_band or seleceted_rat != prev_selected_rat or selected_operator != prev_selected_operator or filter_rsrp_range != prev_filter_rsrp_range or filter_rsrq_range != prev_filter_rsrq_range or filter_rssi_range != prev_filter_rssi_range or filter_rssnr_range != prev_filter_rssnr_range or average_value:
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

			minute_value = str(average_value) + 'min'
			# If you want to retain the original DataFrame with the rolling average column, you can create a new column for it
			meas_df['rsrp'] = meas_df['rsrp'].rolling(minute_value).mean()
			meas_df['rsrq'] = meas_df['rsrq'].rolling(minute_value).mean()
			meas_df['rssi'] = meas_df['rssi'].rolling(minute_value).mean()
			meas_df['rssnr'] = meas_df['rssnr'].rolling(minute_value).mean()

			if optim_size:
				print(optim_size)
				meas_df = meas_df.iloc[::average_value]

			print(meas_df.head())
			prev_selected_file = selected_file  # Update the previous selected file
			prev_selected_band = selected_band # Update the previous selected band
			prev_selected_rat = seleceted_rat # Update the previous selected rat
			prev_selected_operator = selected_operator # Update the previous selected operator
			prev_filter_rsrp_range = filter_rsrp_range
			prev_filter_rsrq_range = filter_rsrq_range
			prev_filter_rssi_range = filter_rssi_range
			prev_filter_rssnr_range = filter_rssnr_range
	# Create a list to hold marker colors and opacity
	marker_colors = ['blue'] * len(meas_df)  # Initialize with the original color
	marker_opacity = [0.5] * len(meas_df)  # Initialize with the original opacity
	# Create the line trace with updated marker colors
	line_trace_rsrp = go.Scatter(
		x=meas_df.index,
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
		x=meas_df.index,
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
		x=meas_df.index,
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
		x=meas_df.index,
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

	boxplot_rsrp_figure = px.box(meas_df, y='rsrp', title='Box Plot of RSRP Values')
	boxplot_rsrp_figure.update_layout(yaxis_title='RSRP (dBm)')
	boxplot_rsrq_figure = px.box(meas_df, y='rsrq', title='Box Plot of RSRQ Values')
	boxplot_rsrq_figure.update_layout(yaxis_title='RSRQ (dB)')
	boxplot_rssi_figure = px.box(meas_df, y='rssi', title='Box Plot of RSSI Values')
	boxplot_rssi_figure.update_layout(yaxis_title='RSSI (dBm)')
	boxplot_rssnr_figure = px.box(meas_df, y='rssnr', title='Box Plot of RSSNR Values')
	boxplot_rssnr_figure.update_layout(yaxis_title='RSSNR (dB)')
	
	histogram_rsrp_figure = px.histogram(meas_df, x='rsrp', title='Histogram Plot of RSRP Values')
	histogram_rsrp_figure.update_layout(xaxis_title='RSRP (dBm)')
	histogram_rsrq_figure = px.histogram(meas_df, x='rsrq', title='Histogram Plot of RSRQ Values')
	histogram_rsrq_figure.update_layout(xaxis_title='RSRQ (dB)')
	histogram_rssi_figure = px.histogram(meas_df, x='rssi', title='Histogram Plot of RSSI Values')
	histogram_rssi_figure.update_layout(xaxis_title='RSSI (dBm)')
	histogram_rssnr_figure = px.histogram(meas_df, x='rssnr', title='Histogram Plot of RSSNR Values')
	histogram_rssnr_figure.update_layout(xaxis_title='RSSNR (dB)')
	
	return rsrp_figure, rsrq_figure, rssi_figure, rssnr_figure, boxplot_rsrp_figure, boxplot_rsrq_figure, boxplot_rssi_figure, boxplot_rssnr_figure, histogram_rsrp_figure, histogram_rsrq_figure, histogram_rssi_figure, histogram_rssnr_figure, min_rsrp_value, max_rsrp_value, min_rsrq_value, max_rsrq_value, min_rssi_value, max_rssi_value, min_rssnr_value, max_rssnr_value

@app.callback(
	[Output('rat-selector-static', 'disabled'),
	 Output('band-selector-static', 'disabled'),
	 Output('operator-selector-static', 'disabled'),],
	[Input('rsrp-chart-static', 'figure')]
)
def update_selectors_availability(selected_file):
	# Check if a data set is selected
	if selected_file:
		# If selected_file is not None, enable the new data selectors
		return False, False, False
	elif selected_file:
		return False, False, False
	else:
		# If no data set is selected, disable the new data selectors
		return True, True, True
@app.callback(
	[Output('band-selector-static', 'options'),
	 Output('rat-selector-static', 'options'),
	 Output('operator-selector-static', 'options')],
	[Input('rsrp-chart-static', 'figure')]
)
def update_selectors_options(selected_file):
	global prev_selected_file_2
	# Check if a data are selected
	if selected_file != prev_selected_file_2:
		if selected_file != None:
			# Make a delay between execution of two callbacks
			print('No file selected!')
		else:
			return [], [], []
		prev_selected_file_2 = selected_file  # Update the previous selected file
		# Update options based on the selected rat 
		return list(meas_df['band'].unique()), list(meas_df['rat'].unique()), list(meas_df['operator'].unique())
	else:
		# If no data are selected, return empty options for other selectors
		return [], [], []
# Define a callback to update options when the dropdown is clicked
@app.callback(
	Output('data-selector-static', 'options'),
	[Input('data-selector-static', 'value')]
)
def update_options(n_clicks):
	# Add your logic to update options based on the click event
	# For example, you can update the options list with new data
	updated_options = [
		{'label': f'Data Set: {file_name}', 'value': file_path}
		for file_name, file_path in zip(
			[os.path.basename(file_path) for file_path in glob.glob(os.path.join(data_directory, '*.csv'))],
			glob.glob(os.path.join(data_directory, '*.csv'))
		)
	]
	return updated_options
if __name__ == "__main__":
	app.run_server(debug=True)