import ee
import geemap

import pandas as pd
import numpy as np


def MODalbedo(start_date, end_date, glacier_outline):

    """
    Loads the MODIS daily albedo data for a specified glacier area and time range.

    Parameters
    ----------
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    end_date : str
        End date in 'YYYY-MM-DD' format.
    glacier_outline : ee.Geometry or ee.Feature
        Glacier outline defining the region of interest.

    Returns
    -------
    ee.ImageCollection
        MODIS albedo image collection (`MODIS/061/MOD10A1`) filtered by space and time,
        with the 'Snow_Albedo_Daily_Tile' band renamed to 'albedo' and scaled to the 0–1 range.
    """

    space_time_filter = ee.Filter.And(
        ee.Filter.bounds(glacier_outline),
        ee.Filter.date(start_date, end_date)
    )
    
    return (
        ee.ImageCollection('MODIS/061/MOD10A1')
        .filter(space_time_filter)
        .map(lambda img: (
            img.select(['Snow_Albedo_Daily_Tile'], ['albedo'])
            .divide(100)
            .copyProperties(img, img.propertyNames())
            )
        )
    )


def glacierwide_albedo(albedo_img, geom, scale=None):

    """
    Computes the mean glacier-wide albedo and valid pixel fraction for a single MODIS image.

    Parameters
    ----------
    albedo_img : ee.Image
        MODIS albedo image containing an 'albedo' band scaled from 0–1.
    geom : ee.Geometry or ee.Feature
        Geometry (e.g., glacier outline) over which to compute statistics.
    scale : int, optional
        Spatial resolution (in meters) to use when reducing the image. Defaults to MODIS native scale.

    Returns
    -------
    ee.Feature
        A feature containing:
        - 'date': image acquisition date (YYYY-MM-DD)
        - 'valid_fraction': fraction of valid (non-masked) pixels
        - 'albedo_avg': mean glacier-wide albedo
    """

    N_valid = albedo_img.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geom,
        scale=scale
    ).getNumber('albedo')

    N_tot = albedo_img.unmask().reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geom,
        scale=scale
    ).getNumber('albedo')

    albedo_mean = albedo_img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale
    ).getNumber('albedo')

    return ee.Feature(None, {
        'date': ee.Date(albedo_img.get('system:time_start')).format('YYYY-MM-dd'),
        'valid_fraction': N_valid.divide(N_tot),
        'albedo_avg': albedo_mean
    })


def albedo_ts(img_collection, geom, scale=None):

    """
    Generates a time series of average albedo values for a given glacier.

    Parameters
    ----------
    img_collection : ee.ImageCollection
        MODIS albedo images with an 'albedo' band (e.g., from MODalbedo()).
    geom : ee.Geometry or ee.Feature
        Glacier outline or region of interest.
    scale : int, optional
        Spatial resolution (in meters) to use when reducing the image. Defaults to MODIS native scale.

    Returns
    -------
    pandas.DataFrame
        Time series DataFrame indexed by date, with columns:
        - 'albedo_avg': mean glacier-wide albedo
        - 'valid_fraction': fraction of valid pixels per date
    """

    albedo_avg = ee.FeatureCollection(img_collection.map(lambda img: glacierwide_albedo(img, geom, scale)))
    albedo_avg = geemap.ee_to_df(albedo_avg).set_index('date')
    albedo_avg.index = pd.to_datetime(albedo_avg.index)

    # If more albedo values for the same date keep only the one with the highest valid_fraction
    albedo_avg = albedo_avg.groupby(albedo_avg.index).apply(
        lambda x: x.sort_values(by='valid_fraction').iloc[-1, :]
    )

    return albedo_avg


def albedo_interp(albedo, th, smooth=False):

    """
    Interpolates and optionally smooths a glacier albedo time series.

    Parameters
    ----------
    albedo : pandas.DataFrame
        Output from `albedo_ts()` containing 'albedo_avg' and 'valid_fraction' columns.
    th : float
        Threshold for valid pixel fraction (0–1). Albedo values below this threshold are discarded.
    smooth : bool, optional
        If True, applies a centered 5-day rolling mean smoothing to the interpolated albedo.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing interpolated (and optionally smoothed) albedo values,
        limited to the ablation season (June 1 – September 30).
        Includes:
        - 'albedo_avg_interp': temporally interpolated albedo
        - 'albedo_avg_interp_smoothed' (if smooth=True): smoothed albedo
    """

    year = albedo.index[0].year
    albedo = albedo.reindex(pd.date_range(start=f'{year}-05-01', end=f'{year}-10-31', freq='D'))

    albedo['albedo_avg_interp'] = albedo['albedo_avg']
    albedo.loc[albedo['valid_fraction'] < th, 'albedo_avg_interp'] = np.nan
    albedo['albedo_avg_interp'] = albedo['albedo_avg_interp'].interpolate(method='time').ffill().bfill()

    if smooth:
        albedo['albedo_avg_interp_smoothed'] = albedo['albedo_avg_interp'].rolling(5, center=True).mean()
    
    return albedo.loc[f'{year}-06-01':f'{year}-09-30', :]





    