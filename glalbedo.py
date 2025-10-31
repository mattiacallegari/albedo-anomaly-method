import ee
import geemap
ee.Initialize()

import pandas as pd
import numpy as np





### -------------------------------------------------------------------------------------------------------------------------


### MOD10 Albedo


def MODalbedo(start_date, end_date, glacier_outline):

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



### Functions to extract time series of the glacier wide albedo


def glacierwide_albedo(albedo_img, geom, scale=None):

    '''
    Compute the average albedo and the valid pixel fraction within the input geometry
    :param albedo_img: image with albedo band saved as "albedo"
    :param geom:
    :return: ee.Feature
    '''

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

    '''
    Compute the average albedo over the input geometry for all the dates of the ablation season of the input year
    :param geom:
    :return: DataFrame
    '''

    albedo_avg = ee.FeatureCollection(img_collection.map(lambda img: glacierwide_albedo(img, geom, scale)))
    albedo_avg = geemap.ee_to_df(albedo_avg).set_index('date')
    albedo_avg.index = pd.to_datetime(albedo_avg.index)

    # If more albedo values for the same date keep only the one with the highest valid_fraction
    albedo_avg.groupby(albedo_avg.index).apply(
        lambda x: x.sort_values(by='valid_fraction').iloc[-1, :]
    )

    #albedo_avg = albedo_avg.reindex(pd.date_range(start=f'{year}-07-01', end=f'{year}-09-30', freq='D'))

    return albedo_avg


def albedo_interp(albedo, th, smooth=False):

    '''
    albedo from albedo_ts function
    '''

    year = albedo.index[0].year
    albedo = albedo.reindex(pd.date_range(start=f'{year}-05-01', end=f'{year}-10-31', freq='D'))

    albedo['albedo_avg_interp'] = albedo['albedo_avg']
    albedo.loc[albedo['valid_fraction'] < th, 'albedo_avg_interp'] = np.nan
    albedo['albedo_avg_interp'] = albedo['albedo_avg_interp'].interpolate(method='time').ffill().bfill()

    if smooth:
        albedo['albedo_avg_interp_smoothed'] = albedo['albedo_avg_interp'].rolling(5, center=True).mean()
    
    return albedo.loc[f'{year}-06-01':f'{year}-09-30', :]





    