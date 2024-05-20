# 4G and 5G Coverage Analysis

This thesis deals with the advanced measurement of signal coverage, capacity, and reliability in mobile networks, especially with the widespread adoption of 4G and 5G technologies. As these networks become increasingly integral to daily life, there is a need for cost-effective solutions to assess and optimize their performance. The primary objective of this work is to develop affordable software and hardware solutions capable of extracting fundamental Key Performance Indicators (KPIs) from 4G/5G mobile networks. The proposed system aims to provide users with an accessible tool to assess network performance, signal coverage in specific areas, and predictive models for future network capacity. These functionalities are presented through a user-friendly graphical interface (so-called GUI), allowing for straightforward and cost-effective measurements in both outdoor and indoor settings.

## The tree structure of the repository with definitions:
```
coverage-analysis
├── app................................................................Application directory
│   ├── app.py
│   ├── assets.................................................Pictures for the 'About' page
│   │   ├── boxplot_app.png
│   │   └── ...
│   ├── components............................................................Navigation bar
│   │   └── navbar.py
│   ├── data
│   │   ├── cell_database.......................................Cell database from GSMWeb.cz
│   │   │   └── bts_list.csv
│   │   └── measured_data
│   │       ├── dynamic....................................Datasets from mobile measurements
│   │       │   ├── kolejni_street.csv
│   │       │   ├── measurement_band1_lte_0.csv
│   │       │   └── ...
│   │       └── static.....................................Datasets from static measurements
│   │           ├── measurement_band1_lte_static.csv
│   │           └── ...
│   ├── index.py
│   └── pages.......................................................Pages of the application
│       ├── about.py
│       ├── forecast.py
│       ├── mobile_analysis.py
│       └── static_analysis.py
│
├── app_rpi......................................................Application on Raspberry Pi
│   └── meas_setting.py
├── environment
│   └── requirements.txt...................................................Required packages 
├── lab_assignment
│   ├── app_lab...............Application on Raspberry Pi modified for Laboratory Assignment 
│   │   └── meas_setting.py
│   └── Laboratory Assignment focused on analyzing the Coverage of Mobile Networks.pdf
└── README.md
```
## Installation Instructions:

### Unix/MacOS
```bash
# Clone the repository
git clone https://github.com/michalizn/coverage-analysis

# Get to the app directory
cd coverage-analysis

# Create a new Python environment
python3 -m venv env

# Activate the virtual environment (Unix/MacOS)
source env/bin/activate

# Install the required packages
pip3 install -r environment/requirements.txt

# Get to the app index
cd app

# Run app locally
python3 index.py
```
### Windows
```bash
# Clone the repository
git clone https://github.com/michalizn/coverage-analysis

# Get to the app directory
cd coverage-analysis

# Create a new Python environment
python3 -m venv env

# Activate the virtual environment (Windows)
.\env\Scripts\activate

# Install the required packages
pip3 install -r environment/requirements.txt

# Get to the app index
cd app

# Run app locally
python3 index.py
```
