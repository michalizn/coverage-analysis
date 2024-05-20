from dash import html, dcc
from dash.dependencies import Input, Output
# Connect to main app.py file
from app import app
# Connect to app pages
from pages import mobile_analysis, forecast, static_analysis, about
# Connect the navbar to the index
from components import navbar
# Make a server
server = app.server
# Define the navbar
nav = navbar.Navbar()
# Define the index page layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    nav, 
    html.Div(id='page-content', children=[]), 
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/mobile_analysis':
        return mobile_analysis.layout
    # if pathname == '/forecast':
    #     return forecast.layout
    if pathname == '/static_analysis':
        return static_analysis.layout
    if pathname == '/about':
        return about.layout
    else:
        return mobile_analysis.layout

if __name__ == '__main__':
    app.run_server(debug=True)