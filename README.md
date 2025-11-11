# 4G/5G Coverage Analysis Dashboard

An interactive Dash/Plotly application for **mapping and analyzing signal coverage and quality in 4G/5G mobile networks**. The app loads measurement CSV files, merges them with a serving-cell database, and visualizes results on OpenStreetMap along with KPI distributions and filters. A lightweight Raspberry Pi helper is included for field measurements.

---

## Table of Contents

- Features
- Architecture & Pages
- Data Model (CSV schema)
- Color Mapping & Thresholds
- Directory Layout
- Quick Start
  - Unix/macOS
  - Windows
  - Production (Gunicorn)
- Usage Workflow
- Raspberry Pi Helper (app_rpi)
- Troubleshooting
- Roadmap
- License & Acknowledgements
- References

---

## Features

- 📍 **Geospatial visualization** on OpenStreetMap with Plotly Scattermapbox.
- 📊 **KPI dashboards** for RSRP, RSRQ, RSSI, and RSSNR with interactive range filters.
- 🔎 **Filtering by RAT, band, operator**, and by KPI ranges.
- 🗺️ **Interpolation options** (SciPy `griddata`, `LinearNDInterpolator`, `CloughTocher2DInterpolator`) to produce estimated coverage surfaces from point samples.
- 🗂️ **Multi‑file selection** – combine multiple CSVs (e.g., multiple drive routes) in one view.
- 🏷️ **Cell database merge** (e.g., GSMWeb.cz export) to enrich samples with BTS location/metadata.
- 💻 **Two analysis modes**: mobile (drive‑test style) and static (stationary measurements).
- 🧪 **Laboratory assignment** material included (PDF).

---

## Architecture & Pages

The app is a classic Dash single‑page app with manual routing and Bootstrap styling.

- `app/app.py` — creates the Dash instance with Bootstrap theme.
- `app/index.py` — defines the top‑level layout, navbar, and simple path router (`/mobile_analysis`, `/static_analysis`, `/about`). Exposes `server = app.server` for WSGI.
- `app/components/navbar.py` — navigation bar (Dashboard title + links).
- `app/pages/` — per‑page layouts and callbacks:
  - `mobile_analysis.py` — main interactive map + KPI panels for **dynamic** (drive) data.
  - `static_analysis.py` — charts for **static** (stationary) measurements.
  - `about.py` — about page (assets under `app/assets/`).
  - `forecast.py` — placeholder (not enabled in navbar by default).

**Map layer**: Plotly `Scattermapbox` with `open-street-map` tiles.  
**Routing**: Querystring/location driven (`dcc.Location`) with a callback deciding the active page.  
**Styling**: `dash-bootstrap-components` (Navbar, Cards, Grid).

---

## Data Model (CSV schema)

The app expects CSV files with the following columns (comma‑separated). Types/units in brackets:

```
date [YYYY-MM-DD], time [HH:MM:SS], operator [str], csq [int],
rat [LTE|NR5G_NSA], operation_mode [str],
mobile_country_code [int], location_area_code [int], cell_id [int],
arfcn [int], band [str],
downlink_frequency [MHz], downlink_bandwidth [MHz], uplink_bandwidth [MHz],
rsrp [dBm], rsrq [dB], rssi [dBm], rssnr [dB],
latitude [deg], ns_indicator [N|S], longitude [deg], ew_indicator [E|W],
date2 [YYYY-MM-DD], time2 [HH:MM:SS],
altitude [m], speed [m/s or km/h], course [deg],
color_rsrp, color_rsrq, color_rssi, color_rssnr, text
```

Notes:

- **Units**: RSRP (dBm), RSRQ (dB), RSSI (dBm), RSSNR (dB).  
- **Normalization**: Parser performs scaling for specific RATs where raw logs are in tenths (e.g., `rsrq/=100` for LTE, `/=10` for some 5G modem outputs).  
- **Validation/clipping**: Values are clipped to reasonable ranges (e.g., `rsrp∈[-200, -30]`, `rsrq∈[-20, 10]`, `rssi∈[-150, 0]`, `rssnr∈[-15, 50]`).  
- **Bands (EU examples)** used in the app: LTE `EUTRAN-BAND1/3/7/20` and NR `NR5G_BAND78` (see code constants).  
- **Cell DB join**: `app/data/cell_database/bts_list.csv` (semicolon `;` delimited) must provide, at minimum: `bts_place`, `bts_lat`, `bts_lon`, `hex` (Cell ID). Non‑numeric `hex` is stripped and coerced to integer before the merge.

---

## Color Mapping & Thresholds

Points are color‑coded by KPI using fixed band‑aware thresholds (colors: `lawngreen`, `yellow`, `orange`, `red`).

**RSRP thresholds (dBm):**
- Default/LTE B1/B3: **≥ -90** green, **≥ -120** yellow, **≥ -140** orange, else red
- LTE **B7**: **≥ -95**, **≥ -125**, **≥ -145**, else red
- LTE **B20**: **≥ -80**, **≥ -110**, **≥ -130**, else red
- NR **n78**: **≥ -90**, **≥ -110**, **≥ -130**, else red

**Other KPIs:**
- **RSRQ**: **≥ -10**, **≥ -15**, **≥ -20**, else red
- **RSSI**: **≥ -65**, **≥ -75**, **≥ -85**, else red
- **RSSNR**: **≥ 10**, **≥ 3**, **≥ 0**, else red

