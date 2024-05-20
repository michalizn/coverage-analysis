from dash import html
import dash_bootstrap_components as dbc

def Navbar():

    layout = html.Div([
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Mobile Measurement", href="/mobile_analysis")),
                dbc.NavItem(dbc.NavLink("Static Measurement", href="/static_analysis")),
                #dbc.NavItem(dbc.NavLink("Forecasting", href="/forecast")),
                dbc.NavItem(dbc.NavLink("About", href="/about")),
            ],
            brand="Coverage Analysis - Dashboard",
            brand_href="/mobile_analysis",
            color="dark",
            dark=True,
        ), 
    ])

    return layout