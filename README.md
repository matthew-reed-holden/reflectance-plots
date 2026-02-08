# Reflectance Plots

Interactive Bokeh application for visualizing total reflectance, specular reflectance, and Lambertian reflectance data of black and white materials.

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Setup

```bash
pip install -r requirements.txt
```

## Running

From the **parent directory** containing the `reflectance-plots` folder:

```bash
bokeh serve --show reflectance-plots
```

This launches the Bokeh server and opens the application at `http://localhost:5006/reflectance-plots`.

## Features

- **Total Reflectance** -- Wavelength-based (250-2500 nm) for 45+ black and 9+ white materials
- **Specular Reflectance** -- Angle-based (10-160 degrees) with reflectance and ratio views
- **Lambertian Reflectance** -- Angle-based (10-90 degrees) with scaled, power, and residual measurements
- **Interactive Filtering** -- Filter by material color or select individual materials by name
- **Range Sliders** -- Adjust displayed wavelength/angle ranges
- **CSV Downloads** -- Export full datasets or selected materials as CSV files
- **Hover Tooltips** -- View material name and exact values on hover

## Data

All measurement data is stored in `data/` as CSV files, organized by reflectance type.

## Video Demo

[![B/W Materials Webpage](https://img.youtube.com/vi/xFqTxLJb9t8/0.jpg)](https://www.youtube.com/watch?v=xFqTxLJb9t8)
