# Albedo-anomaly method

This repository contains the implementation of the albedo-anomaly method, a technique used to estimate glacier mass balance by combining geodetic measurements with satellite-derived albedo estimates.

## Repository Structure

### `GMB_estimation.ipynb`
A Jupyter Notebook that demonstrates how to compute **annual glacier mass balance time series** using the albedo-anomaly method.

### `glalbedo.py`
A Python module containing functions to calculate **MOD10 glacier-wide summer albedo**, which serves as a key input to the albedo-anomaly method.

### `data/`
Contains input datasets required for the albedo-anomaly method:

#### Input Data
- **`Hugonnet2021/`** — Geodetic glacier mass balance estimates (2000–2019)  
  Source: *Hugonnet et al. (2021)*
- **`rgi60/`** — Glacier outlines from the **Randolph Glacier Inventory v6.0**

#### Output Data
- **Annual mass balance time series** for all land-terminating, non-surging glaciers larger than 0.5 km², located in:
  - European Alps  
  - Scandinavia  
  - Svalbard

---

## Requirements

This project requires access to **[Google Earth Engine (GEE)](https://earthengine.google.com/)** to retrieve and process MODIS albedo data. The steps to set up GEEare :

1. **Create a Google Earth Engine account**  
   Sign up at [https://earthengine.google.com/signup/](https://earthengine.google.com/signup/).

2. **Create a GEE project**  
   After your account is approved, create a new project in the GEE Code Editor (e.g., `projects/your-project-name`).

3. **Authenticate GEE in your Python environment**  
   Run the following command in your terminal or Jupyter notebook to link your Google account:
   ```bash
   earthengine authenticate

Ensure your project has the appropriate permissions and asset storage for exporting and reading data.

To run the notebook and scripts, you’ll need Python ≥ 3.8 and the following packages:

`ee`

`geemap`

`pandas`

`geopandas`

`shapely`

`matplotlib`
