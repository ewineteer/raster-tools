# raster-tools
Raster/geoprocessing tools. Depends on rasterio and geopandas.

`mosaic_rasters`

Combines a list of raster tiles into a single raster file.
Only argument is a list of raster tile paths. 
Combined raster probably needs to fit in memory (I've never test with an out-of-memory raster)

`reproj`

Fast parallel reprojection of categorical or continuous rasters.
Must pass a resampling technique, depending on type of data in raster. For resampling options see:
https://rasterio.readthedocs.io/en/latest/topics/resampling.html
Raster doesn't need to fit in memory.

`rasterize`
Converts a geodataframe to raster.
If given an outpath, it writes it to a geotiff. If no outpath, it returns a numpy array and projection info.
Raster needs to fit in memory.

`polygontoraster`
Converts a shapefile path to a geotiff. Calls the above rasterize funciton.

`polygonize`
Converts a numpy array and projection info into a polygon geodataframe.

`rastertopolygon`
Converts a geotiff file into a shapefile. Calls the above polygonize function.