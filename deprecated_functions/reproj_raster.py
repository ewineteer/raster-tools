import multiprocessing
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling

def reproj(inpath,outpath,dst_crs,resamp):

    numthreads = multiprocessing.cpu_count()
    resamptechnique = getattr(Resampling,resamp)

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
