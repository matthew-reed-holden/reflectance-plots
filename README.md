# Reflectance Plots

Interactive Bokeh application for visualizing total reflectance, specular reflectance, and Lambertian reflectance data of black and white materials.

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Setup

```bash
pip install -r requirements.txt
```

## Running Locally

**Option 1: Bokeh Server** (interactive, with Python backend)

From the **parent directory** containing the `reflectance-plots` folder:

```bash
bokeh serve --show reflectance-plots
```

This launches the Bokeh server and opens the application at `http://localhost:5006/reflectance-plots`.

**Option 2: Static HTML** (no server needed)

```bash
pip install jinja2
python build.py
```

This generates `docs/index.html` -- a self-contained page you can open directly in a browser.

## GitHub Pages Deployment

This project can be hosted as a static site on GitHub Pages. A GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically builds and deploys on every push to `master`.

To enable:

1. Go to your repository **Settings > Pages**
2. Under **Source**, select **GitHub Actions**
3. Push to `master` -- the workflow will build `docs/index.html` and deploy it

The static version uses client-side JavaScript for all interactivity (no Python server required).

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