> These thresholds are implemented in `mobile_analysis.py` and can be modified to your own planning guidelines.

---

## Directory Layout

```
coverage-analysis/
├─ app/                       # Dash application
│  ├─ app.py                  # Dash() app factory (Bootstrap theme)
│  ├─ index.py                # Top-level layout, router and server export
│  ├─ components/
│  │  └─ navbar.py
│  ├─ pages/
│  │  ├─ mobile_analysis.py   # Dynamic drive-test analysis + map
│  │  ├─ static_analysis.py   # Static (stationary) analysis
│  │  ├─ about.py             # About page
│  │  └─ forecast.py          # Placeholder (not enabled by default)
│  ├─ assets/                 # Images for About / UI
│  └─ data/
│     ├─ cell_database/
│     │  └─ bts_list.csv      # BTS database (e.g., GSMWeb.cz export)
│     └─ measured_data/
│        ├─ dynamic/          # Drive-test CSVs (e.g., kolejni_street.csv, ...)
│        └─ static/           # Stationary CSVs
├─ app_rpi/
│  └─ meas_setting.py         # Raspberry Pi helper for measurement capture
├─ environment/
│  └─ requirements.txt        # dash, plotly, pandas, matplotlib, scipy, etc.
├─ lab_assignment/
│  ├─ app_lab/                # RPi app variant for lab work
│  └─ Laboratory Assignment focused on analyzing the Coverage of Mobile Networks.pdf
└─ README.md
```

---

## Quick Start

### Unix/macOS

```bash
git clone https://github.com/michalizn/coverage-analysis
cd coverage-analysis

# Create & activate a virtualenv
python3 -m venv env
source env/bin/activate

# Install dependencies
pip3 install -r environment/requirements.txt

# Run the app
cd app
python3 index.py  # http://127.0.0.1:8050
```

### Windows

```powershell
git clone https://github.com/michalizn/coverage-analysis
cd coverage-analysis

# Create & activate a virtualenv
python -m venv env
.\env\Scripts ctivate

# Install dependencies
pip install -r environment/requirements.txt

# Run the app
cd app
python index.py  # http://127.0.0.1:8050
```

### Production (Gunicorn)

```bash
# From repository root (virtualenv activated)
pip install gunicorn
cd app
gunicorn -w 2 -b 0.0.0.0:8050 app.index:server
```

---

## Usage Workflow

1. **Prepare data**: Place CSV logs in `app/data/measured_data/dynamic/` (drive) and/or `app/data/measured_data/static/` (stationary). Ensure column names match the *Data Model* above.
2. **Cell database (optional)**: Provide/refresh `app/data/cell_database/bts_list.csv` (semicolon `;` delimited) containing the serving cells (ID, lat/lon, site name).
3. **Run the app** and open the **Mobile Measurement** page.
4. **Select dataset(s)** in *Select the data for processing* (multi‑select is allowed).
5. (Optional) Choose **RAT**, **Band**, **Operator** filters.
6. (Optional) Choose an **Interpolation Method** and **Data for interpolation**.
7. Use the **RSRP/RSRQ/RSSI/RSSNR sliders** to restrict the value ranges and update plots.
8. Inspect the **map**—hover shows a rich tooltip with timestamp, operator, RAT, cell ID, ARFCN, band, bandwidths, and KPI values.
9. Use the **Static Measurement** page for box/violin/hist style summaries of stationary logs.

---

## Raspberry Pi Helper (`app_rpi`)

The `app_rpi/meas_setting.py` module provides a minimal helper configuration used for **field data collection** on Raspberry Pi with a cellular modem. It produces CSV files with the schema consumed by the Dash app. Adjust serial/modem parameters and output paths there to match your setup.

> For classroom use, see the lab variant under `lab_assignment/app_lab/` and the included PDF assignment.

---

## Troubleshooting

- **No points on the map**
  - Verify CSVs are in the expected `app/data/measured_data/*` directories and have the exact column names.
- **BTS not shown / tooltips missing site info**
  - Check `bts_list.csv` delimiter (`;`) and that `hex` (Cell ID) is numeric after cleaning.
- **RSRP/RSRQ look off by 10x**
  - Some modem logs encode values in tenths; the app rescales, but double‑check raw logs.
- **5G dataset lacks RSSI**
  - Some NR sources do not provide an RSSI; RSSI panels may be empty for NR logs.
- **`ModuleNotFoundError: dash_bootstrap_components`**
  - Install dependencies via `pip install -r environment/requirements.txt`.

---

## Roadmap

- Add **Handover / Serving vs. Neighbor** overlays.
- Support **multi‑RAT aggregation layers** and more NR bands.
- Export **GeoJSON/MBTiles** for GIS workflows.
- Optional **MEC‑style** remote processing for heavy interpolation.

---

## License & Acknowledgements

- **License**: No license file has been provided yet.
- **Acknowledgements**: Espressif Dash/Plotly ecosystem, GSMWeb.cz (cell DB export).

---

## References

- Repository README and structure.  
- LTE measurements (RSRP/RSRQ/RSSI) — 3GPP TS **36.214** / ETSI TS **136 214** (E‑UTRA Physical layer; Measurements).  
- NR measurements (SS‑RSRP/SS‑RSRQ/SS‑SINR) — 3GPP TS **38.215** / ETSI TS **138 215** (NR Physical layer; Measurements).
