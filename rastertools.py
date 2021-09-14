import multiprocessing
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS

import rasterio as rio 
from rasterio.merge import merge
from rasterio.plot import show

from shapely.geometry import shape
import geopandas as gpd
import numpy as np

# Argument is a list of file paths to raster tiles.
def mosaic_rasters(demfiles):
	mosaicsources = []
	for demfile in demfiles:
		with rio.open(demfile) as src:
			mosaicsources.append(src)

	mosaic, out_trans = merge(mosaicsources)	

	return (mosaic, out_trans)



# Fast parallel reprojection of categorical or continuous rasters.
def reproj(inpath,outpath,dst_crs,resamp):

    numthreads = multiprocessing.cpu_count()
    resamptechnique = getattr(Resampling,resamp)

    if isinstance(dst_crs,int):
        dst_crs = CRS.from_epsg(dst_crs)
    elif isinstance(dst_crs,str):
        dst_crs = CRS.from_proj4(dst_crs)
    else:
        raise Exception('Destination CRS is invalid.')
        
    with rio.open(inpath) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwds = src.profile
        kwds.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        kwds.pop('compress', None)  #deletes compression and interleave parameters
        kwds.pop('interleave', None)

        with rio.open(outpath, 'w', **kwds, threads=numthreads-1) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resamptechnique)

# Generator used by rasterize
def shapegenerator(gdf,valfield='FID'):
    for i,row in gdf.iterrows():
        geom = row.geometry
        val = row[valfield]
        yield(geom,val)

# Convert a geodataframe to raster
################ TODO: add capability to rasterize using an example raster for cellsize
def rasterize(gdf, cellsize, valfield, outpath=None, fill=None, nodata=None, all_touched=True):

    minx, miny, maxx, maxy = gdf.total_bounds

    transform = rio.transform.from_origin(west=minx, north=maxy, xsize=cellsize, ysize=cellsize)
    height,width = rio.transform.rowcol(transform,maxx,miny)
    shape = (height,width)

    shapegen = shapegenerator(gdf=gdf,valfield=valfield)

    dtype = gdf[valfield].dtype

    if not fill:
        fill = np.iinfo(dtype).min
    if not nodata:
        nodata = np.iinfo(dtype).min

    rastarr = rio.features.rasterize(shapes=shapegen,
                            out_shape=shape,
                          fill=fill,
                          transform=transform,
                          dtype=dtype,
                          all_touched=all_touched)

    profile = {'driver':'GTiff', 'dtype':dtype, 'nodata':nodata, 'width':width, 'height':height, 'count':1, 'crs':gdf.crs,
                'transform':transform, 'blockxsize':128, 'blockysize':128, 'tiled':True, 'interleave':'band'}
    if outpath:
        with rio.open(outpath, 'w',**profile) as dst:
            dst.write(rastarr, indexes=1)
    else:
        return (rastarr, profile)

# Convert a polygon shapefile to raster (using the above rasterize function)
def polygontoraster(polypath, exrastpath, valfield, dtype, outpath=None, fill=None, nodata=None, all_touched=True):
    with rio.open(exrastpath) as src:
        profile = src.profile

    height = profile['height']
    width = profile['width']
    shape = (height,width)

    gdf = gpd.read_file(polypath)

    crs = profile['crs']
    transform = profile['transform']

    if gdf.crs != profile['crs']:
        gdf = gdf.to_crs(crs)

    shapegen = shapegenerator(gdf=gdf,valfield=valfield)

    if not fill:
        fill = np.iinfo(dtype).min
    if not nodata:
        nodata = np.iinfo(dtype).min

    rastarr = rio.features.rasterize(shapes=shapegen,
                            out_shape=shape,
                          fill=fill,
                          transform=transform,
                          dtype=dtype,
                          all_touched=all_touched)

    profile.update({'dtype':dtype, 'nodata':nodata})

    if outpath:
        with rio.open(outpath, 'w',**profile) as dst:
            dst.write(rastarr, indexes=1)
    else:
        return (rastarr, profile)


# Convert raster (numpy array & transform) to polygon geodataframe
def polygonize(rastarr, transform, crs, multipart=True):
    polys = rio.features.shapes(source=rastarr,
                         mask=None,
                         connectivity=4,
                         transform=transform)

    allgeoms = []
    allvals = []
    for poly,val in polys:
        geom = shape(poly)
        allgeoms.append(geom)
        allvals.append(val)

    dfdata = {'Value':allvals}

    gdf = gpd.GeoDataFrame(data=dfdata, geometry=allgeoms, crs=crs)
    gdf.geometry = gdf.geometry.buffer(0) # to fix self-intersections if you have a single cell hanging off of a watershed corner

    if multipart:
        gdf = gdf.dissolve('Value').reset_index() # otherwise you get multiple separate features if you have a single cell hanging off of a watershed corner

    return gdf

# Convert geotiff raster to raster shapefile using the above polygonize function
def rastertopolygon(rasterpath, outpath=None, multipart=True):
    with rio.open(rasterpath) as src:
        rastarr = src.read(1)
        prof = src.profile

    gdf = polygonize(rastarr=rastarr,
                    transform=prof['transform'],
                    crs=prof['crs'],
                    multipart=multipart)

    if outpath:
        gdf.to_file(outpath)
        return
    else:
        return gdf