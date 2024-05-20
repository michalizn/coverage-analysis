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

# Define the layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("Welcome to Coverage Analysis - Dashboard"),
                    html.P("Here you can find information along with pictures."),
                    dcc.Markdown('''
                                 All measurements are done via measrument setting tool availible on https://github.com/michalizn/coverage-analysis 
                                 together with this application and measured data. Measured data are collected via Simcom SIM8200EA-M2 5G Module 
                                 shown on the Fig.1.
                    '''),
                    html.Img(src="/assets/meas_setup.JPG", style={'width': '50%'}),
                    html.P("Fig. 1. Simcom SIM8200EA-M2 5G Module together with measurement setting application running on Raspberry Pi"),
                    dcc.Markdown('''
                                 This application includes a user-friendly navigation bar, granting easy access to individual analyses 
                                 of data from both mobile and static measurements. For instance, on the mobile measurement data analysis 
                                 page, this tool features an interactive map enabling to explore the measured area. 
                                 Samples are color-coded based on predetermined thresholds (e.g., green for excellent signal, red for 
                                 insufficient signal) shown in Table 1., allowing to quickly identify areas of interest. Hovering over samples provides 
                                 detailed information about the network. Furthermore, the tool presents graphical representations in the 
                                 time domain for signal measurements, including RSRP, RSRQ, RSSI, and RSSNR. (Note: For the Waveshare 5G 
                                 Module, RSSNR represents the average reference signal SNR of the serving cell, as SINR measurement is 
                                 unavailable.) To ensure consistency in results, the tool incorporates integrated filtering mechanisms. 
                                 These mechanisms isolate the analyzed RAT, band, operator, or other relevant parameters, facilitating 
                                 focused analysis on specific criteria. Additionally, users can set individual thresholds for signal 
                                 metrics, aiding in the targeted examination and detection of problematic areas.
                    '''),
                    html.Img(src="/assets/thresholds.png", style={'width': '50%'}),
                    html.P("Table. 1. Used thresholds for color coding of the individual metrics"),
                    html.H1("User Guide"),
                    html.H3("Mobile Measurement"),
                    dcc.Markdown('''
                                 The Mobile Measurement page consists of four main components. As shown in Fig. 2,
                                  the top section of the page is divided into two parts. The first part, labeled Dropdown data selector, 
                                 enables users to select and process data. Users can choose multiple datasets, merge them together, or 
                                 deselect them as needed. The second part is the Interactive map, which utilizes the OpenStreetMap 
                                 API to retrieve geodata from the OpenStreetMap database. Measured points are displayed this map, color-coded
                                  based on predefined thresholds for each KPI as shown in Table. 1. These 
                                 thresholds were determined through a combination of experimental measurements and objective assessments, 
                                 considering various scenarios, including Internet connectivity status and outages on individual bands and 
                                 technologies.
                    '''),
                    dcc.Markdown('''
                                 The eNBs or gNBs are represented by larger black circles (coordinates from GSMweb.cz). Hovering over a sample 
                                 on the map reveals a detailed summary of the measured sample. Clicking on individual samples generates a line 
                                 connecting the sample to the corresponding cell at that moment, displaying the calculated distance in the legend.
                                  Additionally, the legend allows users to switch between different displays of individual metrics. 
                                 The comprehensive functionality is depicted in Fig. 2.
                    '''),
                    html.Img(src="/assets/upper_part_app.png", style={'width': '50%'}),
                    html.P("Fig. 2. Upper part of the application with navigation bar, dropdown data selector, and interactive map"),
                    dcc.Markdown('''
                                 To facilitate useful data analysis, a Filtering was implemented, which is also linked to the 
                                 Interpolation setting. Through filtering dropdown menus, users can filter data based on RAT, band, and operator. 
                                 Additionally, the interpolation setting enables the estimation of the coverage map over the measured data, 
                                 specifying the KPI for calculation, as shown in Fig. 3.
                    '''),
                    dcc.Markdown('''
                                 The last important part for analysis is the so called Graphs, which display waveforms of measured KPIs, 
                                 like RSRP, RSRQ, RSSI, and RSSNR, are shown in Fig. 4. Detailed information about each sample 
                                 is displayed when hovering over it. The synchronization between the map and all graphs ensures that clicking on a 
                                 point in either the graph or the map triggers the same callback in the Dash application, generating a line 
                                 between the measured point and the corresponding cell. For various analysis scenarios, filtering values within a 
                                 defined range is essential. To achieve this, a range slider is employed. This slider enables users to filter a 
                                 specific metric, allowing them to, for example, isolate only very low values of the RSRP metric. This functionality 
                                 aids in identifying areas with poor coverage and facilitates targeted analysis.
                    '''),
                    html.Img(src="/assets/filtr_interpolation.png", style={'width': '50%'}),
                    html.P("Fig. 3. Filtering menu together with interpolation settings"),
                    html.Img(src="/assets/rsrp_graph_app.png", style={'width': '50%'}),
                    html.P("Fig. 4. Example of time series graph in the application"),
                    html.H3("Static Measurement"),
                    dcc.Markdown('''
                                 The Static Measurement page closely resembles the Mobile Measurement page previously described. However, in static 
                                 measurements, data are collected from a fixed location indoors, where capturing GPS signals is often not feasible. 
                                 Therefore, the interactive map is removed from this page.
                    '''),
                    dcc.Markdown('''
                                 Essentially, the Static Measurement page mirrors the structure of the page designed for mobile measurements.
                                  However, instead of interactive maps, boxplots and histograms are featured, as depicted in 
                                 Fig. 5., and Fig. 6. This similarity in layout and functionality ensures consistency 
                                 across different measurement scenarios while adapting the visualization tools to suit the characteristics 
                                 of static measurements. Additionally, two sections have been incorporated, crucial for analyzing large datasets 
                                 with significant variability. First, a section has been introduced to set the minute rolling average, as depicted 
                                 in Fig. 7. By averaging data over a specified window, it becomes easier to discern long-term
                                  trends or patterns while mitigating the impact of short-term fluctuations. Furthermore, another section aids
                                  in optimizing the data loading time. Given that static measurements typically entail hundreds of thousands to 
                                 millions of measured samples, loading such extensive datasets on a standard computer hosting the application can 
                                 impose an unnecessarily heavy burden. 
                    '''),
                    html.Img(src="/assets/boxplot_app.png", style={'width': '50%'}),
                    html.P("Fig. 5. RSRP Box plot"),
                    html.Img(src="/assets/histogram_app.png", style={'width': '50%'}),
                    html.P("Fig. 6. RSRP Histogram"),
                    dcc.Markdown('''
                                 Therefore, this option allows users to reduce the dataset size, thereby alleviating the data loading strain. 
                                 If this option is enabled, the dataset comprises only every nth value, based on the specified value of the slider
                                  in the 'Rolling Average' section.
                    '''),
                    html.Img(src="/assets/static_meas_part_app.png", style={'width': '50%'}),
                    html.P("Fig. 7. Two added sections for averaging the static dataset and optimizing the loading time of the page"),
                ], style={'textAlign': 'center'}),
            ]),
        ]),
    ]),
])

if __name__ == "__main__":
    app.run_server(debug=True)