# %% codecell
from osgeo import gdal
import multiprocessing

def compress_gdal(origpath,outpath,multithread=True,fileformat='GTiff',compress='PACKBITS', verbose=True):
    numthreads = multiprocessing.cpu_count()
    driver = gdal.GetDriverByName(fileformat)
    metadata = driver.GetMetadata()
    if (metadata.get(gdal.DCAP_CREATECOPY) == "YES") & (verbose):
        print("Driver {} supports CreateCopy() method.".format(fileformat))
    else:
        print("Driver {} does not support CreateCopy() method.".format(fileformat))
        return

    src_ds = gdal.Open(origpath)
    dst_ds = driver.CreateCopy(outpath, src_ds, strict=1,options=["TILED=YES", "COMPRESS=PACKBITS","NUM_THREADS="+str(numthreads)])#,"PREDICTOR=3","ZSTD_LEVEL=15"])
    dst_ds = None # Once we're done, close properly the dataset
    src_ds = None
    if verbose:
        print('Compression complete.')
