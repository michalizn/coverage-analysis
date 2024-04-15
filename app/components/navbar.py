from dash import html
import dash_bootstrap_components as dbc

def Navbar():

    layout = html.Div([
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Dynamic Measurement", href="/dynamic_analysis")),
                dbc.NavItem(dbc.NavLink("Static Measurement", href="/static_analysis")),
                dbc.NavItem(dbc.NavLink("Forecasting", href="/forecast")),
            ],
            brand="Coverage Analysis - Dashboard",
            brand_href="/dynamic_analysis",
            color="dark",
            dark=True,
        ), 
    ])

    return layout